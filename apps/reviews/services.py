from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied

from apps.places.cache import invalidate_places_list
from core.exceptions import DuplicateReviewError, DuplicateVoteError

from .models import Review, ReviewVote, VoteValue


def create_review(*, author, place, **data) -> Review:
    try:
        with transaction.atomic():
            review = Review.objects.create(author=author, place=place, **data)
    except IntegrityError:
        raise DuplicateReviewError
    invalidate_places_list()  # змінились rating / reviews_count / popularity
    return review


def update_review(review: Review, **data) -> Review:
    for field, value in data.items():
        setattr(review, field, value)
    review.save()
    invalidate_places_list()
    return review


def delete_review(review: Review) -> None:
    review.delete()
    invalidate_places_list()


def vote_review(*, user, review: Review, value: str) -> ReviewVote:
    if review.author_id == user.id:
        raise PermissionDenied('You cannot vote on your own review.')
    try:
        with transaction.atomic():
            return ReviewVote.objects.create(
                review=review, user=user, value=VoteValue[value.upper()]
            )
    except IntegrityError:
        raise DuplicateVoteError