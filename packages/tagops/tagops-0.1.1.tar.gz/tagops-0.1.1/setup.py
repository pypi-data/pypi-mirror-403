from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tagops",
    version="0.1.1",
    author="Tharun",  # Replace with your name
    author_email="tharunme25@gmail.com",  # Replace with your email
    description="An AWS Tag-Based Operations Tool for safe and efficient resource management.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tharun-me/tagopss",  # Replace with your project's URL
    license="MIT",
    packages=['tagops'] + ['tagops.' + p for p in find_packages(exclude=['__pycache__', '*.egg-info'])],
    package_dir={'tagops': '.'},
    install_requires=[
        "boto3",
        "tabulate",
        "colorama",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "tagops=tagops.tagops:cli",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)
