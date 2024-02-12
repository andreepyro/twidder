import datetime
import sqlite3

from flask import g, current_app


def get_db():
    """
    Get a database connection to the SQLite database.

    :return: SQLite database connection
    """
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect(current_app.config["DATABASE_FILE"])
    return db


def disconnect_db():
    """
    Disconnect the current database connection.

    :return: None
    """
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
        g.db = None
    return db


def initialize_database():
    """
    Initialize the database schema and tables.

    :return: None
    """
    with open(current_app.config["DATABASE_SCHEMA"], "r") as schema_file:
        get_db().executescript(schema_file.read())
        get_db().commit()


def create_user(email: str, password: str, firstname: str, lastname: str, gender: str, city: str, country: str, image: bytes) -> bool:
    """
    Insert a new user into the database.

    :param email: user's email address
    :param password: user's password
    :param firstname: user's first name
    :param lastname: user's lastname
    :param gender: user's gender
    :param city: user's city
    :param country: user's country
    :param image: user's profile image
    :return: True on success, False on error
    """
    try:
        get_db().execute("insert into user (email, password, firstname, lastname, gender, city, country, image) values (?, ?, ?, ?, ?, ?, ?, ?)",
                         [email, password, firstname, lastname, gender, city, country, image])
        get_db().commit()
        return True
    except Exception:
        return False


def get_user_by_email(email: str) -> None | dict:
    """
    Retrieve the user information belonging to a user with the given email address.

    :param email: user's email address
    :return: dictionary of user's information if user exists, None otherwise
    """
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
    """
    Update information belonging to a user with the given email address.

    :param curr_email: current user's email address
    :param email: new email address
    :param password: new hashed password
    :param firstname: new first name
    :param lastname: new last name
    :param gender: new gender
    :param city: new city
    :param country: new country
    :param image: new profile image
    :return: True on success, False on error
    """
    try:
        get_db().execute("update user set email=?, password=?, firstname=?, lastname=?, gender=?, city=?, country=?, image=? where email==?",
                         [email, password, firstname, lastname, gender, city, country, image, curr_email])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_user_by_email(email: str) -> bool:
    """
    Delete a user with the given email address.

    :param email: user's email address
    :return: True on success, False on error
    """
    try:
        get_db().execute("delete from user where email==?", [email])
        get_db().commit()
        return True
    except Exception:
        return False


def create_post(author: str, user: str, content: str, created: datetime.datetime, edited: datetime.datetime) -> int:
    """
    Insert a new post into the database.

    :param author: email of the author
    :param user: email of the user on whose wall the post will be created
    :param content: content of the post
    :param created: datetime of the post creation
    :param edited: datetime of the post last edition
    :return: id of the created post on success, -1 on error
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("insert into post (author, user, content, created, edited) values (?, ?, ?, ?, ?)", [author, user, content, created, edited])
        db.commit()
        return cursor.lastrowid
    except Exception:
        return -1


def get_post_by_id(post_id: str) -> None | dict:
    """
    Retrieve a post by its id.

    :param post_id: id of the post
    :return: dictionary of the posts information if it exists, None otherwise
    """
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
    """
    List all posts.

    :return: list of dictionaries of posts information
    """
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
    """
    List all posts on given user's wall.

    :param email: user's email address
    :return: list of dictionaries of posts information
    """
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
    """
    List all posts created by given user.

    :param email: user's email address
    :return: list of dictionaries of posts information
    """
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
    """
    Update post by its id.

    :param post_id: post id
    :param author: new author's email
    :param user: new user's email
    :param content: new post's content
    :param created: datetime of the post creation
    :param edited: datetime of the post last edition
    :return: True on success, False on error
    """
    try:
        get_db().execute("update post set author=?, user=?, content=?, created=?, edited=? where id==?", [author, user, content, created, edited, post_id])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_post_by_id(post_id: str) -> bool:
    """
    Deletes post by its id.

    :param post_id: post id
    :return: True on success, False on error
    """
    try:
        get_db().execute("delete from post where id==?", [post_id])
        get_db().commit()
        return True
    except Exception:
        return False


def delete_posts_by_user(email: str) -> bool:
    """
    Delete all posts on user's wall.

    :param email: user's email address
    :return: True on success, False on error
    """
    try:
        get_db().execute("delete from post where user==?", [email])
        get_db().commit()
        return True
    except Exception:
        return False
