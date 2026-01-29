from setuptools import setup, find_packages

setup(
    name="drevixbot",
    version="1",
    packages=find_packages(),
    install_requires=["requests"],
    author="Drevix Dev",
    description="The official Secure Receiver Gate for Drevix Bots",
    long_description="A simplified library that allows users to create bots using only a Bot Token.",
    long_description_content_type="text/markdown",
)
