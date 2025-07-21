

from rest_framework.pagination import PageNumberPagination

class AutoCompleteResultsSetPagination(PageNumberPagination):
    search = ""
