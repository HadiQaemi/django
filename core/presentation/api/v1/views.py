import os
from django.conf import settings
from django.http import FileResponse, JsonResponse, Http404


def custom_serve_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(open(file_path, "rb"))

    # Customize 404 response (JSON style)
    return JsonResponse({"error": "Media file not found", "path": path}, status=404)
