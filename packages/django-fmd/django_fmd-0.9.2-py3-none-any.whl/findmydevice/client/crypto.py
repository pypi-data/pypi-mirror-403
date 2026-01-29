import base64
import logging
from base64 import b64decode

from argon2 import PasswordHasher
from Cryptodome.PublicKey import RSA
from Cryptodome.PublicKey.RSA import RsaKey
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from findmydevice.client import constants


logger = logging.getLogger(__name__)


def decode_base64(data):
    """
    >>> decode_base64('aGVsbG8=')
    b'hello'
    >>> decode_base64('aGVsbG8')
    b'hello'
    """
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data)


def hash_password_argon2(*, password: str, salt: str | bytes) -> str:
    """
    Counterpart of FMD: hashPasswordArgon2() in:
    https://gitlab.com/fmd-foss/fmd-server/-/blob/master/web/fmdcrypto.js

    >>> hash_password_argon2(password='context:loginAuthentication'+'pp', salt='YeAM+gUcbAdm5UKles3Ldw')
    '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
    """
    assert password.startswith(
        constants.FMD_CONTEXT_PREFIX
    ), f'Password must start with {constants.FMD_CONTEXT_PREFIX=}'
    if isinstance(salt, str):
        salt = decode_base64(salt)

    ph = PasswordHasher(
        time_cost=constants.FMD_ARGON2_T,
        memory_cost=constants.FMD_ARGON2_M,
        parallelism=constants.FMD_ARGON2_P,
        hash_len=constants.FMD_ARGON2_HASH_LENGTH,
        salt_len=constants.FMD_ARGON2_SALT_LENGTH,
    )
    hash = ph.hash(password=password, salt=salt)
    return hash


def hash_password4login(*, password: str, salt: str | bytes):
    """
    Counterpart of FMD: hashPasswordForLoginModern() in:
    https://gitlab.com/fmd-foss/fmd-server/-/blob/master/web/fmdcrypto.js

    >>> hash_password4login(password='pp', salt='YeAM+gUcbAdm5UKles3Ldw')
    '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
    """
    return hash_password_argon2(password=constants.FMD_CONTEXT_STRING_LOGIN + password, salt=salt)


def hash_password4key_wrap(*, password: str, salt: str | bytes):
    """
    Counterpart of FMD: hashPasswordForKeyWrap() in:
    https://gitlab.com/fmd-foss/fmd-server/-/blob/master/web/fmdcrypto.js

    >>> hash_password4login(password='pp', salt='YeAM+gUcbAdm5UKles3Ldw')
    '$argon2id$v=19$m=131072,t=1,p=4$YeAM+gUcbAdm5UKles3Ldw$W+m4nT7UK/T6h9PUxQRxyEo8AQ9aHr9YgQAlSzspin4'
    """
    return hash_password_argon2(password=constants.FMD_CONTEXT_STRING_ASYM_KEY_WRAP + password, salt=salt)


def assert_startswith(text: str, prefix: str):
    assert text.startswith(prefix), f'{text=} must start with {prefix=}'


def remove_prefix(text: str, prefix: str) -> str:
    assert_startswith(text=text, prefix=prefix)
    return text[len(prefix) :]


def assert_endswith(text: str, suffix: str):
    assert text.endswith(suffix), f'{text=} must end with {suffix=}'


def remove_suffix(text: str, suffix: str) -> str:
    assert_endswith(text=text, suffix=suffix)
    return text[: -len(suffix)]


def decrypt_private_key(*, key_data, password) -> str:
    """
    Decrypt the private key with the given password.
    """
    concat_bytes = b64decode(key_data)
    salt_bytes = concat_bytes[: constants.FMD_ARGON2_SALT_LENGTH]
    iv_bytes = concat_bytes[
        constants.FMD_ARGON2_SALT_LENGTH : constants.FMD_ARGON2_SALT_LENGTH + constants.FMD_AES_GCM_IV_SIZE_BYTES
    ]
    wrapped_key_bytes = concat_bytes[constants.FMD_ARGON2_SALT_LENGTH + constants.FMD_AES_GCM_IV_SIZE_BYTES :]

    # Hash the password
    result = hash_password4key_wrap(password=password, salt=salt_bytes)
    password_hash = result.rpartition('$')[-1]
    aes_key = decode_base64(password_hash)

    aesgcm = AESGCM(aes_key)
    plaintext_bytes = aesgcm.decrypt(iv_bytes, wrapped_key_bytes, None)
    raw_private_key = serialization.load_pem_private_key(plaintext_bytes, password=None, backend=default_backend())

    private_key_bytes = raw_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key = private_key_bytes.decode('utf-8')
    return private_key


def unwrap_private_key_modern(*, key_data, password) -> RsaKey:
    """
    Counterpart of FMD: unwrapPrivateKeyModern() in:
    https://gitlab.com/fmd-foss/fmd-server/-/blob/master/web/fmdcrypto.js
    """
    private_key = decrypt_private_key(key_data=key_data, password=password)

    private_key = remove_prefix(text=private_key, prefix=constants.PRIVATE_KEY_PREFIX)
    private_key = remove_suffix(text=private_key, suffix=constants.PRIVATE_KEY_SUFFIX)
    binary_der = b64decode(private_key)

    rsa_private_key = RSA.import_key(binary_der)
    return rsa_private_key


def decrypt_packet_modern(*, rsa_crypto_key: RsaKey, packet_base64: str) -> str:
    """
    Counterpart of FMD: decryptPacketModern() in:
    https://gitlab.com/fmd-foss/fmd-server/-/blob/master/web/fmdcrypto.js
    """

    concat_bytes = b64decode(packet_base64)
    session_key_packet_bytes = concat_bytes[: constants.FMD_RSA_KEY_SIZE_BYTES]
    iv_bytes = concat_bytes[
        constants.FMD_RSA_KEY_SIZE_BYTES : constants.FMD_RSA_KEY_SIZE_BYTES + constants.FMD_AES_GCM_IV_SIZE_BYTES
    ]
    ct_bytes = concat_bytes[constants.FMD_RSA_KEY_SIZE_BYTES + constants.FMD_AES_GCM_IV_SIZE_BYTES :]

    auth_tag = ct_bytes[-16:]  # The authentication tag is typically the last 16 bytes
    ct_bytes = ct_bytes[:-16]  # The rest is the actual ciphertext

    private_key = serialization.load_pem_private_key(
        rsa_crypto_key.export_key(format='PEM', pkcs=8),
        password=None,
        backend=default_backend(),
    )

    # Decrypt the session key
    session_key_bytes = private_key.decrypt(
        session_key_packet_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Decrypt the ciphertext
    cipher = Cipher(algorithms.AES(session_key_bytes), modes.GCM(iv_bytes, auth_tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ct_bytes)
    plaintext += decryptor.finalize()
    return plaintext.decode('utf-8')
