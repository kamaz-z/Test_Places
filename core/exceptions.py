from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Conflict.'
    default_code = 'conflict'


class DuplicateReviewError(ConflictError):
    default_detail = 'You have already reviewed this place.'
    default_code = 'duplicate_review'


class DuplicateVoteError(ConflictError):
    default_detail = 'You have already voted on this review.'
    default_code = 'duplicate_vote'