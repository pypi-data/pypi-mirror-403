from __future__ import annotations

import getpass
import json
import os
import subprocess
from json import JSONDecodeError
from pathlib import Path
from typing import Optional

import keyring
import yaml


def get_db_connection_strings(
    path: str, reset_pw: Optional[list[str]] = None
) -> DbStringCollection:
    """Creates object containing all database connection strings based on yaml
    file containg the database connection settings. Password for the specific
    database will be prompted and stored in the keyring of the device

    Args:
        path (str): _description_
        flush_pw (Optional[list[str]], optional): List with passwords to be reset. Use the
            name of the database connection in the config file. Defaults to None.

    Returns:
        DbStringCollection: Simple class with an attribute for each connection string
    """
    with open(path) as f:
        db_info = yaml.safe_load(f)

    dsc = DbStringCollection()

    for dbname, params in db_info.items():
        flush = dbname in reset_pw if reset_pw else False

        if params["password"] == "access_token":
            pw = get_azure_access_token()
        else:
            pw = get_pw_from_keyring(dbname=dbname, user=params["user"], reset_pw=flush)

        engine = build_conn_string(pw=pw, **params)
        dsc.add_conn_string(dbname, engine)

    return dsc


def build_conn_string(user: str, pw: str, host: str, port: str, dbname: str) -> str:
    """Builds the connection string for the database

    @@TODO
    Add possibility to use different database types

    Args:
        user (str): username
        pw (str): database password
        host (str): database host
        port (str): database port
        dbname (str): database name

    Returns:
        str: engine string
    """
    return f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"


def get_pw_from_keyring(dbname: str, user: str, reset_pw: Optional[bool] = None) -> str:
    """_summary_

    Args:
        db_name (str): database name
        user (str): username

    Returns:
        str: password
    """
    pw = keyring.get_password(dbname, user)

    if not pw or reset_pw:
        pw = getpass.getpass(f"Input password for {dbname}: ")
        keyring.set_password(dbname, user, pw)

    return pw


class DbStringCollection:
    """_summary_"""

    def add_conn_string(self, db_name: str, connection_str: str) -> None:
        setattr(self, db_name, connection_str)


def get_azure_access_token():
    command = "az account get-access-token --resource-type oss-rdbms"
    result = subprocess.run(command, capture_output=True, shell=True, text=True)

    try:
        return json.loads(result.stdout)["accessToken"]
    except JSONDecodeError:
        subprocess.run("az login", shell=True)


def get_token_from_pgpass() -> None:
    p = Path(os.getenv("APPDATA")) / "postgresql" / "pgpass.conf"
    with open(p) as f:
        token = f.readline().split(":")[4]

    return token


def write_pgpass(
    host: str, port: str, database: str, user: str, path: str | None = None
) -> None:
    password = get_azure_access_token()
    conn_string = f"{host}:{port}:{database}:{user}:{password}"

    if not path:
        if os.name == "nt":
            path = Path(os.getenv("APPDATA")) / "postgresql" / "pgpass.conf"
        else:
            path = Path("$home/.pgpass")

    if not path.parent.exists():
        path.parent.mkdir()

    with open(path, "w") as f:
        f.write(conn_string)

    if os.name != "nt":
        path.chmod("0600")


def write_multiple_pgpass(conn_details, path: str | None = None):
    password = get_azure_access_token()

    conn_strings = []
    for c in conn_details:
        c_string = f'{c["host"]}:{c["port"]}:{c["database"]}:{c["user"]}:{password}'
        conn_strings.append(c_string)

    if not path:
        if os.name == "nt":
            path = Path(os.getenv("APPDATA")) / "postgresql" / "pgpass.conf"
        else:
            path = Path("$home/.pgpass")

    if not path.parent.exists():
        path.parent.mkdir()

    with open(path, "w") as f:
        f.writelines(line + "\n" for line in conn_strings)

    if os.name != "nt":
        path.chmod("0600")
