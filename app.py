"""Лендинг PEcf08 на Flask: страница, форма заявок, простая админка.

Ассистент на сайт не встроен: он отвечает в Telegram.
"""

import logging
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

import config

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / config.DATABASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
csrf = CSRFProtect(app)

TOPICS = [
    ("Типовые ответы", "Типовые ответы"),
    ("Заявки", "Заявки"),
    ("Следующий шаг", "Следующий шаг"),
    ("Порядок в сделках", "Порядок в сделках"),
    ("Первая линия", "Первая линия"),
    ("Другое", "Другое"),
]


class ContactForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(message="Укажите имя"), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(message="Укажите email"), Email(message="Некорректный email")])
    phone = StringField("Телефон", validators=[Optional(), Length(max=40)])
    topic = SelectField("Тема сообщения", choices=[("", "Выберите тему")] + TOPICS, validators=[DataRequired(message="Выберите тему")])
    message = TextAreaField(
        "Сообщение",
        validators=[
            DataRequired(message="Напишите сообщение"),
            Length(min=10, max=1000, message="От 10 до 1000 символов"),
        ],
    )


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            topic TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.commit()
    db.close()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


def bot_context():
    return {
        "bot_url": config.TELEGRAM_BOT_URL,
        "bot_handle": config.TELEGRAM_BOT_HANDLE,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    form = ContactForm()
    if form.validate_on_submit():
        db = get_db()
        db.execute(
            "INSERT INTO leads (name, email, phone, topic, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                form.name.data.strip(),
                form.email.data.strip(),
                (form.phone.data or "").strip(),
                form.topic.data,
                form.message.data.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        db.commit()
        logger.info("Новая заявка: %s / %s", form.name.data, form.email.data)
        flash("Заявка записана. Это учебный прототип: письмо на почту не уходит, запись лежит в SQLite.", "ok")
        return redirect(url_for("index", _anchor="contact"))
    if request.method == "POST":
        logger.info("Форма не прошла проверку")
    return render_template("index.html", form=form, **bot_context())


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin"))
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == config.ADMIN_USERNAME and form.password.data == config.ADMIN_PASSWORD:
            session["admin"] = True
            logger.info("Вход в админку")
            return redirect(url_for("admin"))
        flash("Неверный логин или пароль.", "error")
    return render_template("admin_login.html", form=form)


@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    leads = db.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    total = len(leads)
    unread = sum(1 for row in leads if not row["is_read"])
    return render_template("admin.html", leads=leads, total=total, unread=unread, read=total - unread)


@app.post("/admin/leads/<int:lead_id>/read")
@admin_required
def mark_read(lead_id):
    get_db().execute("UPDATE leads SET is_read = 1 WHERE id = ?", (lead_id,))
    get_db().commit()
    return redirect(url_for("admin"))


@app.post("/admin/leads/<int:lead_id>/delete")
@admin_required
def delete_lead(lead_id):
    get_db().execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    get_db().commit()
    return redirect(url_for("admin"))


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    logger.info("Приложение запущено")
    app.run(debug=False, host="127.0.0.1", port=5050)
