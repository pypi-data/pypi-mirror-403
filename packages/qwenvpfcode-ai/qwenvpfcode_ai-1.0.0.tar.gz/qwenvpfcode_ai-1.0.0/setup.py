from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# List requirements directly (don't read from file to avoid build errors)
requirements = [
    "torch>=2.0.0",
    "transformers>=4.35.0", 
    "accelerate>=0.24.0",
    "sentencepiece>=0.1.99",
    "tiktoken>=0.5.0",
]

setup(
    name="qwenvpfcode-ai",
    version="1.0.0",
    author="Adriano (litaliano00-dev)",
    author_email="",  # Optional: add your email
    description="Fast local AI assistant based on Qwen2.5-Coder-1.5B - No filters, complete memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/litaliano00-dev/QwenVPFCode-AI",
    project_urls={
        "Bug Tracker": "https://github.com/litaliano00-dev/QwenVPFCode-AI/issues",
        "Source Code": "https://github.com/litaliano00-dev/QwenVPFCode-AI",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Android",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "qwenvpfcode-ai=qwenvpfcode_ai.cli:main",
        ],
    },
    keywords="ai, local-ai, qwen, assistant, terminal, uncensored, privacy",
)
