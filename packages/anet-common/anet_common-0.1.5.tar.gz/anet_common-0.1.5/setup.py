import os
from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="anet-common",
    version="0.1.5",
    description="Common utilities, settings, and contracts for Anet Microservices (Django/DRF)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/murodalidev/anet-common/",
    author="Murodali Narzullaev",
    author_email="murodalinarzullaevofficial@gmail.uz",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=5.2",
        "djangorestframework==3.16.1",
        "drf-spectacular==0.29.0",
        "django-modeltranslation==0.19.19",
        "djangorestframework-camel-case>=1.4.2",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 5.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.10",
    keywords="django, drf, microservices, utilities, common",
)
