import re

def validate_password(password):
    """
    Validates the password against the specified requirements.
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be a minimum of 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least 1 Uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least 1 lowercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain at least 1 number.")
    return errors