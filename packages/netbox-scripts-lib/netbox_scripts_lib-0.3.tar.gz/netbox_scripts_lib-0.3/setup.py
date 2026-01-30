from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="netbox_scripts_lib",
    version="0.3",
    author="Jiri Vrany",
    author_email="jiri.vrany@cesnet.cz",
    description="Shared lib of functions and tools for NetBox Custom Scripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "Django>=3.0",
    ],
)
