from .cache import invalidate_places_list
from .models import Place


def create_place(*, author, **data) -> Place:
    place = Place.objects.create(author=author, **data)
    invalidate_places_list()
    return place


def update_place(place: Place, **data) -> Place:
    for field, value in data.items():
        setattr(place, field, value)
    place.save()
    invalidate_places_list()
    return place


def delete_place(place: Place) -> None:
    place.delete()  # soft delete
    invalidate_places_list()