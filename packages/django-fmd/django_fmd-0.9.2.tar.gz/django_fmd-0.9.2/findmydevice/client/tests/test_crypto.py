import json
import unittest
from pathlib import Path

from bx_py_utils.path import assert_is_file
from Cryptodome.PublicKey.RSA import RsaKey

from findmydevice.client import constants
from findmydevice.client.crypto import (
    assert_endswith,
    assert_startswith,
    decrypt_packet_modern,
    decrypt_private_key,
    unwrap_private_key_modern,
)


BASE_PATH = Path(__file__).parent


def get_fixture(file_name: str) -> str:
    file_path = Path(BASE_PATH / 'fixtures', file_name)
    assert_is_file(file_path)
    return file_path.read_text('ASCII')


def get_encrypted_private_key() -> str:
    return get_fixture('encrypted_private_key.txt')


def get_encrypted_location() -> str:
    return get_fixture('encrypted_location.txt')


class CryptoTestCase(unittest.TestCase):
    def test_decrypt_private_key(self):
        pem_string = decrypt_private_key(key_data=get_encrypted_private_key(), password='pp')
        self.assertIsInstance(pem_string, str)
        assert_startswith(text=pem_string, prefix=constants.PRIVATE_KEY_PREFIX)
        assert_endswith(text=pem_string, suffix=constants.PRIVATE_KEY_SUFFIX)

    def test_unwrap_private_key_modern(self):
        rsa_private_key = unwrap_private_key_modern(key_data=get_encrypted_private_key(), password='pp')
        self.assertIsInstance(rsa_private_key, RsaKey)
        self.assertEqual(rsa_private_key.size_in_bits(), constants.FMD_RSA_KEY_SIZE_BITS)
        self.assertTrue(rsa_private_key.has_private())  # Is an RSA private key?

    def test_decrypt_packet_modern(self):
        rsa_private_key = unwrap_private_key_modern(key_data=get_encrypted_private_key(), password='pp')
        location_data = decrypt_packet_modern(
            rsa_crypto_key=rsa_private_key,
            packet_base64=get_encrypted_location(),
        )
        self.assertIsInstance(location_data, str)
        location_data = json.loads(location_data)
        self.assertEqual(
            location_data,
            {
                'bat': '57',
                'date': 1718647584637,
                'lat': '51.4378',
                'lon': '6.617',
                'provider': 'fused',
                'time': 'Mon Jun 17 20:06:24 GMT+02:00 2024',
            },
        )
