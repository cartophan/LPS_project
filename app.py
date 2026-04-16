from flask import Flask, redirect, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from dotenv import load_dotenv
from flask import session
from mistralai.client import Mistral

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
app.secret_key = os.getenv("SECRET_KEY")
DOG_API_KEY = os.getenv("DOG_API_KEY")
CAT_API_KEY = os.getenv("CAT_API_KEY")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

client = Mistral(api_key=MISTRAL_API_KEY)
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    favorites = db.relationship("Favorite", backref="user", lazy=True)
    profile = db.relationship("Profile", backref="user", uselist=False)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    activity_level = db.Column(db.String(50))
    home_type = db.Column(db.String(50))
    has_kids = db.Column(db.Boolean)
    pet_type = db.Column(db.String(20))  # dog / cat / both
    has_experience = db.Column(db.Boolean)
    time_available = db.Column(db.String(50))
    budget = db.Column(db.String(50))

class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    pet_name = db.Column(db.String(120))
    pet_type = db.Column(db.String(10))  # dog / cat
    image = db.Column(db.String(300))
    reason = db.Column(db.Text)  # 🔥 объяснение от ИИ

# 1. Главная страница с кнопкой
@app.route("/")
def index():
    return render_template("index.html")


# 2. Редирект на Google
@app.route("/login")
def login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
    )
    return redirect(google_auth_url)


# 3. Callback от Google
@app.route("/callback")
def callback():
    code = request.args.get("code")

    # Обмениваем code на токен
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    token_json = token_response.json()

    access_token = token_json.get("access_token")

    # Получаем инфу о пользователе
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_info = userinfo_response.json()

    email = user_info.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id


    return render_template("success.html", email=user_info.get("email"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    if request.method == "POST":
        activity = request.form.get("activity_level")
        home = request.form.get("home_type")
        kids = request.form.get("has_kids") == "no"
        pet_type = request.form.get("pet_type")

        # 🔥 ищем существующую анкету
        profile = Profile.query.filter_by(user_id=user_id).first()

        if profile:
            # обновляем
            profile.activity_level = activity
            profile.home_type = home
            profile.has_kids = kids
            profile.pet_type = pet_type
        else:
            # создаём новую
            profile = Profile(
                user_id=user_id,
                activity_level=activity,
                home_type=home,
                has_kids=kids,
                pet_type=pet_type
            )
            db.session.add(profile)

        db.session.commit()

        return redirect("/recommend")

    return render_template("profile.html")

@app.route("/recommend")
def recommend():
    import json

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    profile = Profile.query.filter_by(user_id=user_id).first()

    if not profile:
        return redirect("/profile")

    refresh = request.args.get("refresh")

    # 🔥 если НЕ refresh и есть кэш → показываем старое
    if not refresh and session.get("last_recommendations"):
        return render_template(
            "recommend.html",
            pets=session["last_recommendations"]
        )

    # 🔹 1. получаем собак
    dog_res = requests.get(
        "https://api.thedogapi.com/v1/breeds",
        headers={"x-api-key": DOG_API_KEY}
    )
    if dog_res.status_code != 200:
        print("DOG API ERROR:", dog_res.text)
        dogs = []
    else:
        dogs = dog_res.json()

    # 🔹 2. получаем котов
    cat_res = requests.get(
        "https://api.thecatapi.com/v1/breeds",
        headers={"x-api-key": CAT_API_KEY}
    )
    if cat_res.status_code != 200:
        print("CAT API ERROR:", cat_res.text)
        cats = []
    else:
        cats = cat_res.json()

    # 🔹 3. объединяем
    breed_list = []

    if profile.pet_type == "dog":
        for d in dogs[:30]:
            breed_list.append(f"Dog: {d['name']} ({d.get('temperament', '')})")

    elif profile.pet_type == "cat":
        for c in cats[:30]:
            breed_list.append(f"Cat: {c['name']} ({c.get('temperament', '')})")

    else:  # both
        for d in dogs[:30]:
            breed_list.append(f"Dog: {d['name']} ({d.get('temperament', '')})")

        for c in cats[:30]:
            breed_list.append(f"Cat: {c['name']} ({c.get('temperament', '')})")
    dog_breeds_map = {d["name"]: d["id"] for d in dogs}
    cat_breeds_map = {c["name"]: c["id"] for c in cats}

    # 🔥 4. промпт
    prompt = f"""
Ты помощник по подбору питомцев.

Анкета:
- Активность: {profile.activity_level}
- Жильё: {profile.home_type}
- Есть дети: {profile.has_kids}

Выбирай ТОЛЬКО из списка ниже.
{breed_list}

ЗАДАЧА:
1. Выбери ровно 6 лучших вариантов
2. Используй только породы из списка
3. Не придумывай новые
4. Учитывай анкету строго

Если выбран "dog" — выбирай только собак  
Если "cat" — только котов  
Если "both" — можно смешивать

Верни ТОЛЬКО JSON:
[
  {{
    "type": "dog или cat",
    "name": "точное название из списка",
    "reason": "конкретно почему этот питомец подходит именно этому человеку, с учётом его характера и особенностей породы. 1–2 предложения, уникальные для каждой породы",
    "pros": "2-3 плюса",
    "cons": "1-2 минуса"
  }}
]
Каждое описание reason должно быть УНИКАЛЬНЫМ.

НЕ используй одинаковые или шаблонные фразы.

Каждый питомец должен иметь индивидуальное объяснение,
основанное на его особенностях.

Запрещено повторять одну и ту же формулировку.
НЕ ПИШИ ничего кроме JSON
НЕ ПРИДУМЫВАЙ новые породы.
"""

    # 🔹 5. запрос к Mistral
    try:
        chat_response = client.chat.complete(
            model="mistral-small",
            messages=[
                {
                    "role": "system",
                    "content": "Return ONLY valid JSON array."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    except Exception as e:
        print("MISTRAL ERROR:", e)
        return "ИИ сейчас перегружен, попробуйте позже"

    import re
    import json

    result_text = chat_response.choices[0].message.content

    # вытащить только JSON массив из ответа
    match = re.search(r"\[.*\]", result_text, re.S)

    if not match:
        return f"Ошибка ИИ: {result_text}"

    try:
        selected = json.loads(match.group())
    except json.JSONDecodeError:
        return f"Ошибка парсинга JSON: {result_text}"

    dogs = [item for item in selected if item["type"] == "dog"]
    cats = [item for item in selected if item["type"] == "cat"]

    final_selected = []

    half_dogs = min(3, len(dogs))
    half_cats = min(3, len(cats))

    final_selected.extend(dogs[:half_dogs])
    final_selected.extend(cats[:half_cats])

    if len(final_selected) < 6:
        remaining = [x for x in selected if x not in final_selected]
        final_selected.extend(remaining[:6 - len(final_selected)])

    # 🔹 7. получаем картинки
    pets = []

    import re

    for item in final_selected:
        name = item["name"]
        pet_type = item["type"]

        # 🔥 чистим название
        name_clean = re.sub(r"\(.*\)", "", name)
        name_clean = name_clean.replace("Dog:", "").replace("Cat:", "")
        name_clean = name_clean.strip()

        breed_id = None
        search_data = None

        # =========================
        # 🐶 DOG
        # =========================
        if pet_type == "dog":

            search = requests.get(
                "https://api.thedogapi.com/v1/breeds/search",
                headers={"x-api-key": DOG_API_KEY},
                params={"q": name_clean},
                timeout=5
            )

            if search.status_code == 200 and search.text.strip():
                try:
                    search_data = search.json()
                except Exception:
                    print("BAD JSON DOG:", search.text)
                    continue
            else:
                print("API ERROR DOG:", search.status_code, search.text)
                continue

            if isinstance(search_data, list) and len(search_data) > 0:
                breed_id = search_data[0].get("id")

            if not breed_id:
                print("NOT FOUND DOG:", name_clean)
                continue

            res = requests.get(
                "https://api.thedogapi.com/v1/images/search",
                headers={"x-api-key": DOG_API_KEY},
                params={"breed_id": breed_id, "limit": 1}
            )

        # =========================
        # 🐱 CAT
        # =========================
        elif pet_type == "cat":

            search = requests.get(
                "https://api.thecatapi.com/v1/breeds/search",
                headers={"x-api-key": CAT_API_KEY},
                params={"q": name_clean},
                timeout=5
            )

            if search.status_code == 200 and search.text.strip():
                try:
                    search_data = search.json()
                except Exception:
                    print("BAD JSON CAT:", search.text)
                    continue
            else:
                print("API ERROR CAT:", search.status_code, search.text)
                continue

            if isinstance(search_data, list) and len(search_data) > 0:
                breed_id = search_data[0].get("id")

            if not breed_id:
                print("NOT FOUND CAT:", name_clean)
                continue

            res = requests.get(
                "https://api.thecatapi.com/v1/images/search",
                headers={"x-api-key": CAT_API_KEY},
                params={"breed_id": breed_id, "limit": 1}
            )

        else:
            continue

        # =========================
        # 📸 IMAGE RESULT
        # =========================
        data = res.json()

        if data:
            pets.append({
                "name": name_clean,
                "type": "Собака" if pet_type == "dog" else "Кот",
                "image": data[0]["url"],
                "reason": item.get("reason")
            })


    session["last_recommendations"] = pets
    print("PETS:", pets)

    return render_template("recommend.html", pets=pets)

@app.route("/add_favorite", methods=["POST"])
def add_favorite():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")

    fav = Favorite(
        user_id=user_id,
        pet_name=request.form.get("name"),
        pet_type=request.form.get("type"),
        image=request.form.get("image"),
        reason=request.form.get("reason")
    )

    db.session.add(fav)
    db.session.commit()

    return redirect("/favorites")

@app.route("/favorites")
def favorites():
    user_id = session.get("user_id")

    favs = Favorite.query.filter_by(user_id=user_id).all()

    return render_template("favorites.html", pets=favs)

@app.route("/account", methods=["GET", "POST"])
def account():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    profile = Profile.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        profile.activity_level = request.form.get("activity_level")
        profile.home_type = request.form.get("home_type")
        profile.has_kids = request.form.get("has_kids") == "yes"
        profile.pet_type = request.form.get("pet_type")

        db.session.commit()

        return redirect("/recommend")

    return render_template("account.html", profile=profile)

@app.route("/delete_favorite", methods=["POST"])
def delete_favorite():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    fav_id = request.form.get("fav_id")

    fav = Favorite.query.filter_by(id=fav_id, user_id=user_id).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()

    return redirect("/favorites")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(port=5000)