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