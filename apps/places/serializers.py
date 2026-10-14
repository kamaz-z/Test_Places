from rest_framework import serializers

from apps.categories.serializers import CategorySerializer

from .models import Place


class RoundedFloatField(serializers.FloatField):
    def to_representation(self, value):
        return round(float(value), 2)


class PlaceSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)
    avg_rating = RoundedFloatField(read_only=True)
    reviews_count = serializers.IntegerField(read_only=True)
    views_7d = serializers.IntegerField(read_only=True)
    popularity = RoundedFloatField(read_only=True)

    class Meta:
        model = Place
        fields = (
            'id', 'title', 'description', 'category', 'category_detail',
            'address', 'latitude', 'longitude', 'author',
            'avg_rating', 'reviews_count', 'views_7d', 'popularity',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')