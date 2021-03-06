import hmac
import hashlib

from .exceptions import GithubRequestException


class GithubRequestValidator:

    def __init__(self, secret):
        self.secret = secret

    @staticmethod
    def _check_method(method):
        if method != 'POST':
            message = f'Method not allowed: {method}'
            raise GithubRequestException(message)

    def _check_signature(self, signature, raw_data):
        try:
            digest = signature.split('=')[1]
        except IndexError:
            message = f'Unexpected signature format: {signature}'
            raise GithubRequestException(message)
        digest_maker = hmac.new(bytes(self.secret, 'utf-8'), raw_data, hashlib.sha1)
        if digest != digest_maker.hexdigest():
            message = f'Invalid signature: {signature}'
            raise GithubRequestException(message)

    def validate_webhook(self, request):
        method = request.method
        signature = request.headers.get('X-Hub-Signature', '')
        raw_data = request.get_data()

        self._check_method(method)
        self._check_signature(signature, raw_data)
