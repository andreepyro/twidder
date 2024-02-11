import datetime
import sqlite3

from flask import g

DATABASE_FILE = "./database.db"
DATABASE_SCHEMA = "./twidder/schema.sql"


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect(DATABASE_FILE)
    return db


def disconnect_db():
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
        g.db = None
    return db


def initialize_database():
    with open(DATABASE_SCHEMA, "r") as schema_file:
        get_db().executescript(schema_file.read())
        get_db().commit()


def create_user(email: str, password: str, firstname: str, lastname: str, gender: str, city: str, country: str, image: bytes) -> bool:
    try:
        get_db().execute("insert into user (email, password, firstname, lastname, gender, city, country, image) values (?, ?, ?, ?, ?, ?, ?, ?)",
                         [email, password, firstname, lastname, gender, city, country, image])
        get_db().commit()
        return True
    except Exception:
        return False


def get_user_by_email(email: str) -> None | dict:
    cursor = get_db().execute("select email, password, firstname, lastname, gender, city, country, image from user where email==?", [email])
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return {
        'email': rows[0][0],
        'password': rows[0][1],
        'firstname': rows[0][2],
        'lastname': rows[0][3],
        'gender': rows[0][4],
        'city': rows[0][5],
        'country': rows[0][6],
        'image': rows[0][7]
    }


def update_user_by_email(curr_email: str, email: str, password: str, firstname: str, lastname: str, gender: str, city: str, country: str, image: bytes) -> bool:
    try:
        get_db().execute("update user set email=?, password=?, firstname=?, lastname=?, gender=?, city=?, country=?, image=? where email==?",
                         [email, password, firstname, lastname, gender, city, country, image, curr_email])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_user_by_email(email: str) -> bool:
    try:
        get_db().execute("delete from user where email==?", [email])
        get_db().commit()
        return True
    except Exception:
        return False


def create_post(author: str, user: str, content: str, created: datetime.datetime, edited: datetime.datetime) -> int:
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("insert into post (author, user, content, created, edited) values (?, ?, ?, ?, ?)", [author, user, content, created, edited])
        db.commit()
        return cursor.lastrowid
    except Exception:
        return -1


def get_post_by_id(post_id: str) -> None | dict:
    cursor = get_db().execute("select id, author, user, content, created, edited from post where id==?", [post_id])
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return {
        'id': rows[0][0],
        'author': rows[0][1],
        'user': rows[0][2],
        'content': rows[0][3],
        'created': rows[0][4],
        'edited': rows[0][5]
    }


def list_post() -> list[dict]:
    cursor = get_db().execute("select id, author, user, content, created, edited from post")
    rows = cursor.fetchall()
    return [{'id': row[0],
             'author': row[1],
             'user': row[2],
             'content': row[3],
             'created': row[4],
             'edited': row[5]
             } for row in rows]


def list_posts_by_user(email: str) -> list[dict]:
    cursor = get_db().execute("select id, author, user, content, created, edited from post where user==?", [email])
    rows = cursor.fetchall()
    return [{'id': row[0],
             'author': row[1],
             'user': row[2],
             'content': row[3],
             'created': row[4],
             'edited': row[5]
             } for row in rows]


def list_posts_by_author(email: str) -> list[dict]:
    cursor = get_db().execute("select id, author, user, content, created, edited from post where author==?", [email])
    rows = cursor.fetchall()
    return [{'id': row[0],
             'author': row[1],
             'user': row[2],
             'content': row[3],
             'created': row[4],
             'edited': row[5]
             } for row in rows]


def update_post_by_id(post_id: str, author: str, user: str, content: str, created: datetime.datetime, edited: datetime.datetime) -> bool:
    try:
        get_db().execute("update post set author=?, user=?, content=?, created=?, edited=? where id==?", [author, user, content, created, edited, post_id])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_post_by_id(post_id: str) -> bool:
    try:
        get_db().execute("delete from post where id==?", [post_id])
        get_db().commit()
        return True
    except Exception:
        return False
