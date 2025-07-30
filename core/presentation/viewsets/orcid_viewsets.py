import os
import requests
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache

User = get_user_model()


class OrcidInitiateView(APIView):
    def get(self, request):
        url = request.GET.get("url")
        form = request.GET.get("form")
        state = request.GET.get("state")
        cache.set(state, {"url": url, "form": form}, timeout=60)
        params = {
            "client_id": os.environ.get("ORCID_CLIENT_ID"),
            "response_type": "code",
            "scope": "/authenticate",
            "redirect_uri": os.environ.get("ORCID_CALLBACK_URL"),
            "state": state,
        }
        url = f"https://orcid.org/oauth/authorize?{urlencode(params)}"
        return redirect(url)


class OrcidCallbackView(APIView):
    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        res = cache.get(state)

        if not code:
            return Response({"error": "No code provided"}, status=400)

        frontend_url = f"{res['url']}?code={code}&state={state}&form={res['form']}"
        return redirect(frontend_url)


class OrcidTokenExchangeView(APIView):
    def post(self, request):
        code = request.data.get("code")
        print("---------OrcidTokenExchangeView----------")
        if not code:
            return Response({"error": "Missing code"}, status=400)

        token_res = requests.post(
            "https://orcid.org/oauth/token",
            data={
                "client_id": os.environ.get("ORCID_CLIENT_ID"),
                "client_secret": os.environ.get("ORCID_CLIENT_SECRET"),
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": os.environ.get("ORCID_CALLBACK_URL"),
            },
        )

        if token_res.status_code != 200:
            return Response({"error": "Token exchange failed"}, status=400)

        token_data = token_res.json()
        orcid_id = token_data["orcid"]
        name = token_data["name"]

        user, created = User.objects.get_or_create(
            orcid_id=orcid_id,
            defaults={"name": name},
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "token": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {"name": name, "orcid_id": orcid_id},
            }
        )
