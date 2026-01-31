import re
from .exceptions import PasswordInvalidoError

def validar_password(password:str) -> bool:
    reglas = [
            (len(password) >= 8, "minimo 8 caracteres" ),
            (re.search(r"[A-Z]", password), "Debe tener Mayuscula"),
            (re.search(r"\d",password),"Debe tener un digito"),
            (re.search(r"[^\w\s]",password),"Un simbolo"),
    ]
    
    errores = [msg for ok, msg in reglas if not ok]

    if errores:
        raise PasswordInvalidoError(
            "Password inválido, falta: " + ", ".join(errores)
        )

    return True
    
