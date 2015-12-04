from setuptools import find_packages
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

    packages=find_packages('.'),
    install_requires=[
        'lxml',
        'tinycss2'
    ],
    entry_points={
        'console_scripts': [
            'detect_missing_css_classes = pre_commit_hooks.detect_missing_css_classes:main',
            'forbid_crlf = pre_commit_hooks.forbid_crlf:main',
            'forbid_html_img_without_alt_text = pre_commit_hooks.forbid_html_img_without_alt_text:main',
            'forbid_non_std_html_attributes = pre_commit_hooks.forbid_non_std_html_attributes:main',
            'forbid_tabs = pre_commit_hooks.forbid_tabs:main',
            'remove_crlf = pre_commit_hooks.remove_crlf:main',
            'remove_tabs = pre_commit_hooks.remove_tabs:main',
        ],
    },
)
