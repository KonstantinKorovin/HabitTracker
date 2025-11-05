from django.urls import path
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path("docs/", include_docs_urls(title="API Documentation")),
]
