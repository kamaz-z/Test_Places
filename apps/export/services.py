import pandas as pd
from django.db.models import F

MAX_EXPORT_ROWS = 10_000

COLUMNS = [
    'id', 'title', 'description', 'category_name', 'address', 'latitude', 'longitude',
    'author_username', 'avg_rating', 'reviews_count', 'views_7d', 'popularity',
    'created_at', 'updated_at',
]
TEXT_COLUMNS = ['title', 'description', 'category_name', 'address', 'author_username']


def places_to_dataframe(queryset) -> pd.DataFrame:
    rows = queryset.values(
        'id', 'title', 'description', 'address', 'latitude', 'longitude',
        'avg_rating', 'reviews_count', 'views_7d', 'popularity', 'created_at', 'updated_at',
        category_name=F('category__name'),
        author_username=F('author__username'),
    )[:MAX_EXPORT_ROWS]
    df = pd.DataFrame.from_records(list(rows), columns=COLUMNS)
    df[['latitude', 'longitude']] = df[['latitude', 'longitude']].astype(float)
    df[['avg_rating', 'popularity']] = df[['avg_rating', 'popularity']].astype(float).round(2)
    return df


def _neutralize(value):
    """Defence against CSV formula injection when opened in Excel."""
    if isinstance(value, str) and value[:1] in ('=', '+', '-', '@'):
        return "'" + value
    return value


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    safe = df.copy()
    for col in TEXT_COLUMNS:
        safe[col] = safe[col].map(_neutralize)
    return safe.to_csv(index=False).encode('utf-8-sig')  # BOM, щоб Excel читав кирилицю


def to_json_bytes(df: pd.DataFrame) -> bytes:
    return df.to_json(orient='records', date_format='iso', force_ascii=False).encode('utf-8')