from setuptools import setup, find_packages

setup(
    name="nexula-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "nexula=nexula.cli:cli",
        ],
    },
    author="Nexula AI",
    description="Enterprise CLI for Nexula AI Supply Chain Security Platform",
    python_requires=">=3.8",
)
