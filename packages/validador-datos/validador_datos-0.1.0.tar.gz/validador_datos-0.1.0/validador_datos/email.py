import re
from .exceptions import EmailInvalidoError

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def validar_email(email: str) -> bool:
    email = email.strip().lower()
    if not re.match(EMAIL_REGEX, email):
        raise EmailInvalidoError(f"Email inválido: {email}")
    return email, True
