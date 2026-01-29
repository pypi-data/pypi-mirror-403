#!/usr/bin/env python
"""Setup script for tc-db-base package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / 'README.md'
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''

# Read version from package
version = '1.0.3'

setup(
    name='tc-db-base',
    version=version,
    author='Yashvanth D',
    author_email='dev@taskcircuit.com',
    description='Schema-driven MongoDB database module with auto-generated repositories',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/task-circuit/tc-db-base',
    project_urls={
        'Bug Tracker': 'https://github.com/task-circuit/tc-db-base/issues',
        'Documentation': 'https://github.com/task-circuit/tc-db-base#readme',
        'Source Code': 'https://github.com/task-circuit/tc-db-base',
    },
    license='MIT',

    packages=find_packages(include=['tc_db_base', 'tc_db_base.*']),

    python_requires='>=3.8',
    install_requires=[
        'pymongo>=4.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'flask': [
            'flask>=2.0.0',
            'flask-cors>=4.0.0',
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='mongodb, database, schema, repository, orm',

    entry_points={
        'console_scripts': [
            'tc-db-server=tc_db_base.server:main',
        ],
    },
)

