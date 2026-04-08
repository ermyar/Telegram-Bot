from dataclasses import astuple
from sqlite3 import Row
from typing import List, Iterable

import aiosqlite as asq
from aiosqlite import Cursor
import sqlite3 as sq

from user import User
def get_token() -> str:
    db = sq.connect('data.db')
    cur = db.execute('SELECT api_key FROM bot_settings')
    token = cur.fetchone()[0]
    cur.close()
    db.close()
    return token


async def get_user(user_id: int) -> tuple | None:
    db = await asq.connect('data.db')
    cur: Cursor = await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = (await cur.fetchone())
    await cur.close()
    await db.close()
    return user


async def save_user(user: User):
    db = await asq.connect('data.db')
    await db.execute('INSERT INTO users '
                     'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     astuple(user) + ('',))
    await db.commit()
    await db.close()


async def delete_user(user_id: int):
    db = await asq.connect('data.db')
    await db.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    await db.execute('DELETE FROM likes WHERE from_user = ?', (user_id,))
    await db.execute('DELETE FROM likes WHERE to_user = ?', (user_id,))
    await db.commit()
    await db.close()


async def get_matching_users(user: User) -> Iterable[Row]:
    db = await asq.connect('data.db')
    if user.searching_for != 3:
        cur: Cursor = await db.execute('SELECT user_id '
                                       'FROM users '
                                       'WHERE (sex = ? AND (searching_for = ? OR searching_for = 3) AND user_id != ?)',
                                       (user.searching_for, user.sex, user.user_id))
    else:
        cur: Cursor = await db.execute('SELECT user_id '
                                       'FROM users '
                                       'WHERE ((searching_for = ? OR searching_for = 3) AND user_id != ?)',
                                       (user.sex, user.user_id))
    users = await cur.fetchall()
    await cur.close()
    await db.close()
    return users


async def get_watched(user_id: int) -> List[int]:
    db = await asq.connect('data.db')
    cur: Cursor = await db.execute('SELECT watched '
                                   'FROM users '
                                   'WHERE user_id = ?',
                                   (user_id,))
    users = (await cur.fetchone())[0]
    await cur.close()
    await db.close()
    if users == '':
        return []
    return list(map(int, users.split('; ')))


async def add_like(from_id: int, to_id: int) -> None:
    db = await asq.connect('data.db')
    await db.execute('INSERT INTO likes '
                     'VALUES (?, ?)',
                     (from_id, to_id))
    await db.commit()
    await db.close()


async def get_photo(user_id: int) -> str:
    db = await asq.connect('data.db')
    cur: Cursor = await db.execute('SELECT photo FROM users WHERE user_id = ?', (user_id, ))
    photo: str = (await cur.fetchone())[0]
    await cur.close()
    await db.close()
    return photo


async def add_watched(user_id: int, watched_id: int) -> None:
    db = await asq.connect('data.db')
    cur: Cursor = await db.execute('SELECT watched FROM users WHERE user_id = ?', (user_id, ))
    watched: str = (await cur.fetchone())[0]
    watched += f'; {watched_id}'
    watched = watched.removeprefix('; ')
    await cur.close()
    await db.execute('UPDATE users SET watched = ? WHERE user_id = ?',
                     (watched, user_id))
    await db.commit()
    await db.close()


async def get_like(user_id: int) -> Row | None:
    db = await asq.connect('data.db')
    cur: Cursor = await db.execute('SELECT from_user '
                                   'FROM likes '
                                   'WHERE to_user = ?',
                                   (user_id,))
    from_user = await cur.fetchone()
    await cur.close()
    await db.close()
    return from_user


async def del_like(from_id: int, to_id: int) -> None:
    db = await asq.connect('data.db')
    await db.execute('DELETE FROM likes '
                     'WHERE (from_user = ? AND to_user = ?)',
                     (from_id, to_id))
    await db.commit()
    await db.close()

 
async def clear_watched():
    db = await asq.connect('data.db')
    await db.execute('UPDATE users SET watched = ?', ('', ))
    await db.commit()
    await db.close()


async def start_db():
    db = await asq.connect('data.db')
    await db.execute("""create table if not exists bot_settings
(
    api_key TEXT not null
);
""")
    await db.commit()
    await db.execute("""create table if not exists likes
(
    from_user integer not null,
    to_user   integer not null
);
""")
    await db.commit()
    await db.execute("""create table if not exists users
(
    user_id       integer not null,
    username      TEXT    not null,
    name          TEXT    not null,
    age           integer not null,
    photo         TEXT    not null,
    description   TEXT    not null,
    place         integer not null,
    sex           integer not null,
    searching_for integer not null,
    watched       TEXT
);
""")
    await db.commit()
    await db.close()
