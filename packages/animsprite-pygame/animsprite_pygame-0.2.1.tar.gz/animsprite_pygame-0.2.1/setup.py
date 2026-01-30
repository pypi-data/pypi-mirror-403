from setuptools import setup, find_packages
from pathlib import Path

# Lire le contenu du README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="animsprite-pygame",
    version="0.2.1",
    author="EnOx_S",
    author_email="enoxs.pro@gmail.com",
    description="Une librairie légère pour gérer les spritesheets et flipbooks dans Pygame",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EnOx-S/animsprite-pygame",
    project_urls={
        "Bug Tracker": "https://github.com/EnOx-S/animsprite-pygame/issues",
        "Documentation": "https://github.com/EnOx-S/animsprite-pygame#readme",
        "Source Code": "https://github.com/EnOx-S/animsprite-pygame",
    },
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Graphics",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pygame>=2.1.3",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "isort>=5.0",
        ],
    },
    keywords="pygame sprite animation spritesheet flipbook game development",
    license="GPL-3.0-only",
    include_package_data=True,
    zip_safe=False,
)
