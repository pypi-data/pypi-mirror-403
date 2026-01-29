"""Parse the arguments, read the configuration file and fetch the backup
from the truenas firewall
"""

import argparse
import re
import httpx

from os import environ, path, scandir, stat, remove
from datetime import datetime as dt
from urllib.parse import urlparse
from gzip import compress

from truenas_api_client import Client
from yaml import safe_load
from schema import Schema, SchemaError, And, Or, Optional, Use

from prometheus_client import Gauge, CollectorRegistry, write_to_textfile

from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA512

__version__ = "0.1.0"

DEFAULT_CONFIGURATION_FILE = path.join(
    environ["HOME"], ".config", "truenas-backup", "config.yml"
)

SCHEMA = Schema(
    {
        "truenas": Schema(
            {
                Optional("host", default="truenas.local"): And(
                    str, lambda s: len(s) > 0
                ),
                "api_user": And(str, lambda s: len(s) > 0),
                "api_key": And(str, lambda s: len(s) > 0),
                Optional("ssl_verify", default=True): bool,
                Optional("call_timeout", default=60.0): And(
                    Use(float), lambda s: s >= 1.0
                ),
                Optional("backup_password"): And(str, lambda s: len(s) > 0),
            },
        ),
        Optional(
            "output", default={"directory": ".", "name": "truenas-%Y%m%d%H%M"}
        ): Schema(
            {
                Optional("directory"): And(str, lambda s: len(s) > 0),
                Optional("name", default="truenas-%Y%m%d%H%M.backup"): And(
                    str, lambda s: len(s) > 0
                ),
                Optional("keep"): And(Use(int), lambda x: x > 0),
            },
        ),
        Optional("metrics"): Schema(
            {
                "directory": And(str, lambda s: len(s) > 0),
                Optional("suffix"): And(str, lambda s: len(s) > 0),
            },
        ),
    }
)


def parse_arguments():
    """Parse the arguments

    Returns
    -------
    dict
        parsed arguments
    """

    parser = argparse.ArgumentParser(
        prog="truenas-backup",
        description=f"A tool to fetch backups from the TrueNAS instance (v{ __version__ })",
    )

    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIGURATION_FILE,
        metavar="FILE",
        type=argparse.FileType("r"),
        help="the configuration file (default: %(default)s)",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="the output file (default is specified in the configuration file)",
    )

    return vars(parser.parse_args())


def parse_configuration(stream):
    """Parse the configuration file

    Parameters
    ----------
    stream : io.IOBase | str
        Stream to read the configuration from.

    Returns
    -------
    dict
        Parsed and validated configuration
    """
    config = SCHEMA.validate(safe_load(stream))

    return config


def fetch_backup(config: dict, out_file: str):
    """Fetch the backup from the firewall

    Parameters
    ----------
    config : dict
        truenas configuration
    out_file : str
        Path to the output file
    """

    response = None

    with Client(
        uri="wss://" + config["host"] + "/api/current",
        verify_ssl=config["ssl_verify"],
        call_timeout=config["call_timeout"],
    ) as client:

        resp = client.call(
            "auth.login_ex",
            {
                "mechanism": "API_KEY_PLAIN",
                "username": config["api_user"],
                "api_key": config["api_key"],
                "login_options": {"user_info": False},
            },
        )

        if resp["response_type"] != "SUCCESS":
            raise RuntimeError(f"Authentication failed: {resp['response_type']}")

        dl = client.call(
            "core.download", "config.save", [{"secretseed": True}], "backup", False
        )

        response = httpx.get(
            "https://" + config["host"] + dl[1],
            verify=config["ssl_verify"],
        )

        response.raise_for_status()

    data = compress(response.content)

    with open(out_file, "wb") as file:
        file.write(
            data
            if not "backup_password" in config
            else encrypt_backup(data, config["backup_password"])
        )


def rotate_files(output_config: dict):
    """Rotate the files

    Parameters
    ----------
    output_config : dict
        Configuration
    """
    files = sorted(
        [
            f.name
            for f in scandir(output_config["directory"])
            if f.is_file and re.search(r"\.backup$", f.name)
        ]
    )

    while len(files) > output_config["keep"]:
        remove(path.join(output_config["directory"], files.pop(0)))


def encrypt_backup(data: bytes, password: str) -> bytes:
    """
    Encrypts a byte array.

    - AES-256-CBC
    - Key derivation: PBKDF2-HMAC-SHA512 with 100,000 iterations
    - Random 8-byte salt (OpenSSL 'salted' format: 'Salted__' + salt + ciphertext)
    - PKCS7 padding

    Returns the full encrypted backup file.
    """
    # Generate random 8-byte salt
    salt = get_random_bytes(8)

    # Derive 32-byte key + 16-byte IV using PBKDF2-HMAC-SHA512, 100000 iterations
    key_iv = PBKDF2(
        password=password.encode("utf-8"),
        salt=salt,
        dkLen=48,  # 32 bytes key + 16 bytes IV
        count=100000,
        hmac_hash_module=SHA512,
    )
    key = key_iv[:32]
    iv = key_iv[32:48]

    # Encrypt with AES-256-CBC and PKCS7 padding
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))

    # OpenSSL salted format
    encrypted_payload = b"Salted__" + salt + ciphertext

    return encrypted_payload


def main():
    """_summary_

    Raises
    ------
    ValueError
        Configuration is invalid
    ValueError
        Output directory does not exist
    """
    arguments = parse_arguments()

    try:
        config = parse_configuration(arguments["config"])
    except SchemaError as ex:
        raise ValueError(
            "configuration invalid\n" + str(ex.with_traceback(None))
        ) from None

    arguments["config"].close()

    now = dt.now()

    # If the file was given through an argument, use that and skip the rotation
    # If not, use the configuration to construct the file name and do the rotation
    # if requested and the directory was provided as an absolute path
    if arguments["output"] is not None:
        out_file = arguments["output"]
        rotate = False
    else:
        if not path.isdir(config["output"]["directory"]):
            raise ValueError(
                f"Target directory {config['output']['directory']} does not exist or is not a directory"  # pylint: disable=line-too-long
            )
        rotate = (
            path.isabs(config["output"]["directory"]) and "keep" in config["output"]
        )
        out_file = path.join(
            config["output"]["directory"], now.strftime(config["output"]["name"])
        )

    fetch_backup(config["truenas"], out_file)

    if rotate:
        rotate_files(config["output"])

    if "metrics" in config:
        registry = CollectorRegistry()
        backup_time = Gauge(
            "truenas_backup_timestamp_seconds",
            "Time the backup was started.",
            ["host"],
            registry=registry,
        )
        backup_size = Gauge(
            "truenas_backup_size_bytes",
            "Size of the backup.",
            ["host"],
            registry=registry,
        )

        if not path.isdir(config["metrics"]["directory"]):
            raise ValueError(
                f"Metrics directory {config['metrics']['directory']} does not exist or is not a directory"  # pylint: disable=line-too-long
            )

        metrics_file = path.join(config["metrics"]["directory"], "truenas-backup")
        if "suffix" in config["metrics"]:
            metrics_file += "-" + config["metrics"]["suffix"]

        metrics_file += ".prom"

        host = urlparse("wss://" + config["truenas"]["host"]).hostname
        backup_time.labels(host).set_to_current_time()
        backup_size.labels(host).set(stat(out_file).st_size)

        write_to_textfile(metrics_file, registry)
