import pytest
import datetime

from unittest.mock import patch, MagicMock, call

from twidder.database_handler import (
    clear_database,
    create_user,
    get_user_by_email,
    update_user_by_email,
    delete_user_by_email,
    create_post,
    get_post_by_id,
    list_post,
    list_posts_by_user,
    list_posts_by_author,
    update_post_by_id,
    delete_post_by_id,
    delete_posts_by_user
)


def test_clear_database():
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        clear_database()

        expected_calls = [
            call.execute("DROP TABLE IF EXISTS user"),
            call.execute("DROP TABLE IF EXISTS post"),
            call.commit()
        ]
        assert mock_conn.method_calls == expected_calls


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_create_user(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        result = create_user(
            email='test@example.com',
            password='password',
            firstname='Test',
            lastname='User',
            gender='Other',
            city='Test City',
            country='Test Country',
            image=None
        )

        assert result == expected_result
        if not execute_raises_exception:
            mock_conn.execute.assert_called_once_with(
                "insert into user (email, password, firstname, lastname, gender, city, country, image) values (?, ?, ?, ?, ?, ?, ?, ?)",
                ['test@example.com', 'password', 'Test', 'User', 'Other', 'Test City', 'Test Country', None]
            )
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()


@pytest.mark.parametrize("user_exists, expected_result", [
    (True, {'email': 'test@example.com', 'password': 'password', 'firstname': 'Test', 'lastname': 'User', 'gender': 'Other', 'city': 'Test City', 'country': 'Test Country', 'image': None}),
    (False, None)
])
def test_get_user_by_email(user_exists, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        if user_exists:
            mock_cursor.fetchall.return_value = [
                ('test@example.com', 'password', 'Test', 'User', 'Other', 'Test City', 'Test Country', None)
            ]
        else:
            mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor

        result = get_user_by_email('test@example.com')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "select email, password, firstname, lastname, gender, city, country, image from user where email==?",
            ['test@example.com']
        )


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_update_user_by_email(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        result = update_user_by_email(
            curr_email='current@example.com',
            email='new@example.com',
            password='newpassword',
            firstname='New',
            lastname='Name',
            gender='Other',
            city='New City',
            country='New Country',
            image=None
        )

        assert result == expected_result
        if not execute_raises_exception:
            mock_conn.execute.assert_called_once_with(
                "update user set email=?, password=?, firstname=?, lastname=?, gender=?, city=?, country=?, image=? where email==?",
                ['new@example.com', 'newpassword', 'New', 'Name', 'Other', 'New City', 'New Country', None, 'current@example.com']
            )
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_delete_user_by_email(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        result = delete_user_by_email('test@example.com')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "delete from user where email==?", ['test@example.com']
        )
        if not execute_raises_exception:
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()


@pytest.mark.parametrize("execute_raises_exception, lastrowid, expected_result", [
    (False, 1, 1),
    (True, None, -1)
])
def test_create_post(execute_raises_exception, lastrowid, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = lastrowid
        if execute_raises_exception:
            mock_db.cursor.side_effect = Exception("Database error")
        else:
            mock_db.cursor.return_value = mock_cursor

        created = datetime.datetime(2020, 1, 1, 12, 0)
        edited = datetime.datetime(2020, 1, 1, 12, 0)
        result = create_post(
            author='author@example.com',
            user='user@example.com',
            content='Test content',
            created=created,
            edited=edited,
            media=None
        )

        assert result == expected_result
        if not execute_raises_exception:
            mock_db.cursor.assert_called_once()
            mock_cursor.execute.assert_called_once_with(
                "insert into post (author, user, content, created, edited, media) values (?, ?, ?, ?, ?, ?)",
                ['author@example.com', 'user@example.com', 'Test content', created, edited, None]
            )
            mock_db.commit.assert_called_once()
        else:
            mock_db.commit.assert_not_called()


@pytest.mark.parametrize("post_exists, expected_result", [
    (True, {
        "id": 1,
        "author": 'author@example.com',
        "user": 'user@example.com',
        "content": 'Test content',
        "created": 'created_date',
        "edited": 'edited_date',
        "media": None
    }),
    (False, None)
])
def test_get_post_by_id(post_exists, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        if post_exists:
            mock_cursor.fetchall.return_value = [
                (1, 'author@example.com', 'user@example.com', 'Test content', 'created_date', 'edited_date', None)
            ]
        else:
            mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor

        result = get_post_by_id('1')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "select id, author, user, content, created, edited, media from post where id==?",
            ['1']
        )


def test_list_post_with_posts():
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'author1@example.com', 'user1@example.com', 'Content 1', 'created1', 'edited1', None),
            (2, 'author2@example.com', 'user2@example.com', 'Content 2', 'created2', 'edited2', 'media2')
        ]
        mock_conn.execute.return_value = mock_cursor

        result = list_post()

        expected_result = [
            {
                "id": 1,
                "author": 'author1@example.com',
                "user": 'user1@example.com',
                "content": 'Content 1',
                "created": 'created1',
                "edited": 'edited1',
                "media": None
            },
            {
                "id": 2,
                "author": 'author2@example.com',
                "user": 'user2@example.com',
                "content": 'Content 2',
                "created": 'created2',
                "edited": 'edited2',
                "media": 'media2'
            }
        ]
        assert result == expected_result


def test_list_post_no_posts():
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor

        result = list_post()

        assert result == []


@pytest.mark.parametrize("posts_exist, expected_result", [
    (True, [
        {
            "id": 1,
            "author": 'author1@example.com',
            "user": 'user@example.com',
            "content": 'Content 1',
            "created": 'created1',
            "edited": 'edited1',
            "media": None
        }
    ]),
    (False, [])
])
def test_list_posts_by_user(posts_exist, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        if posts_exist:
            mock_cursor.fetchall.return_value = [
                (1, 'author1@example.com', 'user@example.com', 'Content 1', 'created1', 'edited1', None)
            ]
        else:
            mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor

        result = list_posts_by_user('user@example.com')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "select id, author, user, content, created, edited, media from post where user==?",
            ['user@example.com']
        )


@pytest.mark.parametrize("posts_exist, expected_result", [
    (True, [
        {
            "id": 1,
            "author": 'author@example.com',
            "user": 'user1@example.com',
            "content": 'Content 1',
            "created": 'created1',
            "edited": 'edited1',
            "media": None
        }
    ]),
    (False, [])
])
def test_list_posts_by_author(posts_exist, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_cursor = MagicMock()
        if posts_exist:
            mock_cursor.fetchall.return_value = [
                (1, 'author@example.com', 'user1@example.com', 'Content 1', 'created1', 'edited1', None)
            ]
        else:
            mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor

        result = list_posts_by_author('author@example.com')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "select id, author, user, content, created, edited, media from post where author==?",
            ['author@example.com']
        )


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_update_post_by_id(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        post_id = '1'
        author = 'newauthor@example.com'
        user = 'newuser@example.com'
        content = 'Updated content'
        created = datetime.datetime(2020, 1, 1, 12, 0)
        edited = datetime.datetime(2020, 1, 2, 12, 0)
        media = 'newmedia'

        result = update_post_by_id(
            post_id=post_id,
            author=author,
            user=user,
            content=content,
            created=created,
            edited=edited,
            media=media
        )

        assert result == expected_result
        if not execute_raises_exception:
            mock_conn.execute.assert_called_once_with(
                "update post set author=?, user=?, content=?, created=?, edited=?, media=? where id==?",
                [author, user, content, created, edited, media, post_id]
            )
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_delete_post_by_id(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        result = delete_post_by_id('1')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "delete from post where id==?", ['1']
        )
        if not execute_raises_exception:
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()


@pytest.mark.parametrize("execute_raises_exception, expected_result", [
    (False, True),
    (True, False)
])
def test_delete_posts_by_user(execute_raises_exception, expected_result):
    with patch('twidder.database_handler.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn
        if execute_raises_exception:
            mock_conn.execute.side_effect = Exception("Database error")
        else:
            mock_conn.execute.return_value = None

        result = delete_posts_by_user('user@example.com')

        assert result == expected_result
        mock_conn.execute.assert_called_once_with(
            "delete from post where user==?", ['user@example.com']
        )
        if not execute_raises_exception:
            mock_conn.commit.assert_called_once()
        else:
            mock_conn.commit.assert_not_called()
