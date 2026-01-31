import base64
import json
from pathlib import Path
from typing import override

import pytest

from neva.security.encryption import AesEncrypter, Encrypter
from neva.support.facade import Crypt
from neva.testing import TestCase


VALID_KEY = AesEncrypter.generate_key()
PREVIOUS_KEY = AesEncrypter.generate_key()


def _make_config_dir(
    tmp_path: Path,
    *,
    key: str = VALID_KEY,
    previous_keys: str = "[]",
) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    _ = (config_dir / "app.py").write_text(
        f"""
config = {{
    "name": "TestApp",
    "debug": True,
    "key": "{key}",
    "previous_keys": {previous_keys},
}}
"""
    )

    _ = (config_dir / "providers.py").write_text(
        """
from neva.security import SecurityProvider

config = {"providers": [SecurityProvider]}
"""
    )

    return config_dir


class TestEncryptDecryptRoundTrip(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_encrypt_decrypt_string(self) -> None:
        encrypted = Crypt.encrypt("hello world").unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == "hello world"

    async def test_encrypt_decrypt_integer(self) -> None:
        encrypted = Crypt.encrypt(42).unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == 42

    async def test_encrypt_decrypt_float(self) -> None:
        encrypted = Crypt.encrypt(3.14).unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == 3.14

    async def test_encrypt_decrypt_boolean(self) -> None:
        encrypted = Crypt.encrypt(True).unwrap()  # noqa: FBT003
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted is True

    async def test_encrypt_decrypt_none(self) -> None:
        encrypted = Crypt.encrypt(None).unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted is None

    async def test_encrypt_decrypt_list(self) -> None:
        value = [1, "two", 3.0, None]
        encrypted = Crypt.encrypt(value).unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == value

    async def test_encrypt_decrypt_dict(self) -> None:
        value = {"key": "value", "nested": {"a": 1}}
        encrypted = Crypt.encrypt(value).unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == value

    async def test_encrypt_decrypt_empty_string(self) -> None:
        encrypted = Crypt.encrypt("").unwrap()
        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == ""


class TestEncryptProducesDifferentCiphertexts(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_same_value_produces_different_ciphertexts(self) -> None:
        a = Crypt.encrypt("same value").unwrap()
        b = Crypt.encrypt("same value").unwrap()

        assert a != b


class TestDecryptErrors(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_decrypt_invalid_base64(self) -> None:
        result = Crypt.decrypt("not-valid-base64!!!")

        assert result.is_err

    async def test_decrypt_invalid_json_payload(self) -> None:
        bad_payload = base64.b64encode(b"not json").decode("ascii")
        result = Crypt.decrypt(bad_payload)

        assert result.is_err

    async def test_decrypt_missing_fields(self) -> None:
        incomplete = base64.b64encode(json.dumps({"iv": "abc"}).encode()).decode(
            "ascii"
        )
        result = Crypt.decrypt(incomplete)

        assert result.is_err

    async def test_decrypt_wrong_key(self, tmp_path: Path) -> None:
        encrypted = Crypt.encrypt("secret").unwrap()

        from neva.arch import Application

        other_key = AesEncrypter.generate_key()
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        config_dir = _make_config_dir(other_dir, key=other_key)
        other_app = Application(config_path=config_dir)
        other_enc = AesEncrypter(other_app)

        result = other_enc.decrypt(encrypted)
        assert result.is_err
        assert "invalid key or corrupted data" in result.unwrap_err()


class TestEncryptSerializationError(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_encrypt_non_serializable_returns_err(self) -> None:
        result = Crypt.encrypt(object())  # type: ignore[arg-type]

        assert result.is_err
        assert "Failed to serialize" in result.unwrap_err()


class TestKeyRotation(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(
            tmp_path,
            key=VALID_KEY,
            previous_keys=f'["{PREVIOUS_KEY}"]',
        )

    async def test_decrypt_with_previous_key(self) -> None:
        from tempfile import TemporaryDirectory

        from neva.arch import Application

        with TemporaryDirectory() as tmp:
            config_dir = _make_config_dir(Path(tmp), key=PREVIOUS_KEY)
            old_app = Application(config_path=config_dir)
            old_encrypter = AesEncrypter(old_app)
            encrypted = old_encrypter.encrypt("rotated secret").unwrap()

        decrypted = Crypt.decrypt(encrypted).unwrap()

        assert decrypted == "rotated secret"

    async def test_encrypt_uses_current_key(self) -> None:
        from tempfile import TemporaryDirectory

        from neva.arch import Application

        encrypted = Crypt.encrypt("new secret").unwrap()

        with TemporaryDirectory() as tmp:
            config_dir = _make_config_dir(Path(tmp), key=VALID_KEY)
            current_only_app = Application(config_path=config_dir)
            encrypter = AesEncrypter(current_only_app)
            decrypted = encrypter.decrypt(encrypted).unwrap()

        assert decrypted == "new secret"


class TestContainerResolution(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_resolves_encrypter_from_container(self) -> None:
        result = self.app.make(Encrypter)

        assert result.is_ok

    async def test_resolved_encrypter_encrypts(self) -> None:
        encrypter = self.app.make(Encrypter).unwrap()
        encrypted = encrypter.encrypt("from container").unwrap()
        decrypted = encrypter.decrypt(encrypted).unwrap()

        assert decrypted == "from container"


class TestKeyValidation:
    def test_missing_key_raises(self) -> None:
        from tempfile import TemporaryDirectory

        from neva.arch import Application

        with TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            _ = (config_dir / "app.py").write_text(
                'config = {"name": "TestApp", "debug": True}'
            )
            _ = (config_dir / "providers.py").write_text(
                """
from neva.security import SecurityProvider

config = {"providers": [SecurityProvider]}
"""
            )

            app = Application(config_path=config_dir)
            encrypter = AesEncrypter(app)

            with pytest.raises(ValueError, match="No encryption key configured"):
                _ = encrypter.encrypt("fail")

    def test_invalid_base64_key_raises(self) -> None:
        from tempfile import TemporaryDirectory

        from neva.arch import Application

        with TemporaryDirectory() as tmp:
            config_dir = _make_config_dir(Path(tmp), key="not-valid-base64!!!")
            app = Application(config_path=config_dir)
            encrypter = AesEncrypter(app)

            with pytest.raises(ValueError, match="must be valid base64"):
                _ = encrypter.encrypt("fail")

    def test_wrong_length_key_raises(self) -> None:
        from tempfile import TemporaryDirectory

        from neva.arch import Application

        short_key = base64.b64encode(b"tooshort").decode()

        with TemporaryDirectory() as tmp:
            config_dir = _make_config_dir(Path(tmp), key=short_key)
            app = Application(config_path=config_dir)
            encrypter = AesEncrypter(app)

            with pytest.raises(ValueError, match="must be 32 bytes"):
                _ = encrypter.encrypt("fail")


class TestGenerateKey:
    def test_generate_key_returns_valid_base64(self) -> None:
        key = AesEncrypter.generate_key()
        decoded = base64.b64decode(key)

        assert len(decoded) == 32

    def test_generate_key_is_unique(self) -> None:
        a = AesEncrypter.generate_key()
        b = AesEncrypter.generate_key()

        assert a != b


class TestEncrypterProtocol(TestCase):
    @override
    def create_config(self, tmp_path: Path) -> Path:
        return _make_config_dir(tmp_path)

    async def test_aes_encrypter_satisfies_protocol(self) -> None:
        encrypter = self.app.make(Encrypter).unwrap()

        assert isinstance(encrypter, Encrypter)
