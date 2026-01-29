from setuptools import setup,find_packages

setup(
    name="Tushar_Package_STT",
    version="1.1.3",
    author="Tushar Varshney",
    author_email="tusharvarshney620@gmail.com",
    description="A package for Speech-to-Text conversion using Selenium and a web-based STT helper, created by Tushar Varshney."
)

packages = find_packages(),

install_requirements=[
    "selenium",
    "webdriver-manager"
]

