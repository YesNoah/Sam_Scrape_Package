from setuptools import setup, find_packages

setup(
    name='grant_scraper',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'selenium==3.141.0',
        'beautifulsoup4==4.9.3',
        'requests==2.26.0',
        'webdriver-manager==3.4.2',
    ],
)