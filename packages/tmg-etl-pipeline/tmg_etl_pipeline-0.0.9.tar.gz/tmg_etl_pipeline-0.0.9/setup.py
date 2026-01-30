import os
import io
import setuptools


name = "tmg-etl-pipeline"
description = "TMG ETL pipeline"
version = "0.0.9"
dependencies = [
    "google-cloud-secret-manager==2.23.2",
    "PyYAML==6.0.2"
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
    url='https://github.com/telegraph/tmg-etl-pipeline',
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    packages=setuptools.find_packages(),
    install_requires=dependencies,
    python_requires='>=3.6',
)
