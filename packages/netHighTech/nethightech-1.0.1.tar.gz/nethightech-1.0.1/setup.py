from setuptools import setup, find_packages

setup(
    name='netHighTech',
    version='1.0.1', # Version barha do taake naya upload ho
    author='Zubair Khan',
    author_email='zubairdev00@gmail.com',
    description='A package for speech recognition using Selenium and WebDriver',
    packages=find_packages(), # Ye brackets ke andar hona chahiye
    include_package_data=True, # Ye lazmi hai HTML files ke liye
    install_requires=[
        'selenium',
        'webdriver-manager',
    ],
)