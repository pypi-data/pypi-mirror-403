from setuptools import setup, find_packages
from metadata import( __author__,
                    __author_email__,
                    __description__,
                    __github__
                    )   

with open("README.md", "r") as f:
    read_document = f.read()

setup(
    name='vikas_pg',
    version='0.2.1',
    python_requires=">=3.8,<3.14",
    packages=find_packages(),

    install_requires=[
    "async-lru>=2.1.0",
    "asyncpg>=0.29.0",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.7,<3.0",
    "pydantic-settings>=2.0,<3.0",
    ],
    
    entry_points={
        "console_scripts": [
            "vikas_pg = vikas_pg:Accelerate",
        ],
    },
    
    author=__author__,
    author_email=__author_email__,
    url=__github__,
    description=__description__,

    long_description=read_document,
    long_description_content_type="text/markdown",
)

