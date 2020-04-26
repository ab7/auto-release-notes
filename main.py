import os
import base64

import semver
from github import Github
from google.cloud import kms

from github_auto_release_notes.validation import GithubRequestValidator
from github_auto_release_notes.exceptions import (
    GithubRequestException,
    GithubPullRequestNoAction,
)


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
        body = RELEASE_NOTE_FORMAT.format(message=title, url=url)
        repo.create_git_release(tag, tag, body, draft=True)

    if latest.draft is True:
        new_note = RELEASE_NOTE_FORMAT.format(message=title, url=url)
        new_notes = f'{latest.body}\n{new_note}'
        latest.update_release(latest.title, new_notes, draft=True)
    else:
        tag = latest.tag_name.replace(TAG_PREFIX, '')
        new_tag = f'{TAG_PREFIX}{str(semver.parse_version_info(tag).bump_patch())}'
        body = RELEASE_NOTE_FORMAT.format(message=title, url=url)
        repo.create_git_release(new_tag, new_tag, body, draft=True)

    return latest


def webhook_handler(request):
    try:
        GithubRequestValidator(GITHUB_WEBHOOK_SECRET).validate_webhook(request)
    except GithubRequestException as e:
        print(f'Webhook validation failed: {str(e)}')
        return '', 302

    payload = request.get_json()
    try:
        update_release_notes(payload)
    except GithubPullRequestNoAction as e:
        print(f'No action: {str(e)}')
        return '', 200
    except GithubRequestException as e:
        print(f'Failed to update release notes: {str(e)}')
        return '', 502

    return '', 200
