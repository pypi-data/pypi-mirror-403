from setuptools import setup, find_packages

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='MultiDST',
    author="R.A.S. Ouchithya",
    license ="MIT",
    license_files=("LICENSE",),
    description = "A toolkit for multiple hypothesis testing that implements common FWER and FDR control procedures, with intuitive significance visualisation using the Significant Index Plot.",
    version='0.1.11',
    packages=find_packages(),  # Automatically find all packages and subpackages
    install_requires=[
        'numpy', 
        'pandas',
        'scipy',
        'statsmodels',
        'matplotlib'
    ],
    extras_require = {
        "dev":["twine>4.0.2"],
    },
    python_requires=">=3.10",
    long_description=long_description,
    long_description_content_type='text/markdown'
)

