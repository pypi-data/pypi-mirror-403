import dataclasses

from Cryptodome.PublicKey.RSA import RsaKey


@dataclasses.dataclass
class ClientDeviceData:
    plaintext_password: str = None
    password_salt: str = None
    hashed_password: str = None
    device_id: str = None
    short_id: str = None
    encrypted_private_key: str = None
    private_key: RsaKey | None = None
    public_key_base64_str: str = None
    registration_token: str = ''


@dataclasses.dataclass
class LocationDataSize:
    length: int = None
    beginning: int = None


@dataclasses.dataclass
class LocationData:
    bat: str = None
    lat: str = None
    lon: str = None
    provider: str = None
    date: int = None
    time: str = None
