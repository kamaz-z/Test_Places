from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from apps.places.mixins import PlaceQueryMixin

from . import services


class PlaceExportView(PlaceQueryMixin, GenericAPIView):
    permission_classes = [AllowAny]  # читання публічне, як і список
    pagination_class = None

    def get(self, request):
        file_type = request.query_params.get('file_type', 'json').lower()
        if file_type not in ('json', 'csv'):
            raise ValidationError({'file_type': 'Use "json" or "csv".'})

        df = services.places_to_dataframe(self.filter_queryset(self.get_queryset()))

        if file_type == 'csv':
            content, content_type = services.to_csv_bytes(df), 'text/csv; charset=utf-8'
        else:
            content, content_type = services.to_json_bytes(df), 'application/json'

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="places.{file_type}"'
        return response