from setuptools import setup, find_packages

setup(
    name="mindstorms-net",
    version="0.1.0",
    author="Your Name",
    author_email="youremail@example.com",
    description="Python package to connect LEGO EV3 and 51515 via ESP32/BLE/serial",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mindstorms-net",
    packages=find_packages(),
    python_requires='>=3.5',
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
