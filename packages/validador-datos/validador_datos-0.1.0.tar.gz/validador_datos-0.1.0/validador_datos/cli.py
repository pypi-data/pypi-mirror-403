import argparse
from . import validar_email, validar_password
from .exceptions import ValidacionError

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email")
    parser.add_argument("--password")
    args = parser.parse_args()

    try:
        if args.email:
            validar_email(args.email)
            print("✅ Email válido")

        if args.password:
            validar_password(args.password)
            print("✅ Password válido")

    except ValidacionError as e:
        print(f"❌ {e}")
        exit(1)

