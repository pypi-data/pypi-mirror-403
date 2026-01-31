from setuptools import setup

DESCRIPTION = "API-Forwarder: Simplify API calls by sharing a base URL."
NAME = "API-Forwarder"
AUTHOR = "CrossDarkRix"
URL = "https://github.com/CrossDarkrix/API-Forwarder"
LICENSE = "MIT"
DOWNLOAD_URL = URL
VERSION = "2.0.1"
PYTHON_REQUIRES = ">=3.8"
INSTALL_REQUIRES = [
    "cloudscraper",
    "httpx"
]
PACKAGES = [
    "api_forwarder"
]
KEYWORDS = "api forwarder api-forwarder"
CLASSIFIERS=[
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.8"
]
with open('README.md', 'r', encoding='utf-8') as fp:
    readme = fp.read()
LONG_DESCRIPTION = readme
LONG_DESCRIPTION_CONTENT_TYPE = "text/markdown"

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    author=AUTHOR,
    maintainer=AUTHOR,
    url=URL,
    download_url=URL,
    packages=PACKAGES,
    classifiers=CLASSIFIERS,
    license=LICENSE,
    keywords=KEYWORDS,
    install_requires=INSTALL_REQUIRES
)