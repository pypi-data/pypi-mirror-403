from setuptools import setup, find_packages

setup(
    name="area_jiya",       # <- your unique project name
    version="0.1",
    packages=find_packages(),
    install_requires=[],    # dependencies if any
    author="Jiya",
    author_email="youremail@example.com",
    description="A simple library to calculate areas of shapes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/area_jiya",  # optional
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
