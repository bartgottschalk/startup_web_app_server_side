# Unit tests for form validators
# Tests validation functions used throughout the application

from django.test import TestCase
from StartupWebApp.utilities.test_base import PostgreSQLTestCase
from django.contrib.auth.models import User

from StartupWebApp.form import validator


class EmailValidationTests(PostgreSQLTestCase):
    """Tests for email validation functions"""

    def test_isEmail_valid_formats(self):
        """Test that valid email formats are accepted"""
        valid_emails = [
            'user@example.com',
            'test.user@example.com',
            'user+tag@example.com',
            'user_name@example.com',
            'user-name@example.com',
            'user123@example.com',
            '123@example.com',
            'a@b.co',
            'test@subdomain.example.com',
        ]
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(
                    validator.isEmail(email),
                    f'Expected {email} to be valid'
                )

    def test_isEmail_invalid_formats(self):
        """Test that invalid email formats are rejected"""
        invalid_emails = [
            '',  # empty
            'notanemail',  # no @
            '@example.com',  # no local part
            'user@',  # no domain
            'user @example.com',  # space in local part
            'user@example',  # no TLD
            'user@.com',  # no domain name
            'user@@example.com',  # double @
            'user@example..com',  # double period
            'user.@example.com',  # trailing period
            '.user@example.com',  # leading period
        ]
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(
                    validator.isEmail(email),
                    f'Expected {email} to be invalid'
                )

    def test_isEmailValid_with_valid_email(self):
        """Test isEmailValid with valid email and length"""
        result = validator.isEmailValid('test@example.com', 254)
        self.assertTrue(result)

    def test_isEmailValid_empty_required(self):
        """Test that empty email returns required error"""
        result = validator.isEmailValid('', 254)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'required')

    def test_isEmailValid_invalid_format(self):
        """Test that invalid email format returns not_valid error"""
        result = validator.isEmailValid('notanemail', 254)
        self.assertIsInstance(result, list)
        self.assertIn('not_valid', [e['type'] for e in result])

    def test_isEmailValid_too_long(self):
        """Test that email exceeding max length returns error"""
        long_email = 'a' * 250 + '@example.com'
        result = validator.isEmailValid(long_email, 254)
        self.assertIsInstance(result, list)
        self.assertIn('too_many_chars', [e['type'] for e in result])


class PasswordValidationTests(PostgreSQLTestCase):
    """Tests for password validation - SECURITY CRITICAL"""

    def test_isPasswordValid_meets_all_requirements(self):
        """Test that valid password meeting all requirements returns True"""
        result = validator.isPasswordValid('SecurePass1!', 'SecurePass1!', 150)
        self.assertTrue(result)

    def test_isPasswordValid_empty_required(self):
        """Test that empty password returns required error"""
        result = validator.isPasswordValid('', '', 150)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'required')

    def test_isPasswordValid_too_short(self):
        """Test that password under 8 characters returns too_short error"""
        result = validator.isPasswordValid('Short1!', 'Short1!', 150)
        self.assertIsInstance(result, list)
        self.assertIn('too_short', [e['type'] for e in result])

    def test_isPasswordValid_too_long(self):
        """Test that password exceeding max length returns error"""
        long_password = 'A' * 151 + 'a1!'
        result = validator.isPasswordValid(long_password, long_password, 150)
        self.assertIsInstance(result, list)
        self.assertIn('too_many_chars', [e['type'] for e in result])

    def test_isPasswordValid_no_capital_letter(self):
        """Test that password without capital letter returns error"""
        result = validator.isPasswordValid('lowercase1!', 'lowercase1!', 150)
        self.assertIsInstance(result, list)
        self.assertIn('no_capital_letter', [e['type'] for e in result])

    def test_isPasswordValid_no_special_character(self):
        """Test that password without special character returns error"""
        result = validator.isPasswordValid('NoSpecial1', 'NoSpecial1', 150)
        self.assertIsInstance(result, list)
        self.assertIn('no_special_character', [e['type'] for e in result])

    def test_isPasswordValid_passwords_dont_match(self):
        """Test that mismatched passwords return error"""
        result = validator.isPasswordValid('SecurePass1!', 'DifferentPass1!', 150)
        self.assertIsInstance(result, list)
        self.assertIn('confirm_password_doesnt_match', [e['type'] for e in result])

    def test_isPasswordValid_multiple_errors(self):
        """Test that multiple validation errors are returned"""
        # Too short, no capital, no special char
        result = validator.isPasswordValid('short', 'short', 150)
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 3)
        error_types = [e['type'] for e in result]
        self.assertIn('too_short', error_types)
        self.assertIn('no_capital_letter', error_types)
        self.assertIn('no_special_character', error_types)

    def test_containsCapitalLetter_with_capital(self):
        """Test that strings with capital letters are detected"""
        self.assertTrue(validator.containsCapitalLetter('HelloWorld'))
        self.assertTrue(validator.containsCapitalLetter('helloWorld'))
        self.assertTrue(validator.containsCapitalLetter('A'))
        self.assertTrue(validator.containsCapitalLetter('aBc'))

    def test_containsCapitalLetter_without_capital(self):
        """Test that strings without capital letters are detected"""
        self.assertFalse(validator.containsCapitalLetter('helloworld'))
        self.assertFalse(validator.containsCapitalLetter('123456'))
        self.assertFalse(validator.containsCapitalLetter('!!!@@@'))
        self.assertFalse(validator.containsCapitalLetter(''))

    def test_containsSpecialCharacter_with_special(self):
        """Test that strings with special characters are detected"""
        special_chars = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '~', '{', '}', '[', ']']
        for char in special_chars:
            with self.subTest(char=char):
                self.assertTrue(
                    validator.containsSpecialCharacter(f'password{char}'),
                    f'Expected {char} to be detected as special character'
                )

    def test_containsSpecialCharacter_without_special(self):
        """Test that strings without special characters are detected"""
        self.assertFalse(validator.containsSpecialCharacter('Password123'))
        self.assertFalse(validator.containsSpecialCharacter('OnlyLetters'))
        self.assertFalse(validator.containsSpecialCharacter('12345'))
        self.assertFalse(validator.containsSpecialCharacter(''))


class UsernameValidationTests(PostgreSQLTestCase):
    """Tests for username validation"""

    def setUp(self):
        """Create a test user for username availability tests"""
        User.objects.create_user('existinguser', 'test@example.com', 'password')

    def test_isUserNameValid_valid_username(self):
        """Test that valid available username returns True"""
        result = validator.isUserNameValid('newuser123', 150)
        self.assertTrue(result)

    def test_isUserNameValid_empty_required(self):
        """Test that empty username returns required error"""
        result = validator.isUserNameValid('', 150)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'required')

    def test_isUserNameValid_too_short(self):
        """Test that username under 6 characters returns error"""
        result = validator.isUserNameValid('short', 150)
        self.assertIsInstance(result, list)
        self.assertIn('too_short', [e['type'] for e in result])

    def test_isUserNameValid_too_long(self):
        """Test that username exceeding max length returns error"""
        long_username = 'a' * 151
        result = validator.isUserNameValid(long_username, 150)
        self.assertIsInstance(result, list)
        self.assertIn('too_many_chars', [e['type'] for e in result])

    def test_isUserNameValid_invalid_characters(self):
        """Test that username with invalid characters returns error"""
        invalid_usernames = [
            'user name',  # space
            'user@name',  # @
            'user.name',  # period
            'user!name',  # exclamation
        ]
        for username in invalid_usernames:
            with self.subTest(username=username):
                result = validator.isUserNameValid(username, 150)
                self.assertIsInstance(result, list)
                self.assertIn('not_valid', [e['type'] for e in result])

    def test_isUserNameValid_unavailable_username(self):
        """Test that existing username returns unavailable error"""
        result = validator.isUserNameValid('existinguser', 150)
        self.assertIsInstance(result, list)
        self.assertIn('unavailable', [e['type'] for e in result])

    def test_isUserNameAvailable_available(self):
        """Test that non-existent username is available"""
        self.assertTrue(validator.isUserNameAvailable('newuser'))

    def test_isUserNameAvailable_unavailable(self):
        """Test that existing username is unavailable"""
        self.assertFalse(validator.isUserNameAvailable('existinguser'))

    def test_isAlphaNumericUnderscoreHyphen_valid(self):
        """Test that valid username characters are accepted"""
        valid_strings = [
            'username',
            'user_name',
            'user-name',
            'user123',
            'user_name-123',
            '123',
            '_',
            '-',
        ]
        for string in valid_strings:
            with self.subTest(string=string):
                self.assertTrue(validator.isAlphaNumericUnderscoreHyphen(string))

    def test_isAlphaNumericUnderscoreHyphen_invalid(self):
        """Test that invalid username characters are rejected"""
        invalid_strings = [
            'user name',  # space
            'user@name',  # @
            'user.name',  # period
            'user!name',  # exclamation
            'user#name',  # hash
        ]
        for string in invalid_strings:
            with self.subTest(string=string):
                self.assertFalse(validator.isAlphaNumericUnderscoreHyphen(string))


class NameValidationTests(PostgreSQLTestCase):
    """Tests for name field validation"""

    def test_isNameValid_valid_name(self):
        """Test that valid name returns True"""
        result = validator.isNameValid('John Doe', 200)
        self.assertTrue(result)

    def test_isNameValid_empty_required(self):
        """Test that empty name returns required error"""
        result = validator.isNameValid('', 200)
        self.assertIsInstance(result, list)
        self.assertIn('required', [e['type'] for e in result])

    def test_isNameValid_too_long(self):
        """Test that name exceeding max length returns error"""
        long_name = 'a' * 201
        result = validator.isNameValid(long_name, 200)
        self.assertIsInstance(result, list)
        self.assertIn('too_many_chars', [e['type'] for e in result])

    def test_isNameValid_invalid_characters(self):
        """Test that name with invalid characters returns error"""
        result = validator.isNameValid('John@Doe', 200)
        self.assertIsInstance(result, list)
        self.assertIn('not_valid', [e['type'] for e in result])

    def test_isAlphaNumericSpace_valid(self):
        """Test that alphanumeric and spaces are accepted"""
        valid_strings = [
            'John Doe',
            'John123',
            'ABC 123',
            'test',
            '123',
            '',  # empty is technically valid for this function
        ]
        for string in valid_strings:
            with self.subTest(string=string):
                self.assertTrue(validator.isAlphaNumericSpace(string))

    def test_isAlphaNumericSpace_invalid(self):
        """Test that special characters and symbols are rejected"""
        invalid_strings = [
            'John@Doe',
            'John_Doe',
            'John-Doe',
            'John.Doe',
            'John!',
        ]
        for string in invalid_strings:
            with self.subTest(string=string):
                self.assertFalse(validator.isAlphaNumericSpace(string))

    def test_isAlphaNumericSpaceAmpersand_valid(self):
        """Test that alphanumeric, spaces, and ampersands are accepted"""
        valid_strings = [
            'Johnson & Johnson',
            'A&B',
            'Test & Test',
            'Regular Name',
        ]
        for string in valid_strings:
            with self.subTest(string=string):
                self.assertTrue(validator.isAlphaNumericSpaceAmpersand(string))

    def test_isAlphaNumericSpaceAmpersand_invalid(self):
        """Test that other special characters are rejected"""
        invalid_strings = [
            'Johnson@Test',
            'Test_Test',
            'Test-Test',
        ]
        for string in invalid_strings:
            with self.subTest(string=string):
                self.assertFalse(validator.isAlphaNumericSpaceAmpersand(string))


class IntegerRangeValidationTests(PostgreSQLTestCase):
    """Tests for integer range validation"""

    def test_isIntegerInRange_valid_integers(self):
        """Test that integers in range return True"""
        self.assertTrue(validator.isIntegerInRange('5', 0, 10))
        self.assertTrue(validator.isIntegerInRange('0', 0, 10))
        self.assertTrue(validator.isIntegerInRange('10', 0, 10))
        self.assertTrue(validator.isIntegerInRange(5, 0, 10))

    def test_isIntegerInRange_out_of_range(self):
        """Test that integers out of range return error"""
        result = validator.isIntegerInRange('11', 0, 10)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['type'], 'out_of_range')

        result = validator.isIntegerInRange('-1', 0, 10)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['type'], 'out_of_range')

    def test_isIntegerInRange_not_an_integer(self):
        """Test that non-integer values return error"""
        result = validator.isIntegerInRange('abc', 0, 10)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['type'], 'not_an_int')

        result = validator.isIntegerInRange('1.5', 0, 10)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['type'], 'not_an_int')


class SkuQuantityValidationTests(PostgreSQLTestCase):
    """Tests for SKU quantity validation"""

    def test_validateSkuQuantity_valid(self):
        """Test that valid quantities return True"""
        self.assertTrue(validator.validateSkuQuantity('1'))
        self.assertTrue(validator.validateSkuQuantity('50'))
        self.assertTrue(validator.validateSkuQuantity('99'))
        self.assertTrue(validator.validateSkuQuantity('0'))

    def test_validateSkuQuantity_out_of_range(self):
        """Test that quantities out of range return error"""
        result = validator.validateSkuQuantity('100')
        self.assertIsInstance(result, list)
        # Should contain nested list with out_of_range error
        self.assertTrue(len(result) > 0)

        result = validator.validateSkuQuantity('-1')
        self.assertIsInstance(result, list)

    def test_validateSkuQuantity_not_integer(self):
        """Test that non-integer quantities return error"""
        result = validator.validateSkuQuantity('abc')
        self.assertIsInstance(result, list)

        result = validator.validateSkuQuantity('1.5')
        self.assertIsInstance(result, list)


class ChatMessageValidationTests(PostgreSQLTestCase):
    """Tests for chat message validation"""

    def test_isChatMessageValid_valid_message(self):
        """Test that valid message returns True"""
        result = validator.isChatMessageValid('Hello, I need help!', 5000)
        self.assertTrue(result)

    def test_isChatMessageValid_empty_required(self):
        """Test that empty message returns required error"""
        result = validator.isChatMessageValid('', 5000)
        self.assertIsInstance(result, list)
        self.assertIn('required', [e['type'] for e in result])

    def test_isChatMessageValid_too_long(self):
        """Test that message exceeding max length returns error"""
        long_message = 'a' * 5001
        result = validator.isChatMessageValid(long_message, 5000)
        self.assertIsInstance(result, list)
        self.assertIn('too_many_chars', [e['type'] for e in result])


class HowExcitedValidationTests(PostgreSQLTestCase):
    """Tests for excitement rating validation"""

    def test_isHowExcitedValid_valid_ratings(self):
        """Test that valid ratings return True"""
        valid_ratings = ['1', '2', '3', '4', '5']
        for rating in valid_ratings:
            with self.subTest(rating=rating):
                result = validator.isHowExcitedValid(rating)
                self.assertTrue(result)

    def test_isHowExcitedValid_empty_required(self):
        """Test that empty rating returns required error"""
        result = validator.isHowExcitedValid('')
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['type'], 'required')

    def test_isHowExcitedValid_out_of_range(self):
        """Test that rating out of range returns error"""
        invalid_ratings = ['0', '6', '10', '-1']
        for rating in invalid_ratings:
            with self.subTest(rating=rating):
                result = validator.isHowExcitedValid(rating)
                self.assertIsInstance(result, list)
                self.assertIn('out_of_range', [e['type'] for e in result])

    def test_isHowExcitedValid_non_numeric(self):
        """Test that non-numeric rating returns error"""
        result = validator.isHowExcitedValid('abc')
        self.assertIsInstance(result, list)
        self.assertIn('out_of_range', [e['type'] for e in result])


class ErrorMessageTests(PostgreSQLTestCase):
    """Tests to verify error message structure and content"""

    def test_error_messages_have_required_fields(self):
        """Test that all error constants have type and description"""
        errors = [
            validator.required_error,
            validator.not_valid_email,
            validator.not_valid_name,
            validator.too_many_chars,
            validator.not_valid_username,
            validator.username_too_short,
            validator.username_unavailable,
            validator.password_too_short,
            validator.password_must_contain_capital_letter,
            validator.password_must_contain_special_character,
            validator.confirm_password_doesnt_match,
            validator.out_of_range,
            validator.not_an_int,
        ]

        for error in errors:
            with self.subTest(error=error):
                self.assertIn('type', error)
                self.assertIn('description', error)
                self.assertIsInstance(error['type'], str)
                self.assertIsInstance(error['description'], str)
                self.assertTrue(len(error['type']) > 0)
                self.assertTrue(len(error['description']) > 0)
