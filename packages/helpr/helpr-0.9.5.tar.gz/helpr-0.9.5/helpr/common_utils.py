import phonenumbers
import re


def validate_mobile(mobile):
    if not mobile or not mobile.startswith('+') or not mobile[1:].isdigit():
        return False
    try:
        x = phonenumbers.parse(mobile, 'IN')  # Default region sets to 'IN'
        if not phonenumbers.is_valid_number_for_region(x,'IN'):
            return False 
    except phonenumbers.phonenumberutil.NumberParseException:
        return False
    return True

def validate_email(email)->bool:
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False
 