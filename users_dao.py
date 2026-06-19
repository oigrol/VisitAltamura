import sqlite3

def new_user(p_first_name, p_last_name, p_email, p_password, p_role, p_profile_img):

    query = "INSERT INTO users (first_name, last_name, email, password, role, profile_img) VALUES (?,?,?,?,?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_first_name, p_last_name, p_email, p_password, p_role, p_profile_img))

    user_id = get_id_by_email(p_email)['id']
    if p_role == "guide":
        for language in p_languages:
            cursor.execute("INSERT INTO guide_languages (guide_id, language) VALUES (?,?)", (user_id, language))
    conn.commit()
    cursor.close()
    conn.close()
    return user_id

def get_users():
    query = "SELECT * FROM users ORDER BY last_name, first_name"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)

    db_users = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_users

def get_id_by_email(p_email):
    query = "SELECT id FROM users WHERE email = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_email,))

    db_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_user

def get_guides():
    query = "SELECT * FROM users WHERE role = 'guide' ORDER BY last_name, first_name"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)

    db_guides = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_guides

def count_guides():
    query = "SELECT COUNT(*) FROM users WHERE role = 'guide'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count

def get_guide_by_id(p_id):
    query = "SELECT * FROM users WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_id,))

    db_guide = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_guide

def get_participant_by_id(p_id):
    query = "SELECT * FROM users WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_id,))

    db_participant = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_participant

def get_user_by_id(p_id):
    query = "SELECT * FROM users WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_id,))

    db_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_user

def get_user_by_email(p_email):
    query = "SELECT * FROM users WHERE email = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_email,))

    db_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_user

def get_id_by_email(p_email):
    query = "SELECT id FROM users WHERE email = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_email,))

    db_user = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_user

def count_participants():
    query = "SELECT COUNT(*) FROM users WHERE role = 'participant'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count