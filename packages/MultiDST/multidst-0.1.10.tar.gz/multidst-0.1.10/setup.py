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
    description = "MultiDST is a Python library for multiple hypothesis testing, providing FWER and FDR control methods along with the Significant Index Plot to easily visualize significant hypotheses.",
    version='0.1.10',
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

