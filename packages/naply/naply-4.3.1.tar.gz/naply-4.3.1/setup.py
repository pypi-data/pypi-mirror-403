from setuptools import setup, find_packages

setup(
    name="naply",
    version="4.3.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "tqdm",
    ],
    extras_require={
        "finetune": ["safetensors", "pandas"],
        "all": ["colorama", "safetensors", "pandas"],
    },
    author="NAPLY Team",
    description="The Most Powerful AI Framework: Build & Fine-Tune ChatGPT-Level Models - CPU-Optimized, LoRA/QLoRA",
    python_requires=">=3.8",
)
