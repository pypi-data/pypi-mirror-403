from setuptools import setup
from setuptools import find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

# Read version with fallback for encoding
version_path = os.path.join(here, 'restmapi', 'version.txt')
try:
    with open(version_path, 'r', encoding='utf-8') as f:
        version = f.read().strip()
except Exception:
    with open(version_path, 'r') as f:
        version = f.read().strip()

if not version:
    raise RuntimeError(f"Could not read version from {version_path}")

# Read README with utf-8 encoding
with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='restmapi',
    version=version,
    packages=find_packages(),
    description='MORPHEE REST API SDK',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Xavier Dourille',
    author_email='xavier.dourille@enorise.com',
    url='https://dev.azure.com/STS-Software/MORPHEE/_git/TOOLS-REST-MAPI?path=/Python',
    install_requires=[
        'requests>=2.25',
        'psutil>=5.9.8',
        'signalr-client>=0.0.7'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    package_data={"": ["version.txt"]},    
)