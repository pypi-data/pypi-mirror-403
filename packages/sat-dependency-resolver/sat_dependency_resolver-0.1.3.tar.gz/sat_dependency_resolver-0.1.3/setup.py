from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sat-dependency-resolver",
    version="0.1.3",
    author=" Shehan Horadagoda",
    author_email="shehan87h@gmail.com",
    description="Universal dependency resolver using SAT solvers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Apollo87z/sat-dependency-resolver",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-sat>=0.1.7.dev18",
        "requests>=2.27.0",
    ],
    extras_require={
        "api": ["flask>=2.0.0"],
        "ai": ["anthropic>=0.18.0", "python-dotenv>=1.0.0"],
    },
)