import os
import base64
import hmac
import hashlib

from github import Github
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
GITHUB_REPO = os.environ['GITHUB_REPO']


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


class GithubPullRequestNoAction(Exception):
    pass


def update_release_notes(payload):
    PR_CLOSED = 'closed'
    DEFAULT_BRANCH = 'master'
    TAG_INITIAL = '0.0.1'
    TAG_PREFIX = 'v'
    RELEASE_NOTE_FORMAT = '* {message}. ({url})'

    # https://developer.github.com/v3/activity/events/types/#pullrequestevent
    try:
        action = payload['action']
        merged = payload['pull_request']['merged']
        url = payload['pull_request']['html_url']
        title = payload['pull_request']['title']
        base = payload['pull_request']['base']['ref']
    except KeyError:
        message = f'Unexpected webhook payload: {payload}'
        raise GithubRequestException(message)

    merged_into_default = action == PR_CLOSED and merged is True and base == DEFAULT_BRANCH
    if not merged_into_default:
        message = f'PR not merged into default branch: '\
                  f'action:{action}, merged:{merged}, base:{base}'
        raise GithubPullRequestNoAction(message)

    g = Github(GITHUB_ACCESS_TOKEN)
    repo = g.get_repo(GITHUB_REPO)
    releases = repo.get_releases()

    try:
        latest = releases[0]
    except IndexError:
        # must be the first release
        tag = f'{TAG_PREFIX}{TAG_INITIAL}'
        note = RELEASE_NOTE_FORMAT.format(message=title, url=url)
        repo.create_git_release(tag, tag, note, draft=True)

    return latest


def webhook_handler(request):
    try:
        GithubRequestValidator(GITHUB_WEBHOOK_SECRET).validate_webhook(request)
    except GithubRequestException as e:
        print(f'Webhook validation failed: {str(e)}')
        return '', 302

    payload = request.get_json()
    try:
        result = update_release_notes(payload)
    except GithubPullRequestNoAction as e:
        print(f'No action: {str(e)}')
        return '', 200
    except GithubRequestException as e:
        print(f'Failed to update release notes: {str(e)}')
        return '', 502

    print(result)
    return '', 200
