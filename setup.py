from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bai-autotest",
    version="0.1.0",
    author="bettehub",
    author_email="bettehub@gmail.com",
    description="MCP-based test automation for diagram-driven testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bettehub/bai-autotest",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.1.0",
        "pytest>=7.0.0",
        "playwright>=1.40.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0.0",
        "click>=8.0.0",
        "lark>=1.1.0",
    ],
    extras_require={
        "dev": [
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "pre-commit",
        ],
    },
    entry_points={
        "console_scripts": [
            "bai-autotest=bai_test_mcp.cli:main",
        ],
    },
)