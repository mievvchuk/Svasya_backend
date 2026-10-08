# SVAS Shop API

Базовий backend для магазину мерчу на FastAPI та MongoDB.

## Технології

- Python
- FastAPI
- MongoDB
- синхронний PyMongo
- Pydantic
- python-dotenv

## Підготовка

Створіть віртуальне середовище:

```powershell
python -m venv .venv
```

Активуйте його у Windows:

```powershell
.venv\Scripts\activate
```

Встановіть залежності:

```powershell
pip install -r requirements.txt
```

Створіть `.env` на основі `.env.example` і за потреби змініть параметри
підключення до MongoDB.

## Запуск

```powershell
uvicorn app.main:app --reload
```

Після запуску Swagger доступний за адресою:

http://127.0.0.1:8000/docs

## MongoDB collections

MVP використовує дві основні collections:

```text
products
└── variants[]

orders
└── items[]
```

`variants` зберігаються всередині документа `Product`, а `items` — всередині
документа `Order`. Окремі collections для них не потрібні. MongoDB створить
collections `products` і `orders` під час першого запису даних.

Endpoint-и products та orders наразі є заготовками й повертають
`501 Not Implemented`. Бізнес-логіка буде реалізована у відповідних
feature-гілках.
