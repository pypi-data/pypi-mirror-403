from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='msq_data_store_tools',
    packages=find_packages(),
    version='1.0.0',
    description='This is a utility package designed to enable the data team to integrate with the MSQ data lake, i.e. the DataStore',
    long_description=long_description,
    long_description_content_type="text/markdown",    
    url="https://github.com/freemavens/data_store_tools",
    author="Damian Rumble <damian.rumble@forge.com>"
)

### Python code to publish package ###
#pip install build twine setuptools wheel

# clean previous builds
#rm -rf dist/ build/ *.egg-info

#python setup.py sdist bdist_wheel
#twine upload -u __token__ -p [PYPI API KEY - in ENV file] dist/*