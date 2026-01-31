from setuptools import setup, find_packages

setup(
    name="xapp-protected",
    version="0.1.4",
    description="Protected XApp core module",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mr Void",
    url="https://github.com/ibrahimkhan008",
    packages=find_packages(),
    
    # CRITICAL: Include ALL .pyc files from __pycache__
    package_data={
        'xapp_protected': [
            '__pycache__/*.pyc',
            '__pycache__/xapp_core.cpython-*.pyc',
        ],
    },
    
    include_package_data=True,
    
    install_requires=[
        "Flask>=2.3.0",
        "pycryptodome>=3.18.0",
        "requests>=2.31.0",
        "PyJWT>=2.8.0",
        "protobuf>=4.23.0",
    ],
    
    python_requires=">=3.8",
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
    ],
)