import os
import re
import sqlite3
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Optional

from cheems.config import config
from cheems.targets import Picture


def _sanitize_str_for_db(s: str) -> str:
    return re.sub(r'[^\w\s/:.]', '', s)


_db_dir = config['db_dir']
_filename = _db_dir + '/pics.db'

_create_tables = '''
CREATE TABLE IF NOT EXISTS pics (
    id INT PRIMARY KEY,
    url TEXT,
    msg TEXT,
    time DATETIME,
    uploader_id INT,
    channel_id INT,
    server_id INT,
    sfw BOOLEAN
);
'''


def _get_db_connection() -> Connection:
    """Don't forget to close this connection after use."""
    if not os.path.exists(_db_dir):
        os.makedirs(_db_dir)
    if not os.path.exists(_filename):
        open(_filename, 'a').close()
    con = sqlite3.connect(f'file:{_filename}?mode=rw', uri=True)
    cur = con.cursor()
    cur.executescript(_create_tables)
    con.commit()
    cur.close()
    return con


def save_pic(pic: Picture):
    """Doesn't commit the transaction, call `save_all()`"""
    cur = _con.cursor()
    msg = _sanitize_str_for_db(pic.msg)
    url = _sanitize_str_for_db(pic.url)
    cur.execute(
        'INSERT OR IGNORE INTO pics values (?, ?, ?, ?, ?, ?, ?, ?)',
        (pic.id, url, msg, pic.time, pic.uploader_id, pic.channel_id, pic.server_id, pic.sfw)
    )


def get_pic_by_id(pic_id: int) -> Optional[Picture]:
    cur = _con.cursor()
    cur.execute('SELECT * FROM pics WHERE id=:id', {'id': pic_id})
    results = cur.fetchone()
    if results is None:
        return None
    return _pic_from_db_result(results)


def get_pics_where(
        uploader_id: int = None,
        channel_id: int = None,
        server_id: int = None,
        word: str = None,
        sfw: bool = None,
        random: bool = False,
        limit: int = None,
) -> list[Picture]:
    """
    Fetch pics with optional conditions, ordered by time.
    :param random: use random order instead.
    """
    cur = _con.cursor()
    script = 'SELECT * FROM pics'
    conditions = []
    if uploader_id is not None:
        conditions.append(f'uploader_id={uploader_id}')
    if channel_id is not None:
        conditions.append(f'channel_id={channel_id}')
    if server_id is not None:
        conditions.append(f'server_id={server_id}')
    if word is not None:
        sanitized_word = _sanitize_str_for_db(word).lower()
        conditions.append(f'lower(msg) like "%{sanitized_word}%"')
    if sfw is not None:
        conditions.append(f'sfw = {sfw}')
    if len(conditions) > 0:
        script += ' WHERE ' + ' AND '.join(conditions)
    if random:
        script += ' ORDER BY RANDOM()'
    else:
        script += ' ORDER BY time'
    if limit is not None:
        script += f' LIMIT {limit}'
    cur.execute(script)
    results = cur.fetchall()
    pics = [_pic_from_db_result(r) for r in results]
    return pics


def _pic_from_db_result(result: any) -> Picture:
    (_id, url, msg, time, uploader_id, channel_id, server_id, sfw) = result
    return Picture(
        int(_id), str(url), str(msg), datetime.fromisoformat(time).replace(tzinfo=timezone.utc),
        int(uploader_id), int(channel_id), int(server_id), bool(sfw)
    )


def save_all():
    """Commit DB operations"""
    _con.commit()


_con = _get_db_connection()
