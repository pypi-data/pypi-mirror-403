from setuptools import setup, find_packages

setup(
    name="monxcli",
    version="1.0.1",
    description="A simple, extensible git like CLI framework.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Reihmon Estremos",
    author_email="koydaut@gmail.com",
    url="https://gitlab.com/mongkoy/monxcli.git",  # Link to your repo
    license="MIT",
    packages=find_packages(),  # Automatically find and include all Python packages
    include_package_data=True,  # Include non-Python files like README.md
    install_requires=[
        # Dependencies
    ],
    python_requires=">=3.7",  # Minimum Python version
    entry_points={
        "console_scripts": [
            "monxcli=monxcli.main:commands",  # Command to invoke your tool
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
