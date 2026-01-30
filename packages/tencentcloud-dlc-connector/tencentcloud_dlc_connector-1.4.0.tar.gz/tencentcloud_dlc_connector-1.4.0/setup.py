from setuptools import setup, find_packages
import os, io, re

NAME = "tencentcloud_dlc_connector"
DESCRIPTION = "Tencentcloud DLC connector, connect to DLC engines using SQL."
LONG_DESCRIPTION =open("README.rst").read()
LICENCE = "Apache License Version 2.0"
AUTHOR = "Tencentcloud DLC Team."
MAINTAINER_EMAIL = "dlc@tencent.com"
URL = "https://cloud.tencent.com/product/dlc"
DOWNLOAD_URL = "https://cloud.tencent.com/product/dlc"
PLATFORMS='any'



def read(path, encoding="utf-8"):
    path = os.path.join(os.path.dirname(__file__), path)
    with io.open(path, encoding=encoding) as fp:
        return fp.read()

def version(path):
    
    version_file = read(path)
    version_match = re.search(
        r"""^VERSION = ['"]([^'"]*)['"]""", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


VERSION = version("tdlc_connector/version.py")



setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    maintainer_email=MAINTAINER_EMAIL,
    packages=find_packages(exclude=["test*"]),
    platforms=PLATFORMS,
    license=LICENCE,
    install_requires=[
        "tencentcloud-sdk-python>=3.0.1257",
        "cos-python-sdk-v5>=1.9.20",
        "pyarrow>=8.0.0"
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
)

