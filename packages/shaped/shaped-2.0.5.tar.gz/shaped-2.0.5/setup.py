from setuptools import find_packages, setup

# To install the library, run the following:
#
# python setup.py install
#

with open("README.md") as f:
    long_description = f.read()
version = "2.0.5"
setup(
    name="shaped",
    version=version,
    author="Shaped Team",
    author_email="support@shaped.ai",
    url="https://github.com/shaped-ai/magnus",
    description="CLI and SDK tools for interacting with the Shaped API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["shaped-ai"],
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
    ],
    packages=find_packages(
        where=".",
        include=["shaped*"],
        exclude=["tests"],
    ),
    package_dir={"": "."},
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "pyarrow==20.0.0",
        "pandas==2.3.0",
        "numpy==1.26.4",
        "typer==0.7.0",
        "click==8.2.1",
        "requests>=2.28.1",
        "pydantic>=2.8.2",
        "pyyaml>=6.0",
        "tqdm==4.67.1",
        "s3fs==0.4.2",
        "fsspec==2023.5.0",
        "urllib3 >= 2.2.3",
        "h2 >= 4.0.0",
        "python-dateutil",
        "typing-extensions >= 4.7.1",
        "pytest==8.4.1",
        "pytest-mock==3.14.0",
    ],
    python_requires=">=3.9, <3.14",
    entry_points={"console_scripts": ["shaped=shaped.cli.shaped_cli:main"]},
    test_suite="python.tests",
)
