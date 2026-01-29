from setuptools import setup, find_packages

setup(
    name="jai-STT",
    version="0.1",
    author="Jai Yadav",
    author_email="dragon4u4u4@gmail.com",
    description="Speech to text by Jai",
    packages=find_packages(),
    install_requires=[
        "selenium",
        "webdriver-manager"
    ],
)
