import sqlite3

from flask import g

DATABASE_FILE = "./backend/database.db"
DATABASE_SCHEMA = "./backend/schema.sql"


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


# ------------------------------------------------USER-------------------------------------------------------------------------------
def retrieve_user(email):
    cursor = get_db().execute("select email, password, firstname, familyname, gender, city, country, image from user where email==?", [email])
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return {
        'email': rows[0][0],
        'password': rows[0][1],
        'firstname': rows[0][2],
        'familyname': rows[0][3],
        'gender': rows[0][4],
        'city': rows[0][5],
        'country': rows[0][6],
        'image': rows[0][7]
    }


def create_user(email, password, firstname, familyname, gender, city, country, image):
    try:
        get_db().execute("insert into user (email, password, firstname, familyname, gender, city, country, image) values (?, ?, ?, ?, ?, ?, ?, ?)",
                         [email, password, firstname, familyname, gender, city, country, image])
        get_db().commit()
        return True
    except Exception:
        return False


def update_user(old_email, email, password, firstname, familyname, gender, city, country, image):
    try:
        get_db().execute("update user set email=?, password=?, firstname=?, familyname=?, gender=?, city=?, country=?, image=? where email==?",
                         [email, password, firstname, familyname, gender, city, country, image, old_email])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_user(email):
    try:
        get_db().execute("delete from user where email==?", [email])
        get_db().commit()
        return True
    except Exception:
        return False


# ------------------------------------------------POST -------------------------------------------------------------------------------
def create_post(author, user, content, created, edited):
    try:
        get_db().execute("insert into post (author, user, content, created, edited) values (?, ?, ?, ?, ?)", [author, user, content, created, edited])
        get_db().commit()
        return True
    except Exception:
        return False


def retrieve_posts(user):
    cursor = get_db().execute("select id, author, user, content, created, edited from post where user==?", [user])
    rows = cursor.fetchall()
    return [{'id': row[0],
             'author': row[1],
             'user': row[2],
             'content': row[3],
             'created': row[4],
             'edited': row[5]
             } for row in rows]


def update_post(post_id, author, user, content, created, edited):
    try:
        get_db().execute("update post set author=?, user=?, content=?, created=?, edited=? where id==?", [author, user, content, created, edited, post_id])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_post(post_id):
    try:
        get_db().execute("delete from post where id==?", [post_id])
        get_db().commit()
        return True
    except Exception:
        return False


# ------------------------------------------------TOKEN -------------------------------------------------------------------------------
def create_token(email, token, valid):
    try:
        get_db().execute("insert into token (email, token, valid) values (?, ?, ?)", [email, token, valid])
        get_db().commit()
        return True
    except Exception:
        return False


def update_token(token, email, valid):
    try:
        get_db().execute("update token set email=?, valid=? where token==?", [email, valid, token])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_user_tokens(email):
    try:
        get_db().execute("delete from token where email==?", [email])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_token(token):
    try:
        get_db().execute("delete from token where token==?", [token])
        get_db().commit()
        return True
    except Exception:
        return False


def retrieve_token(token):
    cursor = get_db().execute("select email, token, valid from token where token==?", [token])
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

    return {
        "email": rows[0][0],
        "token": rows[0][1],
        "valid": rows[0][2],
    }

def retrieve_user_tokens(email):
    cursor = get_db().execute("select email, token, valid from token where email==?", [email])
    rows = cursor.fetchall()
    return [{
        "email": row[0],
        "token": row[1],
        "valid": row[2],
    } for row in rows]
