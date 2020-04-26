import unittest

from github_auto_release_notes.exceptions import (
    GithubRequestException,
    GithubPullRequestNoAction
)


class TestGithubRequestException(unittest.TestCase):

    def test_github_request_exception(self):
        expected_message = 'test'
        with self.assertRaises(GithubRequestException) as cm:
            raise GithubRequestException(expected_message)
        self.assertEqual(str(cm.exception), expected_message)


class TestGithubPullRequestNoAction(unittest.TestCase):

    def test_github_pull_request_no_action(self):
        expected_message = 'test'
        with self.assertRaises(GithubPullRequestNoAction) as cm:
            raise GithubPullRequestNoAction(expected_message)
        self.assertEqual(str(cm.exception), expected_message)
