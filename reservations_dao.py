from datetime import datetime
import sqlite3

def get_reservations():
    query = "SELECT * FROM reservations"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query)

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_reservations_for_participant(p_participant_id):
    query = "SELECT R.*, T.title AS tour_title, T.meeting_point, T.duration, T.language, U.first_name AS guide_first_name, U.last_name AS guide_last_name FROM reservations R, tours T, users U WHERE R.tour_id = T.id AND T.guide_id = U.id AND R.participant_id = ? ORDER BY R.tour_date"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_participant_id,))

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_reservations_for_tour(p_tour_id):
    query = "SELECT R.*, U.first_name AS participant_first_name, U.last_name AS participant_last_name FROM reservations R, users U WHERE R.participant_id = U.id AND R.tour_id = ? ORDER BY R.tour_date, R.created_at"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_reservations_for_tour_date(p_tour_id, p_tour_date):
    query = "SELECT R.*, U.first_name AS participant_first_name, U.last_name AS participant_last_name FROM reservations R, users U WHERE R.participant_id = U.id AND R.tour_id = ? AND R.tour_date = ? ORDER BY R.created_at"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date))

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_reservation_by_id(p_reservation_id):
    query = "SELECT R.*, T.title AS tour_title, T.meeting_point, T.duration, T.language, U.first_name AS guide_first_name, U.last_name AS guide_last_name FROM reservations R, tours T, users U WHERE R.tour_id = T.id AND T.guide_id = U.id AND R.id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_reservation_id,))

    db_reservation = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservation

def get_guests_by_reservation(p_reservation_id):
    query = "SELECT * FROM reservation_guests WHERE reservation_id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_reservation_id,))

    db_guests = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_guests

def count_reservations_confirmed():
    query = "SELECT COUNT(*) FROM reservations WHERE status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count

def count_people_for_tour_date(p_tour_id, p_tour_date):
    query = "SELECT SUM(num_guests) FROM reservations WHERE tour_id = ? AND tour_date = ? AND status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date))

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count

def get_reservation(p_participant_id, p_tour_id, p_tour_date):
    query = "SELECT * FROM reservations WHERE participant_id = ? AND tour_id = ? AND tour_date = ? AND status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_participant_id, p_tour_id, p_tour_date))

    db_reservation = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservation

def new_reservation(p_participant_id, p_tour_id, p_tour_date, p_num_guests, p_status):
    query = "INSERT INTO reservations (participant_id, tour_id, tour_date, num_guests, status, created_at, cancelled_at) VALUES (?,?,?,?,?,?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_participant_id, p_tour_id, p_tour_date, p_num_guests, p_status, datetime.now(), None))

    conn.commit()
    cursor.close()
    conn.close()

def add_guest_to_reservation(p_reservation_id, p_first_name, p_last_name):
    query = "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?,?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_reservation_id, p_first_name, p_last_name))

    conn.commit()
    cursor.close()
    conn.close()

def cancel_reservation(p_reservation_id):
    query = "UPDATE reservations SET status = 'cancelled', cancelled_at = ? WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (datetime.now(), p_reservation_id))

    conn.commit()
    cursor.close()
    conn.close()

def reservations_by_language():
    query = "SELECT T.language, COUNT(R.id) AS num_reservations, SUM(R.people_count) AS people_count FROM reservations R, tours T WHERE R.tour_id = T.id AND R.status = 'confirmed' GROUP BY T.language ORDER BY num_reservations DESC"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    db_data = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_data