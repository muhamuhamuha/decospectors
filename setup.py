from pathlib import Path
from setuptools import setup

HERE = Path(__file__).parent

README = (HERE / 'README.md').read_text()

setup(
    name='decospectors',
    version='1.1.0',
    description='Simplified function introspection inside decorators',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/muhamuhamuha/decospector',
    author='muhamuhamuha',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    packages=['decospectors'],
    include_package_data=True,
)
