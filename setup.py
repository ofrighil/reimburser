from setuptools import find_packages, setup

NAME = 'reimburser'
VERSION = '0.1.0'
AUTHOR = 'emof'
URL = 'https://github.com/emof/reimburser'
DESCRIPTION = 'WRITE THIS'

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

with open('LICENSE') as f:
    LICENSE = f.read()

REQUIRES = [
    'numpy>=1.16.3',
    'pandas>=0.24.2',
]

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    url=URL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    license=LICENSE,
    python_requires='>=3.7.3',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=REQUIRES,
    #classifiers=,
    #entry_points=,
)
