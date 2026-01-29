from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "LICENSE") as file:
    _license = file.read()

with open(BASE_DIR / "README.md") as file:
    _description = file.read()

setup(
    name="fasoarzeka",
    version="0.0.1",
    long_description=_description,
    long_description_content_type="text/markdown",
    url="https://github.com/parice02/fasoarzeka",
    description="API non officiel pour les paiements mobiles le moyen de paiement FASO ARZEKA au Burkina Faso",
    packages=find_packages(),
    author="Mohamed Zeba",
    author_email="m.zeba@mzeba.dev",
    license=_license,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    requires=["request", "urllib3"],
)
