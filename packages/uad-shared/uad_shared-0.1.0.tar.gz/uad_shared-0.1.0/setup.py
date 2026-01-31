from setuptools import setup, find_packages

setup(
    name="uad-shared",
    version="0.1.0",
    description="Shared UAD models, enums, and core database utilities",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
    ],
)
