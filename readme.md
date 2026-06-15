# 🐾 LPS — Love Pet Selector

LPS (Love Pet Selector) — интеллектуальная система подбора домашних питомцев с использованием искусственного интеллекта.

Пользователь проходит авторизацию через Google, заполняет анкету о своем образе жизни и предпочтениях, после чего AI анализирует ответы и предлагает наиболее подходящих кошек и собак.

---

## ✨ Возможности

* 🔐 Авторизация через Google OAuth 2.0
* 👤 Персональный профиль пользователя
* 🤖 Подбор питомцев с помощью Mistral AI
* 🐶 Интеграция с TheDogAPI
* 🐱 Интеграция с TheCatAPI
* ⭐ Сохранение питомцев в избранное
* 🔄 Обновление рекомендаций
* 📝 Анализ совместимости пользователя и питомца
* 🗄 Хранение данных в PostgreSQL
* 🎨 Современный пользовательский интерфейс на HTML/CSS

---

## 🛠 Используемые технологии

### Backend

* Python
* Flask
* SQLAlchemy
* PostgreSQL
* Google OAuth 2.0

### AI

* Mistral AI API

### External APIs

* TheDogAPI
* TheCatAPI

### Frontend

* HTML5
* CSS3
* Jinja2 Templates

---

## 📂 Структура проекта

LPS_project/

├── app.py

├── .env

├── requirements.txt

├── templates/

│ ├── index.html

│ ├── success.html

│ ├── profile.html

│ ├── recommend.html

│ └── favorites.html

├── static/

│ ├── style.css

│ └── logo.png

└── README.md

---

## ⚙️ Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your-username/LPS_project.git
cd LPS_project
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
```

### 3. Активировать окружение

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

---

## 🔑 Настройка .env

Создайте файл `.env`:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE

CLIENT_ID=google_client_id
CLIENT_SECRET=google_client_secret
REDIRECT_URI=http://localhost:5000/callback

DOG_API_KEY=your_dog_api_key
CAT_API_KEY=your_cat_api_key

MISTRAL_API_KEY=your_mistral_api_key
```

---

## ▶️ Запуск проекта

```bash
python app.py
```

После запуска приложение будет доступно по адресу:

```text
http://localhost:5000
```

---

## 🤖 Как работает подбор

1. Пользователь входит через Google.
2. Заполняет анкету.
3. Система получает список пород кошек и собак через API.
4. Ответы анкеты и характеристики пород отправляются в Mistral AI.
5. ИИ выбирает наиболее подходящих питомцев.
6. Пользователь получает персональную подборку.
7. Понравившихся питомцев можно добавить в избранное.

---

## 📊 База данных

Основные сущности:

### User

* id
* email

### Profile

* user_id
* pet_type
* activity_level
* housing_type
* experience
* family_status

### Favorite

* user_id
* pet_name
* pet_type
* image
* reason

---

## 🚀 Возможности для развития

* Система лайков и рейтингов
* История подборов
* Поиск питомцев по фильтрам
* Административная панель
* Интеграция с приютами животных
* Поддержка нескольких языков

---

## 👩‍💻 Автор

Проект разработан в рамках учебной работы по дисциплине, связанной с разработкой веб-приложений и использованием технологий искусственного интеллекта.
