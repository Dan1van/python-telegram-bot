import sqlite3


def ensure_connection(func):
    def inner(*args, **kwargs):
        with sqlite3.connect('bot.db') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner


@ensure_connection
def init_db(conn, force: bool = False):
    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS user_info')
        c.execute('DROP TABLE IF EXISTS approval_list')
        c.execute('DROP TABLE IF EXISTS approved_list')
        c.execute('DROP TABLE IF EXISTS list_to_design')
        c.execute('DROP TABLE IF EXISTS weekly_useful_info')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            member_name TEXT NOT NULL,
            role TEXT NOT NULL,
            chat_id INTEGER NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS approval_list (
            id INTEGER PRIMARY KEY,
            author_name TEXT NOT NULL,
            chat_id INTEGER NULL,
            file_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS approved_list (
            id INTEGER PRIMARY KEY,
            author_name TEXT NOT NULL,
            chat_id INTEGER NULL,
            file_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS list_to_design (
            id INTEGER PRIMARY KEY,
            cardmaker TEXT NOT NULL,
            author_name TEXT NOT NULL,
            chat_id INTEGER NULL,
            file_id TEXT,
            deadline TEXT,
            is_ready INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS weekly_useful_info (
            id INTEGER PRIMARY KEY,
            info_type TEXT,
            text TEXT
        )
    ''')

    if force:
        c.execute('INSERT INTO weekly_useful_info (info_type, text) VALUES ("Author", "None")')
        c.execute('INSERT INTO weekly_useful_info (info_type, text) VALUES ("Cardmaker", "None")')
    conn.commit()


@ensure_connection
def set_user_info(conn, user_id: int, member_name: str, role: str):
    c = conn.cursor()
    c.execute('INSERT INTO user_info (user_id, member_name, role, chat_id) VALUES (?, ?, ?, ?)',
              (user_id, member_name, role, user_id))
    conn.commit()


@ensure_connection
def set_user_chat_id(conn, user_id: int, chat_id: int):
    c = conn.cursor()
    c.execute('UPDATE user_info SET chat_id = ? WHERE user_id = ?', (chat_id, user_id))
    conn.commit()


@ensure_connection
def get_user_info(conn, user_id: int):
    c = conn.cursor()
    c.execute('SELECT member_name, role, chat_id FROM user_info WHERE user_id = ?', (user_id,))
    (member_name, member_role, chat_id) = c.fetchone()
    return member_name, member_role, chat_id


@ensure_connection
def get_user_chat_id_by_role(conn, user_role: str):
    c = conn.cursor()
    c.execute('SELECT chat_id FROM user_info WHERE role = ?', (user_role,))
    (chat_id,) = c.fetchone()
    return chat_id


@ensure_connection
def set_approval_list(conn, author_name: str, file_id: str):
    c = conn.cursor()
    c.execute('SELECT chat_id FROM user_info WHERE member_name = ?', (author_name,))
    (chat_id,) = c.fetchone()
    c.execute('INSERT INTO approval_list (author_name, chat_id, file_id) VALUES (?, ?, ?)',
              (author_name, chat_id, file_id))
    conn.commit()


@ensure_connection
def set_approval_list_by_coordinator(conn, author_name: str, file_id: str):
    c = conn.cursor()
    c.execute('SELECT chat_id FROM user_info WHERE role = "Coordinator"')
    (chat_id,) = c.fetchone()
    c.execute('INSERT INTO approval_list (author_name, chat_id, file_id) VALUES (?, ?, ?)',
              (author_name, chat_id, file_id))


@ensure_connection
def get_users(conn):
    c = conn.cursor()
    c.execute('SELECT member_name, role FROM user_info')
    user_list = []
    for user in c:
        user_list.append(user)
    return user_list


@ensure_connection
def remove_user(conn, member_name: str):
    c = conn.cursor()
    c.execute('DELETE FROM user_info WHERE member_name = ?', (member_name,))
    conn.commit()

@ensure_connection
def get_approval_list(conn):
    c = conn.cursor()
    c.execute('SELECT id, author_name, file_id, chat_id FROM approval_list')
    article_list = []
    for article in c:
        article_list.append({'id': article[0], 'author': article[1], 'file_id': article[2], 'chat_id': article[3]})
    return article_list


@ensure_connection
def delete_approval_list(conn, id: int):
    c = conn.cursor()
    c.execute('DELETE FROM approval_list WHERE id = ?', (id,))
    conn.commit()


@ensure_connection
def set_approved_list(conn, id: int):
    c = conn.cursor()
    c.execute('SELECT author_name, chat_id, file_id FROM approval_list WHERE id = ?', (id,))
    (author_name, chat_id, file_id) = c.fetchone()
    c.execute('INSERT INTO approved_list (author_name, chat_id, file_id) VALUES (?, ?, ?)',
              (author_name, chat_id, file_id))
    c.execute('DELETE FROM approval_list WHERE id = ?', (id,))
    conn.commit()


@ensure_connection
def get_approved_list(conn):
    c = conn.cursor()
    c.execute('SELECT id, author_name, file_id FROM approved_list')
    article_list = []
    for article in c:
        article_list.append({'id': article[0], 'author': article[1], 'file_id': article[2]})
    return article_list


@ensure_connection
def member_chat_id(conn, member_name: str):
    c = conn.cursor()
    c.execute('SELECT chat_id FROM user_info WHERE member_name = ?', (member_name,))
    (chat_id,) = c.fetchone()
    return chat_id


@ensure_connection
def get_cardmakers_list(conn):
    c = conn.cursor()
    c.execute('SELECT member_name, chat_id FROM user_info WHERE role = "Cardmaker"')
    cardmaker_list = []
    for cardmaker in c:
        cardmaker_list.append({'name': cardmaker[0], 'chat_id': cardmaker[1]})
    return cardmaker_list


@ensure_connection
def set_list_to_design(conn, id: int, cardmaker: str, date: str):
    c = conn.cursor()
    c.execute('SELECT author_name, chat_id, file_id FROM approved_list WHERE id = ?', (id,))
    (author_name, chat_id, file_id) = c.fetchone()
    c.execute(
        'INSERT INTO list_to_design (cardmaker, author_name, chat_id, file_id, deadline, is_ready) VALUES (?, ?, ?, ?, ?, 0)',
        (cardmaker, author_name, chat_id, file_id, date))
    c.execute('DELETE FROM approved_list WHERE id = ?', (id,))
    conn.commit()


@ensure_connection
def get_cardmaker_article_count(conn, cardmaker: str):
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM list_to_design WHERE cardmaker = ?', (cardmaker,))
    (res,) = c.fetchone()
    return res


@ensure_connection
def get_list_to_design(conn, cardmaker: str):
    c = conn.cursor()
    c.execute('SELECT id, author_name, file_id, deadline FROM list_to_design WHERE cardmaker = ? AND is_ready = 0',
              (cardmaker,))
    article_to_design_list = []
    for article in c:
        article_to_design_list.append(
            {'id': article[0], 'author': article[1], 'file_id': article[2], 'deadline': article[3]})
    return article_to_design_list


@ensure_connection
def delete_list_to_design(conn, id: int):
    c = conn.cursor()
    c.execute('DELETE FROM list_to_design WHERE id = ?', (id,))
    conn.commit()


@ensure_connection
def set_article_readiness(conn, id: int):
    c = conn.cursor()
    c.execute('UPDATE list_to_design SET is_ready = 1 WHERE id = ?', (id,))
    conn.commit()


@ensure_connection
def get_article_readiness(conn, id: int):
    c = conn.cursor()
    c.execute('SELECT is_ready FROM list_to_design WHERE id = ?', (id,))
    (is_ready,) = c.fetchone()
    return is_ready


@ensure_connection
def set_weekly_useful_info(conn, info_type: str, text: str):
    c = conn.cursor()
    c.execute('UPDATE weekly_useful_info SET text = ? WHERE info_type = ?', (text, info_type))
    conn.commit()


@ensure_connection
def get_weekly_useful_info(conn, info_type: str):
    c = conn.cursor()
    c.execute('SELECT text FROM weekly_useful_info WHERE info_type = ?', (info_type,))
    (text,) = c.fetchone()
    return text


@ensure_connection
def get_newsletter_chat_ids(conn, newsletter_type: str):
    if newsletter_type == 'For authors':
        role = 'Author'
    else:
        role = 'Cardmaker'
    c = conn.cursor()
    c.execute('SELECT chat_id from user_info WHERE role = ?', (role,))
    chat_id_list = []
    for i in c:
        chat_id_list.append(i[0])

    return chat_id_list


if __name__ == '__main__':
    init_db(force=True)

    set_user_info(user_id=442046856, member_name='Иван Данюшевский', role='Coordinator')
    set_user_info(user_id=442046856, member_name='Иван Данюшевский', role='Cardmaker')
    set_user_info(user_id=718148565, member_name='Анна Баюканская', role='Supervisor')