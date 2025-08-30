import os
from django.conf import settings
from .ftp_client import SimpleFTP

def get_reader():
    mode = settings.TS_SYNC.get("MODE", "ftps")
    file_name = settings.TS_SYNC["FILE"]["NAME"]

    if mode in ("ftp", "ftps"):
        f = settings.TS_SYNC["FTP"]
        client = SimpleFTP(
            host=f["HOST"],
            port=f["PORT"],
            user=f["USER"],
            password=f["PASS"],
            passive=f.get("PASSIVE", True),
            timeout=f.get("TIMEOUT", 60),
            tls=(mode == "ftps"),
            implicit_tls=f.get("IMPLICIT_TLS", False),
        )
        return (mode, client, f["INCOMING_DIR"], None, file_name)

    # local
    ldir = settings.TS_SYNC["LOCAL"]["INCOMING_DIR"]
    return ("local", None, ldir, None, file_name)
