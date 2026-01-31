# Tools Onderzoek & Statistiek

This package contains the tools used by the data scientists/researchers working at Onderzoek & Statistiek.

## Tools

- Huisstijl:
  - Tables: create `huisstijl` formatted excel files
  - Huisstijl: create `huisstijl` figures
- Database
  - Database connection: tools to connect to database
  - Database transfer: easily transfer tables between databases using sqlalchemy to reflect metadata
- Download: quickly download specific branch of repo to local folder
- Geo: some helpers to download geo data
- Polars helpers:
- Create tables: create tables that can be published with custom rounding

## Installation instructions

The package can be installed using:
    - pip
      - Use pip install "toolsos[all]". This will install the package including all the dependencies
    - conda.
      - Use pip install toolsos. The user has to download the dependencies themselves. At a later stage we might native support for conda

## Building the package

Instructions on building a package can be found [here](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

- py -m pip install --upgrade build
- py -m build

## Uploading the package to PyPi

- make a pypi account
- ask to be added as collaborator to toolsos
- first update twine: py -m pip install --upgrade twine
- upload to pypi: twine upload dist/* --skip-existing

## Install to local enviroment for testing

- python -m venv local (maak een lokale venv aan)
- local\Scripts\activate (activeer de venv)
- pip install -e . (installer toolsos)
- pip install -r local_requirements.txt (installeer de benodigde dependencies)
