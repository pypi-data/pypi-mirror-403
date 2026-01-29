from setuptools import setup, find_packages

setup(
    name="opportunity-core",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "tweepy>=4.14.0",
        "pydantic>=2.12.4",
        "pydantic-settings>=2.12.0",
        "python-telegram-bot>=22.5",
        "six>=1.16.0",
        "urllib3>=1.26.0",  # paapi5_python_sdk requires urllib3 v1.x but works with 2.x
        "certifi>=2023.7.22",
        "python-dateutil>=2.9.0",
    ],
    python_requires=">=3.11",
    description="Core library for Opportunity Radar - Shared utilities and services",
    author="Mustafa Aykon",
)
