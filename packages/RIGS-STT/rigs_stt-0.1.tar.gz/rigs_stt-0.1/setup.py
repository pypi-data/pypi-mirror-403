from setuptools import setup, find_packages

setup(
    name='RIGS-STT',
    version='0.1',
    author='Rugved Kulkarni',
    author_email ="example@gmail.com",
    description='This is a speech to text package created by Rugved Kulkarni',
    packages=find_packages(),
    install_requires=[
        'selenium',
        'webdriver-manager',
    ]
)
