"""
OMNIMIND Setup Script
Install with: pip install -e .
"""
from setuptools import setup, find_packages
# No Rust required anymore
# try:
#     from setuptools_rust import Binding, RustExtension
# except ImportError:
#     pass

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="omnimind",
    version="0.2.9",
    author="OMNIMIND Team",
    description="State-Space Language Model - Scalable AI for any device with unlimited memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kue-kid/omnimind",
    packages=find_packages(),
    # rust_extensions=[], # Removed for Triton Migration
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",  # Support Python 3.8+ for wider compatibility
    install_requires=[
        "torch",
        "einops",
        "tqdm",
        "jinja2",
        "safetensors",
        "fire",         # CLI
        "fastapi",      # Server
        "uvicorn",      # Server
        "orjson",       # Server Opt
        "uvloop",       # Server Opt
    ],
    extras_require={
        "finetune": [
            "transformers",
            "peft",
            "bitsandbytes",
            "datasets",
            "accelerate",
        ],
        "memory": [
            "chromadb",
            "sentence-transformers",
        ],
        "voice": [
            "openai-whisper",
            "edge-tts",
        ],
        "vision": [
            "Pillow",
            "torchvision",
            "opencv-python",
        ],
        "audio": [
            "torchaudio",
            "librosa",
        ],
        "generation": [
            "diffusers",
            "transformers",
            "scipy",     # For some diffusers schedulers
        ],
        "science": [
            "numpy",
            "matplotlib",
            "sympy",
            "requests",
            "beautifulsoup4",
        ],
        "all": [
            "accelerate",
            "sentencepiece",
            "transformers",
            "peft",
            "bitsandbytes",
            "datasets",
            "chromadb",
            "sentence-transformers",
            "jinja2",
            "Pillow",
            "torchvision",
            "torchaudio",
            "opencv-python",
            "librosa",
            "diffusers",
            "scipy",
            "numpy",
            "matplotlib",
            "sympy",
            "requests",
            "beautifulsoup4",
        ],
        "dev": [
            "pytest",
            "rich",
        ],
    },
    entry_points={
        "console_scripts": [
            "omnimind=omnimind.cli:main",  # Main CLI
            "omnimind-train=omnimind.scripts.train:main",
            "omnimind-generate=omnimind.scripts.inference:main",
            "omnimind-server=omnimind.server:run_server",
        ],
    },
)
