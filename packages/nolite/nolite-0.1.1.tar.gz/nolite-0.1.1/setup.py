from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    fh.close()

setup(
    name="nolite",
    version="0.1.1",
    author="FakeCoder01",
    author_email="fakecoder@duck.com",
    description="A Python library to create websites using only Python code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FakeCoder01/nolite",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=2.0.0,<3.0.0",
        "Flask-SQLAlchemy>=2.5.1,<3.0.0",
        "SQLAlchemy>=1.4,<2.0",
        "Flask-Login>=0.6.0",
        "email_validator>=2.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "nolite=nolite.cli:main",
        ],
    },
)
