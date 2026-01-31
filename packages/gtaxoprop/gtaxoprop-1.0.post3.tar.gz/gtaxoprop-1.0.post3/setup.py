from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="gtaxoprop",
    version="1.0.post3",
    author="Maulana Malik Nashrulloh, Sonia Az Zahra Defi, Brian Rahardi, Muhammad Badrut Tamam, Riki Ruhimat, Hessy Novita",
    author_email="maulana@genbinesia.or.id",
    description="A utility to generate input files for taxonomy propagation and assignment in QIIME/QIIME2 from the NCBI database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/biomikalab/GTAXOPROP",
    packages=find_packages(),
    py_modules=["gtaxoprop"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Development Status :: 5 - Production/Stable",
    ],
    python_requires=">=3.10",
    install_requires=[
        "tinydb==4.8.2",
        "pbr>=6.1.1",
        "stevedore>=5.5.0",
        "cogent3>=2025.9.8a2",
        "biopython>=1.85",
    ],
    entry_points={
        "console_scripts": [
            "gtaxoprop=gtaxoprop:main",
        ],
    },
    keywords="bioinformatics, taxonomy, ncbi, qiime, qiime2, microbiome, microbiology, genomics",
    project_urls={
        "Bug Reports": "https://gitlab.com/biomikalab/GTAXOPROP/issues",
        "Source": "https://gitlab.com/biomikalab/GTAXOPROP",
        "Documentation": "https://gitlab.com/biomikalab/GTAXOPROP#readme",
    },
    license="GPLv3",
)
