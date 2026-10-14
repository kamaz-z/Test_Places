from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    dislikes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'place', 'author', 'rating', 'comment',
            'likes_count', 'dislikes_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'place', 'created_at', 'updated_at')


class VoteSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=['like', 'dislike'])