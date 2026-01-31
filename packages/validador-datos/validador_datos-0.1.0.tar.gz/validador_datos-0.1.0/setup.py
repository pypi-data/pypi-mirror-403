from setuptools import setup, find_packages

# Leer el README.md para la descripción larga
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="validador-datos",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["regex"],  # Tu dependencia
    author="DogTheRc",
    author_email="skipper@a.com",  # Pon aquí tu email real
    description="Paquete para validar emails y passwords",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://tusitio-o-repositorio-aqui",  # Cambia por URL real o deja vacío
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)

