import io, ssl
from ftplib import FTP, FTP_TLS

class ImplicitFTP_TLS(FTP_TLS):
    """FTP over TLS (implicit, порт 990): TLS встановлюється одразу після TCP connect."""
    def connect(self, host='', port=0, timeout=-999):
        if port == 0:
            port = 990
        # звичайний TCP connect
        super().connect(host, port, timeout)
        # моментально обгортаємо контрольний канал TLS
        self.sock = self.context.wrap_socket(self.sock, server_hostname=host)
        # перебудовуємо file-обгортку для readline()
        self.file = self.sock.makefile('r', encoding=self.encoding)
        return self.getwelcome()

class SimpleFTP:
    def __init__(self, host, port, user, password,
                 passive=True, timeout=60, tls=False, implicit_tls=False,
                 verify_tls=True, debug=False):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.passive = passive
        self.timeout = timeout
        self.tls = tls
        self.implicit_tls = implicit_tls
        self.verify_tls = verify_tls
        self.debug = debug

    def _ctx(self):
        if self.verify_tls:
            ctx = ssl.create_default_context()
        else:
            ctx = ssl._create_unverified_context()
            ctx.check_hostname = False
        # можна залишити TLS1.2/1.3 за замовчуванням; якщо треба, розкоментуй:
        # if hasattr(ssl, "TLSVersion"):
        #     ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        return ctx

    def _open(self):
        if not self.tls:
            ftp = FTP()
            if self.debug: ftp.set_debuglevel(2)
            ftp.connect(self.host, self.port, timeout=self.timeout)
            ftp.login(self.user, self.password)
            ftp.set_pasv(self.passive)
            return ftp

        # TLS:
        if self.implicit_tls:
            ftps = ImplicitFTP_TLS(context=self._ctx())
            if self.debug: ftps.set_debuglevel(2)
            ftps.connect(self.host, self.port or 990, timeout=self.timeout)  # тут вже TLS
            ftps.login(self.user, self.password)
            ftps.prot_p()  # шифруємо data-channel
            ftps.set_pasv(self.passive)
            return ftps
        else:
            # Explicit FTPS (21): AUTH TLS -> LOGIN -> PROT P
            ftps = FTP_TLS(context=self._ctx())
            if self.debug: ftps.set_debuglevel(2)
            ftps.connect(self.host, self.port or 21, timeout=self.timeout)
            ftps.auth()
            ftps.login(self.user, self.password)
            ftps.prot_p()
            ftps.set_pasv(self.passive)
            return ftps

    def read_bytes(self, remote_path: str) -> bytes:
        remote_path = remote_path.replace("\\", "/")
        ftp = self._open()
        try:
            bio = io.BytesIO()
            ftp.retrbinary(f"RETR {remote_path}", bio.write)
            return bio.getvalue()
        finally:
            try:
                ftp.quit()
            except Exception:
                ftp.close()
