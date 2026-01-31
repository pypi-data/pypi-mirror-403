import pytest
from validador_datos import validar_email
from validador_datos.exceptions import EmailInvalidoError

def test_email_valido():
    assert validar_email("test@email.com") is True

def test_email_invalido():
    with pytest.raises(EmailInvalidoError):
        validar_email("correo-malo")

