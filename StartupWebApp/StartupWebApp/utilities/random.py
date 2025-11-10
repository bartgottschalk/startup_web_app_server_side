import string
from random import choice, randint


def getRandomString(min_char, max_char):
    #allchar = string.ascii_letters + string.punctuation + string.digits
    allchar = string.ascii_letters + string.digits
    random_string = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
    return random_string


def getRandomStringUpperDigit(min_char, max_char):
    #allchar = string.ascii_letters + string.punctuation + string.digits
    allchar = string.ascii_uppercase + string.digits
    random_string = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
    return random_string


def getRandomStringUpperLowerDigit(min_char, max_char):
    #allchar = string.ascii_letters + string.punctuation + string.digits
    allchar = string.ascii_uppercase + string.ascii_lowercase + string.digits
    random_string = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
    return random_string
