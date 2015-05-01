from setuptools import setup

setup(
    name='pre-commit-hooks',
    description='Some out-of-the-box hooks for pre-commit',
    url='https://github.com/Lucas-C/pre-commit-hooks',
    version='0.0.1',

    author='Lucas Cimon',
    author_email='lucas.cimon@gmail.com',

    platforms='linux',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    entry_points={
        'console_scripts': [
            'forbid_crlf = forbid_crlf:main',
        ],
    },
)
