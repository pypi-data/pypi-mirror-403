from setuptools import setup,find_packages

setup(
    name='Jignesh-STT',
    version='0.1',
    author='Jignesh',
    author_email='kumarjignesh506@gmail.com',
    description='This is Speech to text package created by Jignesh'
)

packages = find_packages(),

install_requirement = [
    'selenium',
    'webdriver_manager',
]
