import sqlite3

def get_guide_languages():
    query = "SELECT DISTINCT language FROM guide_languages ORDER BY language"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)

    languages = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return [language['language'] for language in languages]

def get_languages_by_guide(p_guide_id):
    query = "SELECT language FROM guide_languages WHERE guide_id = ? ORDER BY language"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_guide_id,))

    languages = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return [language['language'] for language in languages]

def new_guide_language(p_guide_id, p_language):
    query = "INSERT INTO guide_languages (guide_id, language) VALUES (?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_guide_id, p_language))

    conn.commit()
    cursor.close()
    conn.close()
    
def count_guide_languages():
    query = "SELECT COUNT(DISTINCT language) FROM guide_languages"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count