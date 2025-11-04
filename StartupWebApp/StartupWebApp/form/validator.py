import re
from django.contrib.auth.models import User

def isEmail(email):
    # Email regex: local-part @ domain
    # Local part: must start and end with alphanumeric, can contain . _ + - in middle
    # Domain: standard domain format with TLD
    if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9_.+-]*[a-zA-Z0-9])?\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$", email):
        return True
    else:
        return False

def isIntegerInRange(integer_in, min_value, max_value):
    errors = []
    try:
        if int(integer_in) >= min_value and int(integer_in) <= max_value: 
            return True
        else:
            errors.append(out_of_range)
            return errors
    except ValueError as e:
        print(e)
        errors.append(not_an_int)
        return errors

def isAlphaNumericSpace(string_val):
    if re.match("^[A-Za-z0-9 ]*$", string_val):	
        return True
    else:
        return False

def isAlphaNumericSpaceAmpersand(string_val):
    if re.match("^[&A-Za-z0-9 ]*$", string_val): 
        return True
    else:
        return False

def isAlphaNumericUnderscoreHyphen(string_val):
    if re.match("^[a-zA-Z0-9_-]*$", string_val):	
        return True
    else:
        return False

def containsCapitalLetter(string_val):
    if re.match(".*[A-Z].*", string_val):	
        return True
    else:
        return False

def containsSpecialCharacter(string_val):
    if re.match(r".*[!@#$%^&*()~{}\[\]].*", string_val):
        return True
    else:
        return False

def isUserNameAvailable(username):
    try:
        user = User.objects.get(username=username)
        return False
    except User.DoesNotExist:
        return True

def isNameValid(name, max_length):
    #print('isNameValid called')
    errors = [];
    if name == '':
        errors.append(required_error)
    if isAlphaNumericSpace(name) != True:
        errors.append(not_valid_name)
    if len(name) > max_length:
        errors.append(too_many_chars)
    if len(errors) > 0: 
        return errors
    else:
    	return True

def isUserNameValid(username, max_length):
    errors = [];
    if username == '':
        errors.append(required_error)
        return errors
    if isAlphaNumericUnderscoreHyphen(username) != True:
        errors.append(not_valid_username)
    if len(username) > max_length:
        errors.append(too_many_chars)
    if len(username) >= 1 and len(username) < 6:
        errors.append(username_too_short)
    if isUserNameAvailable(username) == False:
        errors.append(username_unavailable)
    if len(errors) > 0: 
        return errors
    else:
    	return True

def isEmailValid(email, max_length):
    errors = []
    if email == '':
        errors.append(required_error)
        return errors
    if isEmail(email) != True:
        errors.append(not_valid_email);
    if len(email) > max_length:
        errors.append(too_many_chars)
    if len(errors) > 0: 
        return errors
    else:
    	return True

def isPasswordValid(password, confirm_password, max_length):
    errors = []
    if password == '':
        errors.append(required_error)
        return errors
    if len(password) > max_length:
        errors.append(too_many_chars)
    if len(password) >= 1 and len(password) < 8:
        errors.append(password_too_short)
    if containsCapitalLetter(password) != True:
        errors.append(password_must_contain_capital_letter)
    if containsSpecialCharacter(password) != True:
        errors.append(password_must_contain_special_character)
    if password != confirm_password:
        errors.append(confirm_password_doesnt_match)
    if len(errors) > 0: 
        return errors
    else:
    	return True

def validateSkuQuantity(quantity):
    errors = []
    isQuantityInRange = isIntegerInRange(quantity, 0, 99)
    if isQuantityInRange is not True:
        errors.append(isQuantityInRange)
    if errors != []:
        return errors
    return True

def isChatMessageValid(message, max_length):
    #print('isNameValid called')
    errors = [];
    if message == '':
        errors.append(required_error)
    if len(message) > max_length:
        errors.append(too_many_chars)
    if len(errors) > 0: 
        return errors
    else:
        return True

def isHowExcitedValid(how_excited):
    errors = []
    if how_excited == '':
        errors.append(required_error)
        return errors
    if str(how_excited) not in ['1', '2', '3', '4', '5']:
        errors.append(out_of_range)
    if len(errors) > 0: 
        return errors
    else:
        return True

required_error = {'type': 'required','description': 'This is a required field.'};
not_valid_email = {'type': 'not_valid','description': 'Please enter a valid email address. For example johndoe@domain.com.'};
not_valid_name = {'type': 'not_valid','description': 'Please enter a valid name. Characters, numbers, and spaces are allowed.'};
too_many_chars = {'type': 'too_many_chars','description': 'The value you entered is too long for this field.'};
not_valid_username = {'type': 'not_valid','description': 'Please enter a valid username. Characters, numbers, underscore ("_"), and hyphens ("-") are allowed.'};
username_too_short = {'type': 'too_short','description': 'The username you entered is too short. Usernames must be between 6 and 150 characters in length.'};
username_unavailable = {'type': 'unavailable','description': 'The username you entered is unavailable. Please enter a different username and try again.'};
password_too_short = {'type': 'too_short','description': 'The password you entered is too short. Passwords must be between 8 and 150 characters in length.'};
password_must_contain_capital_letter = {'type': 'no_capital_letter','description': 'Passwords must contain at least one capital letter.'};
password_must_contain_special_character = {'type': 'no_special_character','description': 'Passwords must contain at least one special character.'};
confirm_password_doesnt_match = {'type': 'confirm_password_doesnt_match','description': 'Please make sure your passwords match.'};
out_of_range = {'type': 'out_of_range','description': 'The value provided is out of range.'};
not_an_int = {'type': 'not_an_int','description': 'The value provided is not an integer.'};