# 🛍️ SVAS Merch Shop API

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%20%2F%20Motor-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://render.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(15%2F15)-brightgreen?style=flat)](https://github.com/mievvchuk/Svasya_backend)

Сучасний, високопродуктивний асинхронний REST API бекенд для магазину фірмового мерчу **SVAS**. Побудований на базі **FastAPI**, неблокуючого драйвера **Motor (MongoDB)**, **GridFS** для збереження медіафайлів та **JWT (RBAC)** авторизації.

---

## 📑 Зміст

- [✨ Основні можливості](#-основні-можливості)
- [🛠 Технологічний стек](#-технологічний-стек)
- [🗄 Структура бази даних](#-структура-бази-даних-mongodb)
- [👥 Ролі та облікові записи](#-ролі-та-облікові-записи)
- [🚀 Швидкий старт (Локальний запуск)](#-швидкий-старт-локальний-запуск)
- [📡 Довідник API (Endpoints)](#-довідник-api-endpoints)
- [⚙️ Змінні середовища](#️-змінні-середовища-env)
- [🌐 Деплой на Render](#-деплой-на-render-rendercom)
- [🧪 Тестування](#-тестування)

---

## ✨ Основні можливості

- **📦 Каталог мерчу:** Отримання товарів з preview-зображеннями, повним описом та списком варіантів (кольори, розміри, залишки).
- **🔍 Швидкий пошук:** Миттєвий регістронезалежний пошук товарів за назвою та описом (`/api/products?search=...`).
- **🖼️ Збереження та стрімінг зображень:** Завантаження файлів прямо в MongoDB GridFS із потоковою віддачею (`StreamingResponse`).
- **🛒 Оформлення замовлень:**
  - Автоматична валідація наявності товару.
  - Атомарне списання залишків (`stock`) на складі при створенні замовлення.
  - Захист від дублювання позицій в одному замовленні.
  - Підтримка замовлень як зареєстрованими клієнтами, так і гостями.
- **🔐 Рольова модель доступу (RBAC):**
  - Безпечні паролі (`bcrypt`) та JWT Bearer токени.
  - Три рівні доступу: `admin`, `manager`, `customer`.
- **🤝 Підтримка клієнтів:** Публічний ендпоінт для зв'язку з закріпленими менеджерами підтримки.
- **⚙️ Повна адмін-панель:** Керування каталогом (створення/редагування/видалення товарів та варіантів), поповнення складу партіями (`add`) чи перезапис залишків (`set`), керування користувачами.
- **🚀 Хмарна готовність:** Готові конфігурації `render.yaml` та `Procfile` для деплою в один клік на Render.com.

---

## 🛠 Технологічний стек

| Компонент | Технологія | Призначення |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Швидкий асинхронний веб-фреймворк з автогенерацією OpenAPI/Swagger |
| **Server** | [Uvicorn](https://www.uvicorn.org/) | Асинхронний ASGI-сервер стандарту Lightning |
| **Database** | [MongoDB Atlas](https://www.mongodb.com/) / [Motor](https://motor.readthedocs.io/) | Документоорієнтована NoSQL БД + асинхронний драйвер |
| **File Storage** | [GridFS](https://www.mongodb.com/docs/manual/core/gridfs/) | Збереження зображень товарів та варіантів у MongoDB |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Сувора валідація схем даних та налаштувань |
| **Security** | `bcrypt`, `PyJWT` | Хешування паролів та видача безпечних JSON Web Tokens |
| **CORS** | `CORSMiddleware` | Гнучке налаштування для взаємодії з будь-яким фронтендом |

---

## 🗄 Структура бази даних (MongoDB)

База даних `svas` складається з 5 взаємопов'язаних колекцій:

```text
svas
├── products           # Базові картки товарів (назва, опис, категорія, ціна, статус)
├── product_variants   # Варіанти товарів (колір, розмір, залишок stock, посилання на фото)
├── orders             # Замовлення покупців (контакти, статус, загальна сума, список items)
├── users              # Облікові записи (пошта, хеш пароля, телефон, роль, статус)
└── fs.files / chunks  # GridFS бінарні чанки завантажених фотографій мерчу
```

---

## 👥 Ролі та облікові записи

| Роль | Опис прав |
| :--- | :--- |
| **`admin`** | Повний контроль: створення/видалення товарів, коригування складу, призначення ролей користувачам. |
| **`manager`** | Робота із замовленнями: зміна статусів (`new` -> `contacted` -> `processing` -> `completed`), закріплення за замовленням, контакти з клієнтами. |
| **`customer`** | Зареєстрований покупець: перегляд каталогу, створення замовлень, перегляд своєї історії. |
| **Гість** | Анонімний користувач: перегляд товарів, оформлення швидкого замовлення без авторизації. |

### 🔑 Тестові акаунти за замовчуванням:
> [!NOTE]
> Створюються автоматично при першому запуску додатку (якщо відсутні в базі).

- **👑 Головний Адміністратор:**
  - **Email:** `admin@svasya.ua`
  - **Пароль:** `Admin123!`
- **👔 Менеджер підтримки:**
  - **Email:** `manager@svasya.ua`
  - **Пароль:** `Manager123!`
- **🛍️ Тестовий покупець:**
  - **Email:** `real_client@gmail.com`
  - **Пароль:** `SecurePassword123!`

---

## 🚀 Швидкий старт (Локальний запуск)

### 1. Клонування репозиторію

```bash
git clone https://github.com/mievvchuk/Svasya_backend.git
cd Svasya_backend
```

### 2. Налаштування віртуального середовища

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Налаштування `.env`

Створіть файл `.env` у корені проєкту (за зразком `.env.example`):

```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=svas
JWT_SECRET_KEY=svasya-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=*
```

### 5. Початкове наповнення товарами (Seed Data)

Для заповнення бази первинним асортиментом мерчу SVAS (футболки, худі, кепки, шопери, кружки з варіантами та залишками):

```bash
python -m app.products.seed
```

### 6. Запуск сервера розробки

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Після запуску відкрийте браузер:
- 📖 **Інтерактивна документація Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📑 **Альтернативна документація ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- 🩺 **Перевірка працездатності (Health Check):** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📡 Довідник API (Endpoints)

Усі маршрути доступні як із префіксом `/api`, так і напряму.

### 🔐 1. Автентифікація (`/api/auth`)
| Метод | Шлях | Доступ | Опис |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Публічний | Реєстрація нового покупця (`customer`) |
| `POST` | `/api/auth/login` | Публічний | Вхід за email/паролем та отримання Bearer JWT |
| `GET` | `/api/auth/me` | Авторизований | Дані поточного авторизованого користувача |

### 👕 2. Каталог товарів та пошук (`/api/products`)
| Метод | Шлях | Доступ | Опис |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products` | Публічний | Список активних товарів з preview-картинками |
| `GET` | `/api/products?search={text}` | Публічний | Пошук товарів за назвою та описом |
| `GET` | `/api/products/{product_id}` | Публічний | Детальна інформація про товар та всі його варіанти |
| `GET` | `/api/products/image/{image_id}` | Публічний | Стрімінг зображення з GridFS |

### 🛍️ 3. Замовлення (`/api/orders`)
| Метод | Шлях | Доступ | Опис |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/orders` | Публічний / Клієнт | Створення замовлення зі списанням залишків `stock` |
| `GET` | `/api/orders` | Авторизований | Перегляд замовлень (клієнт — свої; менеджер/адмін — усі) |
| `GET` | `/api/orders/{order_id}` | Авторизований | Деталі конкретного замовлення |
| `PATCH`| `/api/orders/{order_id}/status` | `manager`, `admin` | Зміна статусу (`new`, `contacted`, `processing`, `completed`, `cancelled`) |
| `PATCH`| `/api/orders/{order_id}/assign` | `manager`, `admin` | Закріплення менеджера за замовленням |

### 👥 4. Користувачі та підтримка (`/api/users`)
| Метод | Шлях | Доступ | Опис |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/users/managers` | Публічний | Список активних менеджерів для зв'язку з клієнтами |
| `GET` | `/api/users` | `admin` | Список усіх зареєстрованих користувачів |
| `POST` | `/api/users/staff` | `admin` | Створення співробітника (`manager` або `admin`) |
| `PATCH`| `/api/users/{user_id}` | `admin` | Зміна ролі або блокування/активація облікового запису |
| `DELETE`| `/api/users/{user_id}` | `admin` | Видалення користувача |

### ⚙️ 5. Адміністрування каталогу та складу (`/api/products`)
| Метод | Шлях | Доступ | Опис |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/products` | `admin` | Додавання нового товару в каталог |
| `PATCH`| `/api/products/{product_id}` | `admin` | Редагування назви, опису, ціни, наявності |
| `DELETE`| `/api/products/{product_id}` | `admin` | Видалення товару разом з усіма варіантами |
| `POST` | `/api/products/{product_id}/variants` | `admin` | Додавання варіанта товару (колір, розмір, залишок) |
| `PATCH`| `/api/products/variants/{variant_id}/stock` | `admin` | Поповнення залишку: `add` (додати) або `set` (встановити) |
| `DELETE`| `/api/products/variants/{variant_id}` | `admin` | Видалення варіанта товару |
| `POST` | `/api/products/{product_id}/image` | `admin` | Завантаження зображення в GridFS для товару чи варіанта |

---

## ⚙️ Змінні середовища (.env)

| Змінна | Тип | За замовчуванням | Опис |
| :--- | :---: | :---: | :--- |
| `MONGODB_URL` | `str` | *Обов'язкова* | Повний рядок підключення до MongoDB (Atlas або локальна) |
| `MONGODB_DATABASE` | `str` | `svas` | Назва робочої бази даних |
| `JWT_SECRET_KEY` | `str` | `svasya-secret-jwt-key...` | Секретний ключ для підпису JWT токенів |
| `JWT_ALGORITHM` | `str` | `HS256` | Алгоритм шифрування токенів |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `1440` (24 год) | Час життя токена до повторної авторизації |
| `CORS_ORIGINS` | `str` / `list` | `*` | Дозволені адреси фронтенду (наприклад, `http://localhost:3000,https://svasya.ua`) |

---

## 🌐 Деплой на Render (Render.com)

Проєкт містить готові конфігураційні файли `render.yaml` та `Procfile`.

### Варіант А: Через Blueprint (Рекомендовано — 2 хвилини)
1. Увійдіть у [Render Dashboard](https://dashboard.render.com/) під своїм GitHub акаунтом.
2. Натисніть **New +** ➡️ **Blueprint**.
3. Оберіть репозиторій **`mievvchuk/Svasya_backend`**.
4. Render автоматично застосує налаштування з `render.yaml`.
5. У формі введіть значення для `MONGODB_URL`.
6. Натисніть **Apply**.

### Варіант Б: Вручну як Web Service
1. Натисніть **New +** ➡️ **Web Service**.
2. Підключіть репозиторій `Svasya_backend`.
3. Заповніть параметри:
   - **Environment:** `Python`
   - **Region:** `Frankfurt (EU Central)`
   - **Branch:** `main` (або `develop`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Free`
4. Додайте **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.9`
   - `MONGODB_URL`: *ваш рядок підключення Atlas*
   - `MONGODB_DATABASE`: `svas`
   - `JWT_SECRET_KEY`: *довільний надійний секретний ключ*
   - `CORS_ORIGINS`: `*`
5. Вкажіть **Health Check Path:** `/health`.
6. Натисніть **Create Web Service**.

---

## 🧪 Тестування

Для проєкту реалізовано повний набір модульних тестів (каталог, пошук, списання залишків, валідація, ролі та адміністрування):

```bash
python -m unittest discover tests
```

Результат виконання:
```text
...............
----------------------------------------------------------------------
Ran 15 tests in 3.4s

OK
```

---

## 📄 Ліцензія

Цей проєкт створено для магазину **SVAS**. Всі права захищено.
