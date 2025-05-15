from setuptools import setup, find_packages

setup(
    name="swelist",
    version="0.1.7",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer",
    ],
    entry_points={
        "console_scripts": [
            "swelist=swelist.main:app",
        ],
    },
    author="Yuan Chen",
    author_email="yuan.chen@sojoai.com",
    description="A CLI tool for job seekers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/chenyuan99/swelist",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
