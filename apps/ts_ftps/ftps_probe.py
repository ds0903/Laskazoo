# ftps_probe.py
import ssl
from ftplib import FTP_TLS
from io import BytesIO

HOST = "laskazoo.com.ua"
PORT = 21
USER = "danil"
PASS = "danilus15"
REMOTE = "/incoming/TSGoods.trs"

def make_ctx(verify=True, tls12_only=True):
    if verify:
        ctx = ssl.create_default_context()
    else:
        ctx = ssl._create_unverified_context()
        ctx.check_hostname = False
    # інколи TLS1.3 викликає дива у деяких стеків => форсимо TLS1.2
    if hasattr(ssl, "TLSVersion") and tls12_only:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    return ctx

def seq_A():
    print("== Sequence A: AUTH -> LOGIN -> PROT P ==")
    ctx = make_ctx(verify=True, tls12_only=True)
    ftps = FTP_TLS(context=ctx)
    ftps.set_debuglevel(2)
    ftps.connect(HOST, PORT, timeout=10)
    ftps.auth()                          # STARTTLS
    ftps.login(USER, PASS)               # логін по захищеному контролю
    ftps.prot_p()                        # шифруємо data channel
    ftps.set_pasv(True)
    buf = BytesIO()
    ftps.retrbinary(f"RETR {REMOTE}", buf.write)
    print("READ OK (A):", len(buf.getvalue()), "bytes")
    ftps.quit()

def seq_B():
    print("== Sequence B: AUTH -> PROT P -> LOGIN ==")
    ctx = make_ctx(verify=True, tls12_only=True)
    ftps = FTP_TLS(context=ctx)
    ftps.set_debuglevel(2)
    ftps.connect(HOST, PORT, timeout=10)
    ftps.auth()
    # деякі стекі люблять PBSZ/PROT перед логіном
    ftps.prot_p()                        # (всередині викликає PBSZ 0 і PROT P)
    ftps.login(USER, PASS)
    ftps.set_pasv(True)
    buf = BytesIO()
    ftps.retrbinary(f"RETR {REMOTE}", buf.write)
    print("READ OK (B):", len(buf.getvalue()), "bytes")
    ftps.quit()

if __name__ == "__main__":
    try:
        seq_A()
    except Exception as e:
        print("A failed:", repr(e))
        try:
            seq_B()
        except Exception as e2:
            print("B failed:", repr(e2))
            raise
