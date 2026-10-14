from django.db.models import F
from rest_framework.filters import OrderingFilter


class NullsLastOrderingFilter(OrderingFilter):
    """Ordering where NULL values (e.g. no rating yet) always go last."""

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset
        exprs = []
        for field in ordering:
            expr = F(field.lstrip('-'))
            exprs.append(
                expr.desc(nulls_last=True) if field.startswith('-') else expr.asc(nulls_last=True)
            )
        return queryset.order_by(*exprs, '-id')  # '-id' = стабільна пагінація