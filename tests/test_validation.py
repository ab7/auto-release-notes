import unittest
from unittest.mock import MagicMock

from github_auto_release_notes.validation import GithubRequestValidator
from github_auto_release_notes.exceptions import GithubRequestException


class TestGithubRequestValidator(unittest.TestCase):

    GITHUB_WEBHOOK_SECRET = 'secret'
    DATA = {"test": "data"}
    RAW_DATA = bytes(str(DATA), 'utf-8')
    VALID_SIGNATURE = 'sha1=e12c95dc17e8b0ebe3a581a19eb18195cfb5e9bb'
    BAD_FORMAT_SIGNATURE = 'e12c95dc17e8b0ebe3a581a19eb18195cfb5e9bb'
    INVALID_SIGNATURE = 'sha1=5a19eb18195cfb5e9bbb0ebe39eb18117e8b0eb5e'
    VALID_REQUEST = MagicMock(
        method='POST',
        headers={'X-Hub-Signature': VALID_SIGNATURE},
        get_data=MagicMock(return_value=RAW_DATA)
    )
    BAD_FORMAT_REQUEST = MagicMock(
        method='POST',
        headers={'X-Hub-Signature': BAD_FORMAT_SIGNATURE},
        get_data=MagicMock(return_value=RAW_DATA)
    )
    NO_HEADER_REQUEST = MagicMock(
        method='POST',
        headers={},
        get_data=MagicMock(return_value=RAW_DATA)
    )
    INVALID_REQUEST = MagicMock(
        method='POST',
        headers={'X-Hub-Signature': INVALID_SIGNATURE},
        get_data=MagicMock(return_value=RAW_DATA)
    )

    def test_check_method_is_valid(self):
        result = GithubRequestValidator._check_method('POST')
        self.assertEqual(result, None)

    def test_check_method_raises_method_error(self):
        with self.assertRaises(GithubRequestException) as cm:
            GithubRequestValidator._check_method('GET')
        expected_message = 'Method not allowed: GET'
        self.assertEqual(str(cm.exception), expected_message)

    def test_check_signature_valid(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        result = validator._check_signature(self.VALID_SIGNATURE, self.RAW_DATA)
        self.assertEqual(result, None)

    def test_check_signature_raises_unexpected_error(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator._check_signature(self.BAD_FORMAT_SIGNATURE, self.RAW_DATA)
        expected_message = f'Unexpected signature format: {self.BAD_FORMAT_SIGNATURE}'
        self.assertEqual(str(cm.exception), expected_message)

    def test_check_signature_with_missing_header(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator._check_signature('', self.RAW_DATA)
        expected_message = 'Unexpected signature format: '
        self.assertEqual(str(cm.exception), expected_message)

    def test_check_signature_with_invalid_signature(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator._check_signature(self.INVALID_SIGNATURE, self.RAW_DATA)
        expected_message = f'Invalid signature: {self.INVALID_SIGNATURE}'
        self.assertEqual(str(cm.exception), expected_message)

    def test_validate_webhook_valid(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        result = validator.validate_webhook(self.VALID_REQUEST)
        self.assertEqual(result, None)

    def test_validate_webhook_raises_unexpected_error(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator.validate_webhook(self.BAD_FORMAT_REQUEST)
        expected_message = f'Unexpected signature format: {self.BAD_FORMAT_SIGNATURE}'
        self.assertEqual(str(cm.exception), expected_message)

    def test_validate_webhook_with_missing_header(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator.validate_webhook(self.NO_HEADER_REQUEST)
        expected_message = 'Unexpected signature format: '
        self.assertEqual(str(cm.exception), expected_message)

    def test_validate_webhook_with_invalid_signature(self):
        validator = GithubRequestValidator(self.GITHUB_WEBHOOK_SECRET)
        with self.assertRaises(GithubRequestException) as cm:
            validator.validate_webhook(self.INVALID_REQUEST)
        expected_message = f'Invalid signature: {self.INVALID_SIGNATURE}'
        self.assertEqual(str(cm.exception), expected_message)
