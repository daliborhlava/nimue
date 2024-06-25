import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.join(script_dir, "..")
sys.path.append(root_path)

import unittest

from ingestion.extractors import extract_mail_info_from_name_method1
from shared.constants import UNKNOWN_VALUE

class TestProcessFunction(unittest.TestCase):
    def test_valid_email_name(self):
        """Test with a valid email name format."""
        name = "1-3-2017__Jane doe_ _Jane.Doe@example.com__RE_ XXX XX - lorem ipsum"
        expected_output = {"from_email": "Jane.Doe@example.com".lower()}
        result = extract_mail_info_from_name_method1(name)
        self.assertEqual(result, expected_output)

    def test_invalid_email_name_no_email(self):
        """Test with an email name that doesn't contain a valid email address."""
        name = "1-3-2017__Jane doe_ _ RE_ XXX XX - lorem ipsum"
        expected_output = {"from_email": UNKNOWN_VALUE}
        result = extract_mail_info_from_name_method1(name)
        self.assertEqual(result, expected_output)

    def test_invalid_email_name_malformed_email(self):
        """Test with an email name that contains a malformed email address."""
        name = "1-3-2017__Jane doe_ _Jane.Doe@example__RE_ XXX XX - lorem ipsum"
        expected_output = {"from_email": UNKNOWN_VALUE}
        result = extract_mail_info_from_name_method1(name)
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()