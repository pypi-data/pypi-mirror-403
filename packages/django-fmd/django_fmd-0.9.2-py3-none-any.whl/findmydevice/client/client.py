import json
import logging

import requests
from Cryptodome.PublicKey.RSA import RsaKey
from requests import Response

from findmydevice.client import __version__
from findmydevice.client.crypto import decrypt_packet_modern, hash_password4login, unwrap_private_key_modern
from findmydevice.client.data_classes import ClientDeviceData, LocationData, LocationDataSize
from findmydevice.urls import VERSION_PREFIX


logger = logging.getLogger(__name__)


def debug_response(response: Response, level=logging.DEBUG):
    logger.log(level, 'Response.url: %r', response.url)
    logger.log(level, 'Response.status_code: %r', response.status_code)
    logger.log(level, 'Response.headers: %r', response.headers)
    logger.log(level, 'Response.links: %r', response.links)
    logger.log(level, 'Response.content: %r', response.content)


class FmdClient:
    user_agent = f'python-fmd-client/{__version__}'

    def __init__(self, fmd_server_url, raise_wrong_responses=False, ssl_verify=True):
        logger.debug(
            'FMD server url: %r (raise_wrong_responses:%r, ssl_verify:%r)',
            fmd_server_url,
            raise_wrong_responses,
            ssl_verify,
        )
        self.fmd_server_url = fmd_server_url.rstrip('/')
        self.raise_wrong_responses = raise_wrong_responses

        self.session = requests.Session()
        self.session.verify = ssl_verify
        self.session.headers['user-agent'] = self.user_agent

    def _request(self, func, url: str, payload: dict | None = None) -> Response:
        uri = f'{self.fmd_server_url}/{url}'
        logger.debug('%s %r %r', func.__name__.upper(), uri, payload)
        if payload is None:
            kwargs = {}
        else:
            kwargs = {'json': payload}
        response: Response = func(uri, allow_redirects=False, **kwargs)

        if response.status_code > 400:
            logger.error('%s response: %r', func.__name__.upper(), response)
        else:
            logger.debug('%s response: %r', func.__name__.upper(), response)

        if response.status_code > 300:
            logger.warning('Raw response content: %r', response.content)

        response.raise_for_status()
        return response

    def get(self, url: str) -> Response:
        return self._request(func=self.session.get, url=url)

    def put(self, url: str, payload: dict) -> Response:
        return self._request(func=self.session.put, url=url, payload=payload)

    def post(self, url: str, payload: dict) -> Response:
        return self._request(func=self.session.post, url=url, payload=payload)

    ##############################################################################################
    def get_access_token(self, *, client_device_data: ClientDeviceData) -> str | None:
        # TODO: Cache the token!

        self.assume_hash_password4login(client_device_data=client_device_data)

        assert client_device_data.short_id

        response = self.put(
            url=f'{VERSION_PREFIX}/requestAccess',
            payload={
                'IDT': client_device_data.short_id,
                'Data': client_device_data.hashed_password,
            },
        )
        data = response.json()

        short_id = data['IDT']
        assert (
            short_id == client_device_data.short_id
        ), f'Device ID mismatch: {short_id!r} is not {client_device_data.short_id!r}'

        access_token = data['Data']
        return access_token

    ##############################################################################################

    def assume_salt(self, *, client_device_data: ClientDeviceData) -> None:
        assert client_device_data.short_id, 'Device ID is needed to request the password salt!'
        if client_device_data.password_salt is None:
            response: Response = self.put(
                url=f'{VERSION_PREFIX}/salt',
                payload={'IDT': client_device_data.short_id},
            )
            data = response.json()
            salt = data['Data']
            assert salt, f'No salt received from {data=}'
            client_device_data.password_salt = salt

    def assume_hash_password4login(self, *, client_device_data: ClientDeviceData) -> None:
        if client_device_data.hashed_password is None:
            assert client_device_data.plaintext_password, 'Password must be set!'
            self.assume_salt(client_device_data=client_device_data)
            logger.info('Calculate hashed password...')
            client_device_data.hashed_password = hash_password4login(
                password=client_device_data.plaintext_password,
                salt=client_device_data.password_salt,
            )

    ##############################################################################################

    def assume_private_key(self, *, client_device_data: ClientDeviceData) -> None:
        if not client_device_data.encrypted_private_key:
            access_token = self.get_access_token(client_device_data=client_device_data)

            response: Response = self.put(
                url=f'{VERSION_PREFIX}/key',
                payload={
                    'IDT': access_token,
                    'Data': 'unused',  # Same as in FMD JS getPrivateKey()
                },
            )
            response_data = response.json()
            encrypted_private_key = response_data['Data']
            logger.info('Received private key (%i bytes)', len(encrypted_private_key))
            client_device_data.encrypted_private_key = encrypted_private_key

        if not client_device_data.private_key:
            client_device_data.private_key = unwrap_private_key_modern(
                key_data=client_device_data.encrypted_private_key,
                password=client_device_data.plaintext_password,
            )

    ##############################################################################################

    def get_version(self):
        response: Response = self.get(url=f'{VERSION_PREFIX}/version')
        raw_version = response.content.decode('utf-8')
        return raw_version

    def register(self, client_device_data: ClientDeviceData):
        """
        Register a new Device
        """
        logger.debug('Register new device on %r...', self.fmd_server_url)
        assert client_device_data.hashed_password
        assert client_device_data.encrypted_private_key
        assert client_device_data.public_key_base64_str
        response = self.put(
            url=f'{VERSION_PREFIX}/device',
            payload={
                'hashedPassword': client_device_data.hashed_password,
                'privkey': client_device_data.encrypted_private_key,
                'pubkey': client_device_data.public_key_base64_str,
                'registrationToken': client_device_data.registration_token,
            },
        )
        try:
            data = response.json()
        except Exception as err:
            logger.error('Device register error: %r', err)
            debug_response(response, level=logging.WARNING)
            raise

        device_id = data['DeviceId']
        client_device_data.short_id = device_id
        logger.info('New device registered at %r with ID: %r', self.fmd_server_url, device_id)

    def get_location_data_size(self, client_device_data: ClientDeviceData) -> LocationDataSize:
        access_token = self.get_access_token(client_device_data=client_device_data)

        response: Response = self.put(
            url=f'{VERSION_PREFIX}/locationDataSize',
            payload={
                'IDT': access_token,
                'Data': 'NaN',  # ;)
            },
        )
        response_data = response.json()
        location_data_size = LocationDataSize(
            length=response_data['DataLength'],
            beginning=response_data['DataBeginningIndex'],
        )
        return location_data_size

    def get_location(self, *, client_device_data: ClientDeviceData, index: int = -1) -> LocationData:
        access_token = self.get_access_token(client_device_data=client_device_data)

        response: Response = self.put(
            url=f'{VERSION_PREFIX}/location',
            payload={
                'IDT': access_token,
                'Data': str(index),  # FMD server accepts only a string!
            },
        )
        response_data = response.json()
        encrypted_data = response_data['Data']
        assert encrypted_data, f'No location data received: {response_data=}'

        self.assume_private_key(client_device_data=client_device_data)
        private_key: RsaKey = client_device_data.private_key

        location_data_str = decrypt_packet_modern(rsa_crypto_key=private_key, packet_base64=encrypted_data)
        location_data = json.loads(location_data_str)

        location = LocationData(
            bat=location_data['bat'],
            lat=location_data['lat'],
            lon=location_data['lon'],
            provider=location_data['provider'],
            date=location_data['date'],
            time=location_data['time'],
        )
        return location

    def _assert_empty(self, response):
        if response.content != b'':
            logger.warning('Unexpected response:')
            debug_response(response, level=logging.WARNING)
            if self.raise_wrong_responses:
                raise AssertionError(f'Unexpected response: {response.content!r}')
