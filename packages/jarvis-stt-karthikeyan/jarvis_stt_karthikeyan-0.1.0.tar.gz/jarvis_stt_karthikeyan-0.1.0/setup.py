from setuptools import setup, find_packages

setup(
    name="jarvis-stt-karthikeyan",
    version="0.1.0",
    packages=find_packages(),
    author="Karthikeyan",
    author_email="karthikcristianosiuu@gmail.com",
    description="This is a speech to text package created by Karthikeyan",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Karthikeyanmurugavel/Jarvis",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "selenium",
        "webdriver-manager"
    ],
)
