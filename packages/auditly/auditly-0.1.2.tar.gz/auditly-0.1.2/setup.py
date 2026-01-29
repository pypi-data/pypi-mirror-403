# setup.py
from setuptools import setup, find_packages

setup(
    name="auditly",
    version="0.1.2",
    author="Krishna Tadi",
    description="Auditly is a next-generation Python dependency vulnerability scanner that helps developers identify security risks in installed packages and requirements.txt files, providing clear severity levels and fix recommendations.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/krishnatadi/auditly-pypi",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "auditly=auditly.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
    ],
    project_urls={
        "Bug Tracker": "https://github.com/krishnatadi/auditly-pypi/issues",
        "Source Code": "https://github.com/krishnatadi/auditly-pypi",
    },
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "tqdm>=4.64.0"
    ],
)
