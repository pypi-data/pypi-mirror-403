from setuptools import setup, find_packages
import pathlib

# Read README with explicit UTF-8 encoding
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="qa-agent-cli",
    version="1.0.0",
    description="AI-powered code quality analysis tool using Groq Llama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="QA Agent Team",
    python_requires=">=3.9",
    py_modules=["qa_agent"],
    install_requires=[
        "groq>=0.4.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "reportlab>=4.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "qa-agent=qa_agent:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
