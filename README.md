# SVAS Shop API

Сучасний асинхронний backend для магазину мерчу SVAS на базі **FastAPI** та **MongoDB (Motor)**.

## 🛠 Технологічний стек

- **Мова:** Python 3.11+
- **Фреймворк:** FastAPI
- **База даних:** MongoDB (асинхронний драйвер `motor`, `pymongo`)
- **Валідація та налаштування:** Pydantic v2, `pydantic-settings`, `email-validator`
- **Безпека та авторизація:** `bcrypt`, `pyjwt` (JWT Bearer токени)
- **CORS:** Налаштовано для безперешкодної інтеграції з фронтендом

---

## 🚀 Швидкий старт

### 1. Клонування та перехід у гілку

```powershell
git checkout feature/users-and-roles
```

### 2. Створення та активація віртуального середовища

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Встановлення залежностей

```powershell
pip install -r requirements.txt
```

### 4. Налаштування змінних середовища

Створіть файл `.env` у корені проєкту (або перевірте наявний):

```env
MONGODB_URL=mongodb+srv://...
MONGODB_DATABASE=svas
```

### 5. Початкове заповнення товарами (Seed)

```powershell
python -m app.products.seed
```

### 6. Запуск сервера

```powershell
uvicorn app.main:app --reload
```

Після запуску документація Swagger UI доступна за адресою:
👉 **http://127.0.0.1:8000/docs**

---

## 👥 Ролі та облікові записи

Система підтримує 3 ролі користувачів:
1. **`admin`** — повний доступ (керування товарами, призначення персоналу, перегляд замовлень).
2. **`manager`** — служба підтримки та обробки замовлень (зв'язок із клієнтами, зміна статусів замовлень, закріплення за замовленнями).
3. **`customer`** — зареєстрований покупець (створення замовлень, перегляд власної історії). Замовлення також можна оформлювати як **гість** (без реєстрації).

### 🔑 Тестові акаунти (створюються автоматично при запуску):
- **Адміністратор:**
  - Email: `admin@svasya.ua`
  - Пароль: `Admin123!`
- **Менеджер для зв'язку:**
  - Email: `manager@svasya.ua`
  - Пароль: `Manager123!`

---

## 🗄 Структура бази даних (MongoDB Collections)

- **`products`** — типи товарів (`id`, `name`, `description`, `category`, `price`, `is_available`, `created_at`).
- **`product_variants`** — конкретні варіанти (`id`, `product_id`, `color`, `size`, `image_url`, `stock`).
- **`orders`** — замовлення клієнтів (`id`, `customer_name`, `phone`, `email`, `total_price`, `status`, `created_at`, `user_id`, `assigned_manager_id`, `items[]`).
- **`users`** — користувачі системи (`id`, `email`, `hashed_password`, `name`, `phone`, `role`, `is_active`, `created_at`).

---

## 📡 Основні API Endpoints

### 1. Каталог товарів (Backend 1)
- `GET /api/products` — список доступних товарів з preview-зображенням.
- `GET /api/products/{id}` — детальна інформація про товар з усіма доступними варіантами.

### 2. Замовлення (Backend 2)
- `POST /api/orders` — створення замовлення (з автоматичною перевіркою та **списанням залишків `stock`**, перевіркою доступності товару, захистом від дублів).
- `GET /api/orders` — перегляд замовлень (покупець бачить свої замовлення; менеджер/адмін бачать усі).
- `GET /api/orders/{id}` — деталі конкретного замовлення.
- `PATCH /api/orders/{id}/status` — зміна статусу (`new`, `contacted`, `processing`, `completed`, `cancelled`) — *Manager/Admin*.
- `PATCH /api/orders/{id}/assign` — закріплення менеджера для зв'язку — *Manager/Admin*.

### 3. Користувачі та зв'язок
- `POST /api/auth/register` — реєстрація нового покупця.
- `POST /api/auth/login` — вхід та отримання JWT Bearer токена.
- `GET /api/auth/me` — інформація про поточного користувача.
- `GET /api/users/managers` — **публічний список менеджерів для зв'язку** (ім'я, телефон, пошта).
- `POST /api/users/staff` — створення адміном нового менеджера чи адміна.

### 4. Адмін-панель (Тільки для ролі `admin`)
- `POST /api/products` — створення нового товару.
- `PATCH /api/products/{id}` — оновлення ціни, опису або перемикання доступності (`is_available`).
- `DELETE /api/products/{id}` — видалення товару та його варіантів.
- `POST /api/products/{id}/variants` — додавання нового варіанта товару (колір, розмір, картинка, залишок).
- `PATCH /api/products/variants/{variant_id}/stock` — **поповнення наявності / коригування залишків на складі** (режими `set` для встановлення або `add` для додавання нової партії).
- `DELETE /api/products/variants/{variant_id}` — видалення варіанта товару.
- `GET /api/users` — список усіх користувачів із фільтрацією за роллю (`customer`, `manager`, `admin`) та статусом.
- `PATCH /api/users/{id}` — зміна ролі користувача або деактивація акаунта.
- `DELETE /api/users/{id}` — видалення користувача.

---

## 🧪 Тестування

Для запуску всіх автоматизованих тестів виконайте:

```powershell
python -m unittest discover tests
```

---

## 🌐 Деплой на Render (Render.com)

Проєкт повністю налаштовано для швидкого безкоштовного деплою на **Render**.

### Варіант 1: Через Blueprint (Автоматично)
1. У панелі [Render Dashboard](https://dashboard.render.com/) натисніть **New +** -> **Blueprint**.
2. Підключіть репозиторій `mievvchuk/Svasya_backend`.
3. Render автоматично прочитає файл `render.yaml`.
4. Введіть змінну оточення `MONGODB_URL` (ваше підключення до MongoDB Atlas).
5. Натисніть **Apply**.

### Варіант 2: Вручну (New Web Service)
1. У Render виберіть **New +** -> **Web Service**.
2. Підключіть репозиторій `Svasya_backend`.
3. Задайте налаштування:
   - **Environment:** `Python`
   - **Region:** `Frankfurt (EU Central)`
   - **Branch:** `develop` (або `main`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Додайте **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.9`
   - `MONGODB_URL`: `mongodb+srv://...` (ваша адреса бази Atlas)
   - `MONGODB_DATABASE`: `svas`
   - `JWT_SECRET_KEY`: (випадковий секретний ключ)
   - `CORS_ORIGINS`: `*` (або адреса вашого фронтенду)
5. **Health Check Path:** `/health`
6. Натисніть **Create Web Service**.

Після завершення білду ваш бекенд буде доступний онлайн з автоматичним SSL-сертифікатом (HTTPS) та Swagger UI за адресою `https://<ваша-назва>.onrender.com/docs`!

