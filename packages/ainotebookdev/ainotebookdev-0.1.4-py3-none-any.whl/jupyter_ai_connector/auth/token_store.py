"""Token storage for Auth0 OAuth tokens.

Uses the OS keyring for secure storage of access and refresh tokens,
with an encrypted file-store fallback when keyring is unavailable.
"""

import base64
import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Literal

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

# Service name for keyring storage
KEYRING_SERVICE = "jupyter-ai-connector"

StoragePreference = Literal["keyring", "file", "memory"]
VALID_STORAGE_PREFERENCES: set[str] = {"keyring", "file", "memory"}


class TokenRefreshError(Exception):
    """Represents a refresh token error that needs special handling."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


@dataclass
class StoredToken:
    """Represents stored OAuth tokens."""

    access_token: str
    refresh_token: Optional[str]
    expires_at: float  # Unix timestamp
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    user_sub: Optional[str] = None
    user_idp: Optional[str] = None
    user_picture: Optional[str] = None

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired or about to expire."""
        return time.time() >= (self.expires_at - buffer_seconds)

    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dict for storage."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "user_email": self.user_email,
            "user_name": self.user_name,
            "user_sub": self.user_sub,
            "user_idp": self.user_idp,
            "user_picture": self.user_picture,
        }

    @classmethod
    def from_json(cls, data: str) -> "StoredToken":
        """Deserialize from JSON."""
        parsed = json.loads(data)
        return cls.from_dict(parsed)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoredToken":
        """Deserialize from a dict."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=data["expires_at"],
            user_email=data.get("user_email"),
            user_name=data.get("user_name"),
            user_sub=data.get("user_sub"),
            user_idp=data.get("user_idp"),
            user_picture=data.get("user_picture"),
        )


class TokenStore:
    """Manages OAuth token storage and refresh.

    Tokens are stored in the OS keyring for security.
    Falls back to an encrypted file store when keyring is unavailable,
    and finally to in-memory storage if file storage cannot be initialized.
    """

    def __init__(
        self,
        auth0_domain: str,
        client_id: str,
        file_store_path: str | None = None,
        file_store_key: str | None = None,
        file_store_key_path: str | None = None,
        file_store_enabled: bool = True,
        storage_preference: str | None = None,
    ):
        """Initialize token store.

        Args:
            auth0_domain: Auth0 domain (custom domain recommended, e.g., 'auth.ainotebook.dev')
            client_id: Auth0 application client ID
            file_store_path: Path to encrypted token store file (used when keyring unavailable)
            file_store_key: Base64-encoded encryption key (overrides key path if set)
            file_store_key_path: Path to encryption key file (created if missing)
            file_store_enabled: Enable encrypted file store fallback
            storage_preference: Optional storage preference ("keyring", "file", or "memory")
        """
        self.auth0_domain = auth0_domain
        self.client_id = client_id
        self._storage_preference = self._normalize_storage_preference(storage_preference)
        self._keyring_available: bool | None = None
        self._memory_store: dict[str, StoredToken] = {}
        self._file_store_enabled = bool(file_store_enabled and file_store_path)
        self._file_store_path = Path(file_store_path).expanduser() if file_store_path else None
        self._file_store_key_path = Path(file_store_key_path).expanduser() if file_store_key_path else None
        self._file_store_key_value = file_store_key or ""
        self._file_store_key: bytes | None = None
        self._file_store_ready = False
        self._file_lock = threading.Lock()

    def _check_keyring(self) -> bool:
        """Check if keyring is available."""
        try:
            import keyring
            # Try a dummy operation to verify keyring works
            keyring.get_password(KEYRING_SERVICE, "__test__")
            return True
        except Exception as e:
            logger.warning(f"Keyring not available, using in-memory storage: {e}")
            return False

    def _normalize_storage_preference(self, preference: str | None) -> StoragePreference | None:
        """Normalize a storage preference value."""
        if preference in VALID_STORAGE_PREFERENCES:
            return preference  # type: ignore[return-value]
        return None

    def set_storage_preference(self, preference: str | None) -> None:
        """Set the storage preference for future operations."""
        self._storage_preference = self._normalize_storage_preference(preference)

    def _ensure_keyring_available(self) -> bool:
        """Lazy-check keyring availability to avoid early prompts."""
        if self._keyring_available is None:
            self._keyring_available = self._check_keyring()
        return bool(self._keyring_available)

    def _allow_keyring(self) -> bool:
        return self._storage_preference == "keyring"

    def _allow_file_store(self) -> bool:
        return self._storage_preference in ("keyring", "file")

    @property
    def storage_backend(self) -> str:
        """Return the active storage backend name."""
        if self._allow_keyring() and self._ensure_keyring_available():
            return "keyring"
        if self._allow_file_store() and self._file_store_enabled and self._ensure_file_store_ready():
            return "file"
        return "memory"

    def _ensure_file_store_ready(self) -> bool:
        """Ensure the encrypted file store is initialized."""
        if not self._file_store_enabled or self._file_store_ready:
            return self._file_store_ready
        key = self._load_or_create_file_key()
        if not key:
            self._file_store_enabled = False
            return False
        self._file_store_key = key
        self._file_store_ready = True
        return True

    def _load_or_create_file_key(self) -> bytes | None:
        """Load or create the encryption key for the file store."""
        if self._file_store_key_value:
            return self._decode_key(self._file_store_key_value.strip())

        if self._file_store_key_path and self._file_store_key_path.exists():
            try:
                raw = self._file_store_key_path.read_text(encoding="utf-8").strip()
                return self._decode_key(raw)
            except Exception as exc:
                logger.error(f"Failed to read token store key file: {exc}")
                return None

        if not self._file_store_key_path:
            logger.warning("Token store key path not configured; file store disabled")
            return None

        try:
            key = os.urandom(32)
            encoded = base64.urlsafe_b64encode(key).decode("ascii")
            self._file_store_key_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_store_key_path.write_text(encoded, encoding="utf-8")
            self._set_strict_permissions(self._file_store_key_path)
            logger.info(f"Generated token store key at {self._file_store_key_path}")
            return key
        except Exception as exc:
            logger.error(f"Failed to create token store key: {exc}")
            return None

    def _decode_key(self, raw: str) -> bytes | None:
        """Decode a base64 key string."""
        try:
            key = base64.urlsafe_b64decode(raw.encode("ascii"))
            if len(key) not in (16, 24, 32):
                raise ValueError("Invalid key length")
            return key
        except Exception as exc:
            logger.error(f"Invalid token store key: {exc}")
            return None

    def _encrypt_payload(self, payload: dict[str, Any]) -> str:
        """Encrypt payload for file storage."""
        if not self._file_store_key:
            raise RuntimeError("File store key is not initialized")
        plaintext = json.dumps(payload).encode("utf-8")
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._file_store_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        envelope = {
            "version": 1,
            "nonce": base64.urlsafe_b64encode(nonce).decode("ascii"),
            "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("ascii"),
        }
        return json.dumps(envelope)

    def _decrypt_payload(self, raw: str) -> dict[str, Any] | None:
        """Decrypt payload from file storage."""
        if not self._file_store_key:
            return None
        try:
            envelope = json.loads(raw)
            if envelope.get("version") != 1:
                return None
            nonce = base64.urlsafe_b64decode(envelope["nonce"].encode("ascii"))
            ciphertext = base64.urlsafe_b64decode(envelope["ciphertext"].encode("ascii"))
            aesgcm = AESGCM(self._file_store_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            logger.error(f"Failed to decrypt token store: {exc}")
            return None

    def _read_file_tokens(self) -> dict[str, StoredToken]:
        """Read tokens from encrypted file store."""
        if not self._file_store_path or not self._file_store_path.exists():
            return {}
        try:
            raw = self._file_store_path.read_text(encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to read token store file: {exc}")
            return {}

        payload = self._decrypt_payload(raw)
        if not payload:
            return {}

        tokens: dict[str, StoredToken] = {}
        for key, data in (payload.get("tokens") or {}).items():
            try:
                tokens[key] = StoredToken.from_dict(data)
            except Exception as exc:
                logger.error(f"Invalid token entry in file store: {exc}")
        return tokens

    def _write_file_tokens(self, tokens: dict[str, StoredToken]) -> None:
        """Write tokens to encrypted file store."""
        if not self._file_store_path:
            return
        payload = {"tokens": {key: token.to_dict() for key, token in tokens.items()}}
        encrypted = self._encrypt_payload(payload)

        self._file_store_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._file_store_path.with_suffix(self._file_store_path.suffix + ".tmp")
        tmp_path.write_text(encrypted, encoding="utf-8")
        os.replace(tmp_path, self._file_store_path)
        self._set_strict_permissions(self._file_store_path)

    def _set_strict_permissions(self, path: Path) -> None:
        """Restrict file permissions to the current user."""
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass

    def _get_storage_key(self, user_id: str) -> str:
        """Get the storage key for a user."""
        return f"token:{user_id}"

    def store_token(
        self,
        user_id: str,
        access_token: str,
        expires_in: int,
        refresh_token: Optional[str] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        user_sub: Optional[str] = None,
        user_idp: Optional[str] = None,
        user_picture: Optional[str] = None,
    ) -> StoredToken:
        """Store OAuth tokens for a user.

        Args:
            user_id: Unique user identifier (e.g., Jupyter username)
            access_token: OAuth access token
            expires_in: Token lifetime in seconds
            refresh_token: Optional refresh token for token renewal
            user_email: User's email from ID token
            user_name: User's display name from ID token
            user_sub: User's subject from ID token
            user_idp: Derived identity provider
            user_picture: User profile picture URL

        Returns:
            StoredToken instance
        """
        token = StoredToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=time.time() + expires_in,
            user_email=user_email,
            user_name=user_name,
            user_sub=user_sub,
            user_idp=user_idp,
            user_picture=user_picture,
        )

        key = self._get_storage_key(user_id)

        if self._allow_keyring() and self._ensure_keyring_available():
            try:
                import keyring
                keyring.set_password(KEYRING_SERVICE, key, token.to_json())
                logger.debug(f"Stored token in keyring for user {user_id}")
                return token
            except Exception as e:
                logger.error(f"Failed to store token in keyring: {e}")
                self._keyring_available = False

        if self._allow_file_store() and self._file_store_enabled and self._ensure_file_store_ready():
            with self._file_lock:
                tokens = self._read_file_tokens()
                tokens[key] = token
                self._write_file_tokens(tokens)
            logger.debug(f"Stored token in encrypted file store for user {user_id}")
            return token

        self._memory_store[key] = token
        logger.debug(f"Stored token in memory for user {user_id}")

        return token

    def get_token(self, user_id: str) -> Optional[StoredToken]:
        """Retrieve stored token for a user.

        Args:
            user_id: Unique user identifier

        Returns:
            StoredToken if found and valid, None otherwise
        """
        key = self._get_storage_key(user_id)

        if self._allow_keyring() and self._ensure_keyring_available():
            try:
                import keyring
                data = keyring.get_password(KEYRING_SERVICE, key)
                if data:
                    return StoredToken.from_json(data)
                return None
            except Exception as e:
                logger.error(f"Failed to retrieve token from keyring: {e}")
                self._keyring_available = False

        if self._allow_file_store() and self._file_store_enabled and self._ensure_file_store_ready():
            with self._file_lock:
                tokens = self._read_file_tokens()
                return tokens.get(key)

        return self._memory_store.get(key)

    def clear_token(self, user_id: str, force_all: bool = False) -> bool:
        """Clear stored token for a user.

        Args:
            user_id: Unique user identifier
            force_all: Clear tokens from all storage backends

        Returns:
            True if token was cleared, False if not found
        """
        key = self._get_storage_key(user_id)
        cleared = False

        keyring_allowed = force_all or self._allow_keyring()
        file_allowed = force_all or self._allow_file_store()

        if keyring_allowed and self._ensure_keyring_available():
            try:
                import keyring
                keyring.delete_password(KEYRING_SERVICE, key)
                cleared = True
                logger.debug(f"Cleared token from keyring for user {user_id}")
            except Exception as e:
                logger.debug(f"No token in keyring to clear: {e}")
                self._keyring_available = False

        if file_allowed and self._file_store_enabled and self._ensure_file_store_ready():
            with self._file_lock:
                tokens = self._read_file_tokens()
                if key in tokens:
                    del tokens[key]
                    self._write_file_tokens(tokens)
                    cleared = True
                    logger.debug(f"Cleared token from file store for user {user_id}")

        if key in self._memory_store:
            del self._memory_store[key]
            cleared = True
            logger.debug(f"Cleared token from memory for user {user_id}")

        return cleared

    async def refresh_token(self, user_id: str) -> Optional[StoredToken]:
        """Refresh an expired token using the refresh token.

        Args:
            user_id: Unique user identifier

        Returns:
            New StoredToken if refresh succeeded, None otherwise
        """
        token = self.get_token(user_id)
        if not token or not token.refresh_token:
            logger.warning(f"No refresh token available for user {user_id}")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.auth0_domain}/oauth/token",
                    data={
                        "grant_type": "refresh_token",
                        "client_id": self.client_id,
                        "refresh_token": token.refresh_token,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    error_code = None
                    error_detail = response.text
                    try:
                        payload = response.json()
                        error_code = payload.get("error")
                        error_detail = payload.get("error_description") or payload.get("error") or response.text
                    except Exception:
                        pass
                    logger.error(f"Token refresh failed: {error_detail}")
                    if error_code == "invalid_grant":
                        raise TokenRefreshError(error_detail, code=error_code)
                    return None

                data = response.json()
                return self.store_token(
                    user_id=user_id,
                    access_token=data["access_token"],
                    expires_in=data.get("expires_in", 86400),
                    refresh_token=data.get("refresh_token", token.refresh_token),
                    user_email=token.user_email,
                    user_name=token.user_name,
                    user_sub=token.user_sub,
                    user_idp=token.user_idp,
                    user_picture=token.user_picture,
                )

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None

    async def get_valid_token(self, user_id: str) -> Optional[str]:
        """Get a valid access token, refreshing if necessary.

        Args:
            user_id: Unique user identifier

        Returns:
            Valid access token string, or None if not available
        """
        token = self.get_token(user_id)
        if not token:
            return None

        if token.is_expired():
            logger.info(f"Token expired for user {user_id}, attempting refresh")
            try:
                token = await self.refresh_token(user_id)
            except TokenRefreshError:
                return None
            if not token:
                return None

        return token.access_token
