from setuptools import setup, find_packages

setup(
    name="netbox_scripts_lib",
    version="0.2",
    author="Jiri Vrany",
    author_email="jiri.vrany@cesnet.cz",
    description="Shared lib of functions and tools for NetBox Custom Scripts",
    packages=find_packages(),
    install_requires=[
        "Django>=3.0",
    ],
)
