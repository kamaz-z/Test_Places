# Places Service

## Що було зроблено

- Додано браузерну сторінку для перевірки API за адресою `/`: перегляд і пошук
  місць, перегляд та створення категорій, реєстрація, вхід і створення місць.
- Налаштовано маршрути API для місць, категорій, відгуків та експорту. Усунуто
  дубльовані URL-префікси, через які запити повертали `404`.
- Спільний дозвіл власника/адміністратора винесено в `core.permissions`.
  Анонімні користувачі можуть читати місця, авторизовані — створювати їх,
  редагувати й видаляти власні.
- Для списку місць додано фільтри за категорією, автором і рейтингом, пошук за
  назвою/описом, сортування та пагінацію. Додано кеш списку з розділенням за
  параметрами запиту й інвалідацією після змін місць, відгуків і категорій.
- Додано підрахунок переглядів із лімітом одного перегляду на користувача за годину та показ популярності на основі рейтингу, відгуків і переглядів
  за останні 7 днів. Є команда очищення старих записів переглядів.
- Експорт місць підтримує JSON і CSV, використовує ті самі фільтри й пошук та
  нейтралізує формули в CSV.
- Додано відсутні міграції місць і відгуків, виправлено конфлікти назв
  тестових файлів/пакетів, зареєстровано категорії в Django admin.
- Налаштовано Docker Compose для Django, PostgreSQL і Redis; PostgreSQL та Redis
  доступні з локального комп’ютера на `127.0.0.1:5433` і `127.0.0.1:6379`.

## Запуск через Docker Compose

Створи `.env` з `.env.example`, заміни секретний ключ і пароль БД на власні,
потім із кореня проєкту виконай:

```powershell
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Сайт: `http://localhost:8000/`. Django admin: `http://localhost:8000/admin/`.
Увійди як superuser, щоб створювати категорії; категорія потрібна для
створення місця. `docker compose down` зупиняє сервіси, але залишає дані в
Docker volume `postgres_data`.

## Локальний запуск Django

Compose опубліковує PostgreSQL та Redis на localhost. Запусти залежності:

```powershell
docker compose up -d db redis
```

В іншому PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Відкрий `http://127.0.0.1:8000/`. pgAdmin підключай до `127.0.0.1:5433`;
назва БД і облікові дані — зі свого `.env`.

## Перевірки й обслуговування

```powershell
docker compose exec web python manage.py test
docker compose exec web python manage.py cleanup_place_views
docker compose exec web python manage.py cleanup_place_views --days 14
```

Очищення переглядів за замовчуванням видаляє записи старші за 30 днів.
Мінімально дозволений строк — 7 днів, відповідно до вікна популярності.
