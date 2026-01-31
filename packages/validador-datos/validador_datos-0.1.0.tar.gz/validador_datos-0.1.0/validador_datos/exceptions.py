class ValidacionError(Exception):
    """Error base de validación"""

class EmailInvalidoError(ValidacionError):
    pass

class PasswordInvalidoError(ValidacionError):
    pass

