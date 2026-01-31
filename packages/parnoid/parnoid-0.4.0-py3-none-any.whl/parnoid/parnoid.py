"""
This SDK can be used in conjunction with Parnoid.io API to authenticate, encrypt and decrypt data in Python implementations.
Copyright (c) Parnoid AG. All rights reserved.
"""

import base64
import json
import os
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, TypedDict, Callable
from urllib.parse import urlparse, urljoin

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from requests import Request, Response


class ParnoidConfig(TypedDict):
    """
    Config object to be passed for setting up Parnoid via ParnoidClient.
    """

    parnoid_auth_base_url: str
    """
    URL to use for authentication.
    If you set up a custom domain, you need to enter it here.
    """

    parnoid_api_base_url: str
    """
    URL to use for the Parnoid API.
    """

    origin: str
    """
    An allowed origin configured in the Pool Settings.
    """

    token_func: Callable[[], str]
    """
    A function returning a valid JWT for authentication.
    """


class ParnoidSealedKeyEnvelope(TypedDict):
    version: int
    kid: str
    okid: str
    pid: str
    sender_id: str
    created: int
    signature: str
    sealed: Dict[str, str]


class ParnoidUnsealedKeyEnvelope(ParnoidSealedKeyEnvelope):
    plaintext_data_key: str


class ParnoidEnvelope:
    """
    `ParnoidEnvelope` is returned when encrypting data using `ParnoidClient.seal_for_recipients`.
    It contains the ciphertext as `bytes`, depending on how you process the data further you can either use the
    provided serialization methods (`ParnoidEnvelope.to_json`) or implement your own.
    """
    ciphertext: bytes
    key_envelope: ParnoidSealedKeyEnvelope

    def __init__(self, ciphertext: bytes, key_envelope: ParnoidSealedKeyEnvelope):
        """
        Creates new `ParnoidEnvelope` from given ciphertext and key envelope.
        """
        self.ciphertext = ciphertext
        self.key_envelope = key_envelope

    def to_json(self) -> str:
        """
        Serializes the `ParnoidEnvelope` into a JSON string.
        """
        return json.dumps({
            'ciphertext': base64.b64encode(self.ciphertext).decode('utf-8'),
            'keyEnvelope': self.key_envelope,
        })

    @staticmethod
    def from_json(data: str) -> 'ParnoidEnvelope':
        """
        Deserializes a JSON string into a ParnoidEnvelope.
        """
        obj = json.loads(data)
        return ParnoidEnvelope(
            ciphertext=base64.b64decode(obj['ciphertext']),
            key_envelope=obj['keyEnvelope'],
        )


class ParnoidClient:
    IV_LENGTH = 12
    REQUEST_TIMEOUT = 10

    def __init__(self, config: ParnoidConfig):
        """
        Create new instance of ParnoidClient
        Args:
            config: Configuration object
        """
        err = self._validate_config(config)
        if err:
            raise ValueError(f"Invalid config: {err}")

        self.parnoid_auth_base_url = config['parnoid_auth_base_url']
        self.parnoid_api_base_url = config['parnoid_api_base_url']
        self.origin = config['origin']
        self.token_func = config['token_func']

        self._refresh_token: Optional[ParnoidRefreshToken] = None
        self._access_token: Optional[ParnoidAccessToken] = None

        self._session = requests.Session()

    def logout(self) -> None:
        """Logout user and clear all state"""
        self._access_token = None
        self._refresh_token = None

    def seal_for_recipients(self, plaintext: bytes, recipients: List[str]) -> ParnoidEnvelope:
        """
        Encrypts data for the given list of receivers and returns a `ParnoidEnvelope` containing the ciphertext as
        `bytes` and the `ParnoidSealedKeyEnvelope`.

        Depending on how you want to process the ciphertext further, you can either use the provided serialization
        methods (`ParnoidEnvelope.to_json`) or implement your own.

        Args:
            plaintext (bytes): Data to encrypt
            recipients (List[str]): List of user IDs
        Returns:
            ParnoidEnvelope: Encrypted envelope
        """
        try:
            unsealed_envelope = self._get_key_envelope(recipients)

            iv = os.urandom(self.IV_LENGTH)
            key = base64.b64decode(unsealed_envelope['plaintext_data_key'])

            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(iv, plaintext, None)

            return ParnoidEnvelope(
                ciphertext=iv + ciphertext,
                key_envelope=self._convert_key_envelope(unsealed_envelope),
            )
        except Exception as e:
            raise Exception(f"Failed to encrypt: {str(e)}") from e

    def unseal(self, envelope: ParnoidEnvelope) -> bytes:
        """
        Decrypts the data from the given `ParnoidEnvelope` and returns the plaintext.

        Args:
            envelope (ParnoidEnvelope): Encrypted envelope
        Returns:
            bytes: Decrypted data
        """
        try:
            iv = envelope.ciphertext[:self.IV_LENGTH]
            ciphertext = envelope.ciphertext[self.IV_LENGTH:]

            unsealed_key_envelope = self._unseal_key_envelope(envelope.key_envelope)
            key = base64.b64decode(unsealed_key_envelope['plaintext_data_key'])

            aesgcm = AESGCM(key)
            return aesgcm.decrypt(iv, ciphertext, None)
        except Exception as e:
            raise Exception(f"Failed to decrypt: {str(e)}") from e

    def reseal(self, key_envelope: ParnoidSealedKeyEnvelope, recipients: List[str]) -> ParnoidSealedKeyEnvelope:
        """
        Reseal creates new data keys for the given receivers based on the given `ParnoidSealedKeyEnvelope` and returns a
        new `ParnoidSealedKeyEnvelope` containing the new keys.

        The `ParnoidSealedKeyEnvelope` can be obtained from `ParnoidEnvelope.key_envelope`.

        Args:
            key_envelope (ParnoidSealedKeyEnvelope): Key envelope
            recipients (List[str]): List of user IDs
        Returns:
            ParnoidSealedKeyEnvelope: Resealed key envelope
        """
        try:
            return self._reseal_key_envelope(key_envelope, recipients)
        except Exception as e:
            raise Exception(f"Failed to reseal: {str(e)}") from e

    def _get_access_token(self) -> str:
        # Add a 5-minute skew/padding to prevent access token expiry issues during request execution
        if self._access_token and datetime.now(tz=UTC) + timedelta(minutes=5) < self._access_token['expiration']:
                return self._access_token['token']

        # Add a 5-minute skew/padding to prevent refresh token expiry issues during request execution
        if not self._refresh_token or datetime.now(tz=UTC) + timedelta(minutes=5) > self._refresh_token['expiration']:
            customer_token = self.token_func()
            self._authenticate(customer_token)

        try:
            self._refresh_access_token()
            return self._access_token['token']
        except Exception as e:
            raise Exception(f"Not authenticated: {str(e)}") from e

    def _authenticate(self, customer_token: str) -> None:
        if not customer_token:
            raise ValueError("Token is missing")

        req = self._build_auth_request(path='authenticate', request=Request(
            method='post',
            headers={
                'Authorization': f'Bearer {customer_token}'
            },
        ))

        response = self._send_request(req)

        if not response.ok:
            raise Exception(f"Failed to authenticate: {response.reason}")

        data = response.json()

        self._refresh_token = {
            'token': data['refresh_token'],
            'expiration': datetime.fromisoformat(data['expiration'])
        }

    def _refresh_access_token(self) -> None:
        req = self._build_auth_request(path='token', request=Request(
            method='get',
            headers={
                'Authorization': f'Bearer {self._refresh_token["token"]}'
            },
        ))

        response = self._send_request(req)

        if not response.ok:
            raise Exception(f"Failed to get token: {response.reason}")

        data = response.json()

        self._access_token = {
            'token': data['token'],
            'expiration': datetime.fromisoformat(data['expiration'])
        }

    def _get_key_envelope(self, receiver_ids: List[str]) -> ParnoidUnsealedKeyEnvelope:
        req = self._build_api_request(path='createdatakey', request=Request(
            method='post',
            json={'receiver_ids': receiver_ids},
        ))

        response = self._send_request(req)

        if not response.ok:
            raise Exception(f"Failed to create data key: {response.reason}")

        return response.json()

    def _unseal_key_envelope(self, envelope: ParnoidSealedKeyEnvelope) -> ParnoidUnsealedKeyEnvelope:
        req = self._build_api_request(path='unsealdatakey', request=Request(
            method='post',
            json={'sealed_data_key': envelope},
        ))

        response = self._send_request(req)

        if not response.ok:
            raise Exception(f"Failed to unseal data key: {response.reason}")

        return response.json()

    def _reseal_key_envelope(self, envelope: ParnoidSealedKeyEnvelope, receiver_ids: List[str]) -> ParnoidSealedKeyEnvelope:
        req = self._build_api_request(path='resealdatakey', request=Request(
            method='post',
            json={
                'sealed_data_key': envelope,
                'receiver_ids': receiver_ids
            },
        ))

        response = self._send_request(req)

        if not response.ok:
            raise Exception(f"Failed to reseal data key: {response.reason}")

        return response.json()

    def _build_auth_request(self, path: str, request: Request) -> Request:
        request.url = urljoin(self.parnoid_auth_base_url, path)
        request.headers['Content-Type'] = 'application/json'
        request.headers['Origin'] = self.origin

        return request

    def _build_api_request(self, path: str, request: Request) -> Request:
        request.url = urljoin(self.parnoid_api_base_url, path)
        request.headers['Authorization'] = f'Bearer {self._get_access_token()}'
        request.headers['Content-Type'] = 'application/json'
        request.headers['Origin'] = self.origin

        return request

    def _send_request(self, request: Request) -> Response:
        prepped = self._session.prepare_request(request)
        response = self._session.send(prepped, timeout=self.REQUEST_TIMEOUT)
        return response

    @staticmethod
    def _validate_config(config: ParnoidConfig) -> Optional[str]:
        def is_valid_url(url: str) -> bool:
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except Exception:
                return False

        if not is_valid_url(config['parnoid_auth_base_url']):
            return 'parnoid_auth_base_url is not a valid URL'
        if not is_valid_url(config['parnoid_api_base_url']):
            return 'parnoid_api_base_url is not a valid URL'
        if not is_valid_url(config['origin']):
            return 'origin is not a valid URL'
        return None

    @staticmethod
    def _convert_key_envelope(unsealed_envelope: ParnoidUnsealedKeyEnvelope) -> ParnoidSealedKeyEnvelope:
        sealed_envelope = unsealed_envelope.copy()
        del sealed_envelope['plaintext_data_key']
        return sealed_envelope


class ParnoidAccessToken(TypedDict):
    token: str
    expiration: datetime


class ParnoidRefreshToken(TypedDict):
    token: str
    expiration: datetime
