"""
SheetSandbox SDK - Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path
import codecs
import os


# Read the README file
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name="sheetsandbox",
    version="1.0.2",
    author="Aravind Kumar Vemula",
    author_email="30lmas09@gmail.com",
    description="Turn Google Sheets into your production-ready database for MVPs. Plan-based features for Free and Pro users.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sheetsandbox/sheetsandbox-pip",
    project_urls={
        "Bug Tracker": "https://github.com/sheetsandbox/sheetsandbox-pip/issues",
        "Documentation": "https://sheetsandbox.com/docs",
        "Source Code": "https://github.com/sheetsandbox/sheetsandbox-pip",
        "Homepage": "https://sheetsandbox.com",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    keywords=[
        "google-sheets",
        "api",
        "database",
        "mvp",
        "no-backend",
        "sheetsandbox",
        "spreadsheet",
        "forms",
        "waitlist",
        "feedback"
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
