import os
import base64
import hmac
import hashlib

from google.cloud import kms


# https://dev.to/googlecloud/using-secrets-in-google-cloud-functions-5aem
kms_client = kms.KeyManagementServiceClient()
GITHUB_ACCESS_TOKEN = kms_client.decrypt(
    os.environ['GITHUB_ACCESS_TOKEN_RESOURCE'],
    base64.b64decode(os.environ['GITHUB_ACCESS_TOKEN']),
).plaintext.decode('utf-8')
GITHUB_WEBHOOK_SECRET = kms_client.decrypt(
    os.environ['GITHUB_WEBHOOK_SECRET_RESOURCE'],
    base64.b64decode(os.environ['GITHUB_WEBHOOK_SECRET']),
).plaintext.decode('utf-8')


class GithubRequestException(Exception):
    pass


class GithubRequestValidator:

    def __init__(self, secret):
        self.secret = secret

    @staticmethod
    def _check_method(method):
        if method != 'POST':
            message = f'Method not allowed: {method}'
            raise GithubRequestException(message)

    def _check_signature(self, signature, raw_data):
        digest_maker = hmac.new(bytes(self.secret, 'utf-8'), raw_data, hashlib.sha1)
        if signature.split('=')[1] != digest_maker.hexdigest():
            message = f'Invalid signature: {signature}'
            raise GithubRequestException(message)

    def validate_webhook(self, request):
        method = request.method
        signature = request.headers.get('X-Hub-Signature', '')
        raw_data = request.get_data()

        self._check_method(method)
        self._check_signature(signature, raw_data)


def webhook_handler(request):
    try:
        GithubRequestValidator(GITHUB_WEBHOOK_SECRET).validate_webhook(request)
    except GithubRequestException:
        return '', 302

    print('success!')
    return '', 200
