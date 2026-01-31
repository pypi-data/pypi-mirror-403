from setuptools import setup, find_packages

setup(
    name="shield_auth",
    version="1.1.0",
    description="Библиотека для безопасного хранения паролей в TXT",
    author="angyedz",
    url="https://github.com/angyedz/shield-auth",
    packages=find_packages(),
    install_requires=[
        "passlib>=1.7.4",
    ],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)