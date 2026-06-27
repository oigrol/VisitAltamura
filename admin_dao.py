import sqlite3


def get_platform_stats():
    query = "SELECT (SELECT COUNT(*) FROM users WHERE role = 'guide') AS total_guides, (SELECT COUNT(*) FROM users WHERE role = 'participant') AS total_participants, (SELECT COUNT(*) FROM tours) AS total_tours, (SELECT COUNT(*) FROM reservations) AS total_reservations, (SELECT COUNT(*) FROM reservations WHERE status = 'confirmed') AS confirmed_reservations, (SELECT COUNT(*) FROM tour_final_reports) AS completed_reports"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    return stats


def get_reservations_by_language():
    query = "SELECT T.language, (SELECT COUNT(id) FROM reservations WHERE tour_id = T.id) AS total_reservations, (SELECT COUNT(id) FROM reservations WHERE tour_id = T.id AND status = 'confirmed') AS confirmed_reservations FROM tours T ORDER BY total_reservations DESC, T.language"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    reservations_by_language = cursor.fetchall()

    cursor.close()
    conn.close()

    return reservations_by_language

def get_recent_reservations():
    query = "SELECT R.id, R.tour_date, R.people_count, R.status, R.created_at, T.id AS tour_id, T.title AS tour_title, T.language, U.first_name AS participant_first_name, U.last_name AS participant_last_name FROM reservations R, tours T, users U WHERE R.tour_id = T.id AND R.participant_id = U.id ORDER BY R.created_at DESC, R.id DESC LIMIT 6"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)
    recent_reservations = cursor.fetchall()

    cursor.close()
    conn.close()

    return recent_reservations


def get_tour_admin_metrics(p_tour_id):
    query = "SELECT COUNT(*) AS total_reservations, SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) AS confirmed_reservations, COALESCE(SUM(CASE WHEN status = 'confirmed' THEN people_count ELSE 0 END), 0) AS expected_people FROM reservations WHERE tour_id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))
    metrics = cursor.fetchone()

    cursor.close()
    conn.close()

    return metrics
