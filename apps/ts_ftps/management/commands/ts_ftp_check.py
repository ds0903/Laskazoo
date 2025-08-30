# apps/ts_ftps/management/commands/ts_ftp_check.py
from django.core.management.base import BaseCommand
import socket
from apps.ts_ftps.utils import get_reader

class Command(BaseCommand):
    help = "Перевірка FTP/FTPS підключення та доступу до файлу"

    def add_arguments(self, parser):
        parser.add_argument('--path', default=None, help='Каталог на FTP (наприклад /incoming)')
        parser.add_argument('--file', default=None, help='Імʼя файлу (наприклад TSGoods.trs)')

    def handle(self, *args, **opts):
        mode, client, incoming_dir, _ph, file_name = get_reader()
        if opts['path']:
            incoming_dir = opts['path']
        if opts['file']:
            file_name = opts['file']

        remote = f"{incoming_dir.rstrip('/')}/{file_name}"
        self.stdout.write(f"Mode: {mode}")
        self.stdout.write(f"Remote path: {remote}")
        self.stdout.write(f"Host: {getattr(client, 'host', 'n/a')}, Port: {getattr(client, 'port', 'n/a')}")

        # сирий TCP
        try:
            s = socket.create_connection((client.host, client.port), timeout=8)
            s.close()
            self.stdout.write(self.style.SUCCESS("TCP connect OK"))
        except Exception as se:
            self.stderr.write(self.style.ERROR(f"TCP connect FAIL: {se}"))
            return

        # спроба читання файла
        try:
            data = client.read_bytes(remote)
            self.stdout.write(self.style.SUCCESS(f"OK: прочитано {len(data)} байт з {remote}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"ERROR: {e.__class__.__name__}: {e}"))
            self.stderr.write("Провір: TS_FTP_INCOMING_DIR, назву файлу, права доступу, пасивний режим.")
