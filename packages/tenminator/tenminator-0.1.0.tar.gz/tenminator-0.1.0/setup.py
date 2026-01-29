"""
MiniTorch Lite - Setup Script
=============================
Script de configuración para instalación y distribución en PyPI.

Instalación local (desarrollo):
    pip install -e .

Instalación desde PyPI (cuando esté publicado):
    pip install minitorch-lite

Subida a PyPI:
    1. Crear cuenta en https://pypi.org/
    2. Instalar twine: pip install twine
    3. Construir distribución: python setup.py sdist bdist_wheel
    4. Subir a PyPI: twine upload dist/*
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leer README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

# Dependencias base
install_requires = [
    "numpy>=1.20.0",
]

# Dependencias opcionales
extras_require = {
    "numba": ["numba>=0.55.0"],
    "jax": ["jax>=0.4.0", "jaxlib>=0.4.0"],
    "cupy": ["cupy>=11.0.0"],
    "scipy": ["scipy>=1.7.0"],
    "keras": ["tensorflow>=2.10.0"],
    "pytorch": ["torch>=1.12.0"],
    "networkx": ["networkx>=2.8.0"],
    "all": [
        "numba>=0.55.0",
        "scipy>=1.7.0",
        "networkx>=2.8.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=3.0.0",
        "black>=22.0.0",
        "flake8>=4.0.0",
        "mypy>=0.950",
    ],
}

setup(
    name="minitorch-lite",
    version="0.1.0",
    author="MiniTorch Lite Team",
    author_email="minitorch@example.com",
    description="Lightweight Deep Learning Library with multi-backend support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/minitorch/minitorch-lite",
    project_urls={
        "Bug Tracker": "https://github.com/minitorch/minitorch-lite/issues",
        "Documentation": "https://minitorch-lite.readthedocs.io/",
        "Source Code": "https://github.com/minitorch/minitorch-lite",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    keywords=[
        "deep learning",
        "machine learning",
        "neural networks",
        "autograd",
        "pytorch",
        "tensorflow",
        "keras",
        "numpy",
        "numba",
        "jax",
    ],
    include_package_data=True,
    zip_safe=False,
)
