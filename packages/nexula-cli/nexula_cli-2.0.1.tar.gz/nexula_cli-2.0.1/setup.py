import os
from setuptools import setup, find_packages

setup(
    name="nexula-cli",
    version="2.0.1",
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
    description="Enterprise CLI for AI/ML Security with Interactive Remediation - Scan, Fix, and Secure AI Supply Chains",
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type="text/markdown",
    url="https://github.com/Nexula-AI/nexula-cli",
    project_urls={
        "Documentation": "https://docs.nexula.one",
        "Source": "https://github.com/Nexula-AI/nexula-cli",
        "Tracker": "https://github.com/Nexula-AI/nexula-cli/issues",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="security ai ml vulnerability scanner sast devsecops",
    python_requires=">=3.8",
)
