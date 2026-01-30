# Before publishing install this
pip install setup tools wheel twine


# To build the package
python setup.py sdist bdist_wheel

code for setup.py

from setuptools import setup, find_packages

setup(
    name="aininja",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={
        "console_scripts": [
           "jarvis=aininja:aininja"
        ], 
        },    
    author="Rajat Ratewal",
    author_email="rajat@greengroovetech.com",
    description="AI Powered Assisstant For Developers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown"    
)

# Install the package locally
pip install dist/aininja-0.1.0-py3-none-any.whl

# Upload to pypi your package
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypiapikey
twine upload dist/*
