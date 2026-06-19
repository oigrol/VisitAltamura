import sqlite3

def get_report(p_tour_id, p_tour_date):
    query = "SELECT * FROM tour_final_reports WHERE tour_id = ? AND tour_date = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date))

    db_report = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_report

def new_report(p_tour_id, p_tour_date, p_final_participants, p_group_img):
    query = "INSERT INTO tour_final_reports (tour_id, tour_date, final_participants, group_img) VALUES (?,?,?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date, p_final_participants, p_group_img))

    conn.commit()
    cursor.close()
    conn.close() 

def get_reports_for_tour(p_tour_id):
    query = "SELECT * FROM tour_final_reports WHERE tour_id = ? ORDER BY tour_date DESC"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_reports = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reports