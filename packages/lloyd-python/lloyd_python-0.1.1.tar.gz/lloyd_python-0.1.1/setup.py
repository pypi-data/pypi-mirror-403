from setuptools import setup, find_packages

setup(
    name="lloyd-python",
    version="0.1.1",
    author="Your Name",
    description=open("DESCRIPTION.txt").read().strip(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "lloyd=lloyd.core1:main",
        ],
    },
    python_requires=">=3.6",
)

