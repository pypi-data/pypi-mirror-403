from setuptools import setup, find_packages

setup(
    name="cache_central_flush",
    version="2.0.0",
    description="Lightweight client package to asynchronously trigger centralized cache invalidation via API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Karan Singh Tomar",
    author_email="karantomar207@gmail.com",
    url="https://github.com/karantomar207/cache-central-flush",  
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests>=2.20,<3",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
