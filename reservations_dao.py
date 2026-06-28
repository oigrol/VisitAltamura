from datetime import date, datetime
import sqlite3

def tominutes(time_str):
    hours, minutes = time_str.split(':')
    return int(hours) * 60 + int(minutes)

def new_reservation(p_participant_id, p_tour_id, p_tour_date, p_people_count, p_status, p_guests):
    query = "INSERT INTO reservations (participant_id, tour_id, tour_date, people_count, status, created_at, cancelled_at) VALUES (?,?,?,?,?,?,?)"
    query_guests = "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?,?,?)"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_participant_id, p_tour_id, p_tour_date, p_people_count, p_status, datetime.now(), None))

    reservation_id = cursor.lastrowid

    for guest in p_guests:
        cursor.execute(query_guests, (reservation_id, guest['first_name'], guest['last_name']))

    conn.commit()
    cursor.close()
    conn.close()
    
    return reservation_id

def cancel_reservation(p_reservation_id):
    query = "UPDATE reservations SET status = 'cancelled', cancelled_at = ? WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (datetime.now(), p_reservation_id))

    conn.commit()
    cursor.close()
    conn.close()

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

def get_reservations_for_participant(p_participant_id):
    query = "SELECT R.*, T.title AS tour_title, T.meeting_point, T.duration, T.language, U.first_name AS guide_first_name, U.last_name AS guide_last_name, (SELECT TI.path_img FROM tour_images TI WHERE TI.tour_id = T.id LIMIT 1) AS path_img FROM reservations R, tours T, users U WHERE R.tour_id = T.id AND T.guide_id = U.id AND R.participant_id = ? ORDER BY R.tour_date"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_participant_id,))

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_reservations_for_tour_date(p_tour_id, p_tour_date):
    query = "SELECT R.*, U.first_name AS participant_first_name, U.last_name AS participant_last_name FROM reservations R, users U WHERE R.participant_id = U.id AND R.status = 'confirmed' AND R.tour_id = ? AND R.tour_date = ? ORDER BY R.created_at"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date))

    db_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_reservations

def get_cancelled_reservations_for_tour_date(p_tour_id, p_tour_date):
    query = "SELECT R.*, U.first_name AS participant_first_name, U.last_name AS participant_last_name FROM reservations R, users U WHERE R.participant_id = U.id AND R.status = 'cancelled' AND R.tour_id = ? AND R.tour_date = ? ORDER BY R.cancelled_at DESC"

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

def count_reservations():
    query = "SELECT COUNT(*) FROM reservations"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count

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
    query = "SELECT SUM(people_count) FROM reservations WHERE tour_id = ? AND tour_date = ? AND status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id, p_tour_date))

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count

def get_reservations_by_language():
    query = "SELECT T.language, COUNT(R.id) AS num_reservations, SUM(R.people_count) AS people_count FROM reservations R, tours T WHERE R.tour_id = T.id AND R.status = 'confirmed' GROUP BY T.language ORDER BY num_reservations DESC, T.language"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    db_data = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_data

def get_dates_with_confirmed_reservations(p_tour_id, p_tour_date=None):
    query = "SELECT R.tour_date, WP.start_time, SUM(R.people_count) AS expected_people FROM reservations R, tour_weekly_plan WP WHERE R.tour_id = WP.tour_id AND WP.day_of_week = (strftime('%w', R.tour_date) + 6) % 7 AND R.tour_id = ?"

    params = (p_tour_id,)

    if p_tour_date is not None:
        query += " AND R.tour_date = ?"
        params += (p_tour_date,)

    query += " AND R.status = 'confirmed' GROUP BY R.tour_date, WP.start_time ORDER BY R.tour_date, WP.start_time"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, params)

    db_dates = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_dates

def get_dates_with_cancelled_reservations(p_tour_id, p_tour_date=None):
    query = "SELECT R.tour_date, WP.start_time, SUM(R.people_count) AS cancelled_people FROM reservations R, tour_weekly_plan WP WHERE R.tour_id = WP.tour_id AND WP.day_of_week = (strftime('%w', R.tour_date) + 6) % 7 AND R.tour_id = ?"
    params = (p_tour_id,)

    if p_tour_date is not None:
        query += " AND R.tour_date = ?"
        params += (p_tour_date,)

    query += " AND R.status = 'cancelled' GROUP BY R.tour_date, WP.start_time ORDER BY R.tour_date DESC, WP.start_time DESC"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, params)

    db_dates = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_dates


def check_conflicting_reservation(p_participant_id, p_tour_date, p_tour_id, p_start_time, p_duration):
    weekday = date.fromisoformat(p_tour_date).weekday()

    query = "SELECT R.id, T.duration, WP.start_time FROM reservations R, tours T, tour_weekly_plan WP WHERE R.tour_id = T.id AND T.id = WP.tour_id AND WP.day_of_week = ? AND R.participant_id = ? AND R.tour_date = ? AND R.tour_id != ? AND R.status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (weekday, p_participant_id, p_tour_date, p_tour_id))

    existing_reservations = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    new_start_time = tominutes(p_start_time)
    new_end_time = new_start_time + int(p_duration)

    for reservation in existing_reservations:
        existing_start_time = tominutes(reservation['start_time'])
        existing_end_time = existing_start_time + int(reservation['duration'])

        if (new_start_time < existing_end_time) and (new_end_time > existing_start_time):
            return True

    return False