from setuptools import setup, find_packages

setup(
    name="bbae_invest_api",
    version="0.1.3",
    description="Unofficial BBAE Invest API written in Python Requests",
    url="https://github.com/ImNotOssy/BBAE_investing_API",
    author="Oswaldo Romero",
    packages=["bbae_invest_api"],
    install_requires=[
        "pillow",
        "python-dotenv",
        "requests",
    ],
)
