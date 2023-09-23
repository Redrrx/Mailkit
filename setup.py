from setuptools import setup, find_packages

setup(
    name='MailKit',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'annotated-types==0.5.0',
        'colorama==0.4.6',
        'colorlog==6.7.0',
        'imap-tools==1.2.0',
        'pydantic==2.3.0',
        'pydantic_core==2.6.3',
        'tenacity==8.2.3',
        'typing_extensions==4.8.0',
    ],
    author='Y.S',
    description='a python package for email scraping and checking.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Redrrx/MailKit',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
