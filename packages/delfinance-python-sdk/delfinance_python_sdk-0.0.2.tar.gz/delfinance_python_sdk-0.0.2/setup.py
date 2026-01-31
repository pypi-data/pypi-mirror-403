from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="delfinance-python-sdk",
    author="Delfinance Team",
    author_email="dev@delfinance.com",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="SDK oficial da Delfinance para Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/delfinance/python-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/delfinance/python-sdk/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=0.21.1",
    ],
)
