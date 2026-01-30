from setuptools import setup, find_packages

setup(
    name="tarea3",
    version="1.0.0",
    description="Gestión de reservas",
    author="cristian zola ndongala ndele nzinga",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PySide6"
    ],
    entry_points={
        "console_scripts": [
            "tarea3=tarea3.principal:main"
        ]
    },
)
