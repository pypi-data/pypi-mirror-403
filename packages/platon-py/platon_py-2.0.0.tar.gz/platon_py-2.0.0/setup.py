#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    find_packages,
    setup,
)

extras_require = {
    'tester': [
        "platon-tester[py-evm]>=1.2.0",
    ],
    'linter': [
        "flake8>=6.0.0",
        "isort>=5.0.0",
        "mypy>=1.0.0",
    ],
    'docs': [
        "mock",
        "sphinx-better-theme>=0.1.4",
        "click>=8.0",
        "pytest>=6.0.0",
        "sphinx>=4.0,<7",
        "sphinx_rtd_theme>=1.0.0",
        "towncrier>=22.0",
        "wheel",
    ],
    'dev': [
        "bumpversion",
        "flaky>=3.7.0",
        "hypothesis>=6.0.0",
        "pytest>=6.2.4,<7",
        "pytest-asyncio>=0.21.0",
        "pytest-mock>=3.0.0",
        "pytest-pythonpath>=0.3",
        "pytest-watch>=4.2.0",
        "pytest-xdist>=3.0.0",
        "setuptools>=65.6.3",
        "tox>=4.0.0",
        "tqdm>=4.60.0",
        "twine>=4.0.0",
        "when-changed>=0.3.0",
    ],
}

extras_require['dev'] = (
    extras_require['tester']
    + extras_require['linter']
    + extras_require['docs']
    + extras_require['dev']
)

with open('./README.md') as readme:
    long_description = readme.read()

setup(
    name='platon_py',
    # *IMPORTANT*: Don't manually change the version here. Use the 'bumpversion' utility.
    version='2.0.0',
    description="""platon.py""",
    long_description_content_type='text/markdown',
    long_description=long_description,
    author='ssdut.steven',
    author_email='ssdut.steven@gmail.com',
    url='https://github.com/PlatONNetwork/platon.py',
    include_package_data=True,
    install_requires=[
        "abi>=0.1.0,<0.2",
        "aiohttp>=3.8.1,<4",
        "attrdict>=2.0.1",
        "cache>=1.0.3",
        "client_sdk_python>=1.1.1",
        "eth_abi>=2.2.0,<3",
        "eth_account>=0.5.9,<0.6",
        "eth_typing>=2.3.0,<3",
        "eth_utils>=1.10.0,<2",
        "fixture>=1.5.11",
        "formatting>=0.0.1",
        "hexbytes>=0.2.1,<1",
        "idna>=3.3",
        "names>=0.3.0",
        "platon_typing>=1.2.0",
        "platon_utils>=1.2.1",
        "requests>=2.32.5,<3",
        "rlp>=1.2.0,<2",
        "signing>=3",
        "web3>=5.23.0,<6",
        "pywin32>=223;platform_system=='Windows'",
        "typing-extensions>=4.0.0;python_version<'3.8'",
    ],
    python_requires='>=3.6,<4',
    extras_require=extras_require,
    py_modules=[],
    entry_points={"pytest11": ["pytest_platon = platon.tools.pytest_platon.plugins"]},
    license="MIT",
    zip_safe=False,
    keywords='platon',
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"platon": ["py.typed"]},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
