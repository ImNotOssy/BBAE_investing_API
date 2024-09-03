from setuptools import setup, find_packages

setup(
    name="bbae_invest_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "python-dotenv",
        "requests",
    ],
)
