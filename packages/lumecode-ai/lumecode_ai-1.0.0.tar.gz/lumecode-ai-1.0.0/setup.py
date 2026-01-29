from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lumecode-ai",
    version="1.0.0",
    author="anonymus-netizien",
    author_email="lumecode@example.com",
    description="AI-powered coding agent with multi-model LLM support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anonymus-netizien/lumecode",
    project_urls={
        "Bug Tracker": "https://github.com/anonymus-netizien/lumecode/issues",
        "Documentation": "https://github.com/anonymus-netizien/lumecode#readme",
        "Source Code": "https://github.com/anonymus-netizien/lumecode",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "platformdirs>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lumecode=lumecode.cli:main",
        ],
    },
)
