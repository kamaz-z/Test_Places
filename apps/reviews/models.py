from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Count, Q

from core.models import TimeStampedModel


class VoteValue(models.IntegerChoices):
    LIKE = 1, 'Like'
    DISLIKE = -1, 'Dislike'


class ReviewQuerySet(models.QuerySet):
    def with_vote_counts(self):
        return self.annotate(
            likes_count=Count('votes', filter=Q(votes__value=VoteValue.LIKE)),
            dislikes_count=Count('votes', filter=Q(votes__value=VoteValue.DISLIKE)),
        )

    def for_active_places(self):
        return self.filter(place__deleted_at__isnull=True)


class Review(TimeStampedModel):
    place = models.ForeignKey('places.Place', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'place'], name='unique_review_per_author_place'
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5),
                name='review_rating_between_1_and_5',
            ),
        ]

    def __str__(self):
        return f'{self.author} -> {self.place} ({self.rating})'


class ReviewVote(TimeStampedModel):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_votes'
    )
    value = models.SmallIntegerField(choices=VoteValue.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'review'], name='unique_vote_per_user_review'
            ),
            models.CheckConstraint(
                condition=Q(value__in=[1, -1]), name='review_vote_value_valid'
            ),
        ]