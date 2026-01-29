from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="deerdawn",
    version="1.0.0",
    author="DeerDawn",
    author_email="support@deerdawn.com",
    description="Official Python SDK for DeerDawn - AI governance and decision control platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deerdawn/deerdawn-sdk-python",
    project_urls={
        "Bug Tracker": "https://github.com/deerdawn/deerdawn-sdk-python/issues",
        "Documentation": "https://deerdawn.com/docs/sdks",
        "Homepage": "https://deerdawn.com",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
        ],
    },
    keywords="deerdawn ai-governance decision-control policy-engine ai-security",
)
