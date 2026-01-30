import os
import io
import setuptools


name = "tmg-data"
description = "TMG data library"

version = "0.3.7"
dependencies = [
    "oauth2client==4.1.3",
    "google-api-python-client==2.167.0",
    "google-cloud-bigquery==3.31.0",
    "google-cloud-storage==2.19.0",
    "paramiko==3.5.1",
    "Jinja2==3.1.6",
    "mysql-connector==2.2.9",
    "boto3==1.37.34",
    "simple-salesforce==1.10.1",
    "parse==1.15.0",
    "delegator.py==0.1.1",
    "markupsafe==3.0.2",
    "pandas==2.2.3",
    "pysftp==0.2.9"
]

package_root = os.path.abspath(os.path.dirname(__file__))

readme_filename = os.path.join(package_root, "README.rst")
with io.open(readme_filename, encoding="utf-8") as readme_file:
    readme = readme_file.read()


setuptools.setup(
    name=name,
    version=version,
    description=description,
    long_description=readme,
    author='TMG Data Platform team',
    author_email="data.platform@telegraph.co.uk",
    license="Apache 2.0",
    url='https://github.com/telegraph/tmg-data',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    packages=setuptools.find_packages(),
    install_requires=dependencies,
    python_requires='>=3.9',

)
