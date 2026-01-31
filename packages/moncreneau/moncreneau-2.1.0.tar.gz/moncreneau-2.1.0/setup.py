from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="moncreneau",
    version="2.1.0",
    description="Official Moncreneau API client for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Moncreneau",
    author_email="moncreneau.rdv@gmail.com",
    url="https://github.com/nbsidiki/moncreneau-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="moncreneau api client appointments booking",
)
