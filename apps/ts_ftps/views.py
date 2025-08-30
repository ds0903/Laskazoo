from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .services import import_from_source

def _ok_token(request):
    return request.headers.get("X-TS-Token") == settings.TS_SYNC.get("INBOUND_TOKEN")

class TorgsoftNotifyView(APIView):
    """
    Торгсофт може викликати POST на цей ендпойнт після своєї синхронізації.
    Ми відразу зчитаємо файл з /incoming і оновимо БД.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if not _ok_token(request):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        res = import_from_source()
        return Response({"status": "ok", "result": res}, status=status.HTTP_200_OK)
