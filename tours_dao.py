import sqlite3
from datetime import date, datetime

def new_tour(p_title, p_description, p_guide_id, p_duration, p_language, p_meeting_point, p_max_participants, p_weekly_plan, p_stops, p_images):
    
    query_tour = "INSERT INTO tours (title, description, guide_id, duration, language, meeting_point, max_participants, created_at) VALUES (?,?,?,?,?,?,?,?, ?)"
    query_weekly_plan = "INSERT INTO weekly_plans (tour_id, day_of_week, start_time) VALUES (?,?,?)"
    query_stop = "INSERT INTO tour_stops (tour_id, position, name) VALUES (?,?,?)"
    query_image = "INSERT INTO tour_images (tour_id, path_img, position) VALUES (?,?,?)"
    
    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query_tour, (p_title, p_description, p_guide_id, p_duration, p_language, p_meeting_point, p_max_participants, datetime.now()))

    tour_id = get_id_by_title_and_guide(p_title, p_guide_id)
     
    for (day_of_week, start_time) in p_weekly_plan:
        cursor.execute(query_weekly_plan, (tour_id, day_of_week, start_time))
    
    for (position, name) in p_stops:
        cursor.execute(query_stop, (tour_id, position, name))
    
    for (path_img, position) in p_images:
        cursor.execute(query_image, (tour_id, path_img, position))
    
    conn.commit()
    cursor.close()
    conn.close()

    return tour_id

def get_tours():
    return get_tours_by_filters('', '', '')

def get_tours_by_filters(p_date, p_language, p_duration):
    query = "SELECT T.*, U.first_name, U.last_name, (SELECT TI.path_img FROM tour_images TI WHERE TI.tour_id = T.id ORDER BY TI.position LIMIT 1) AS path_img FROM tours T, users U WHERE T.guide_id = U.id"
    query_params = ()

    if p_date:
        if isinstance(p_date, str):
            p_date = date.fromisoformat(p_date)

        weekday = p_date.weekday()  # 0 = Monday, 6 = Sunday
        query += " AND T.id IN (SELECT tour_id FROM tour_weekly_plan WHERE day_of_week = ?)"
        query_params += (weekday,)
    
    if p_language:
        query += " AND T.language = ?"
        query_params += (p_language,)

    if p_duration == 'short':
        query += " AND T.duration <= 90"
    if p_duration == 'medium':
        query += " AND T.duration > 90 AND T.duration <= 150"
    if p_duration == 'long':
        query += " AND T.duration > 150"

    query += " ORDER BY T.created_at DESC, T.id DESC"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, query_params)

    db_tours = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_tours


def get_id_by_title_and_guide(p_title, p_guide_id):
    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    tour_id = cursor.execute("SELECT id FROM tours WHERE title = ? AND guide_id = ? ORDER BY created_at DESC LIMIT 1", (p_title, p_guide_id)).fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return tour_id

def get_tour_by_id(p_tour_id):
    query = "SELECT T.*, U.first_name, U.last_name, U.email AS guide_email, (SELECT TI.path_img FROM tour_images TI WHERE TI.tour_id = T.id ORDER BY TI.position LIMIT 1) AS path_img FROM tours T, users U WHERE T.guide_id = U.id AND T.id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_tour = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return db_tour

def get_tour_images(p_tour_id):
    query = "SELECT * FROM tour_images WHERE tour_id = ? ORDER BY position"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_images = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_images

def get_tour_stops(p_tour_id):
    query = "SELECT * FROM tour_stops WHERE tour_id = ? ORDER BY position"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_stops = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_stops

def get_tour_weekly_plan(p_tour_id):
    query = "SELECT * FROM tour_weekly_plan WHERE tour_id = ? ORDER BY day_of_week, start_time"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    db_weekly_plan = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_weekly_plan

def get_tours_by_guide(p_guide_id):
    query = "SELECT T.*, U.first_name, U.last_name, (SELECT TI.path_img FROM tour_images TI WHERE TI.tour_id = T.id ORDER BY TI.position LIMIT 1) AS path_img FROM tours T, users U WHERE T.guide_id = U.id AND T.guide_id = ? ORDER BY T.created_at DESC, T.id DESC"

    conn = sqlite3.connect("VisitAltamura_db.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (p_guide_id,))

    db_tours = cursor.fetchall()

    conn.commit()
    cursor.close()
    conn.close()

    return db_tours

def has_reservations(p_tour_id):
    # This function checks if there are any confirmed reservations for the given tour.
    query = "SELECT COUNT(*) FROM reservations WHERE tour_id = ? AND status = 'confirmed'"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    if count > 0:
        return True
    
    return False

def update_tour(p_tour_id, p_title, p_description, p_duration, p_language, p_meeting_point, p_max_participants):
    query = "UPDATE tours SET title = ?, description = ?, duration = ?, language = ?, meeting_point = ?, max_participants = ? WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_title, p_description, p_duration, p_language, p_meeting_point, p_max_participants, p_tour_id))

    conn.commit()
    cursor.close()
    conn.close()

def update_title_description_tour(p_tour_id, p_title, p_description):
    query = "UPDATE tours SET title = ?, description = ? WHERE id = ?"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_title, p_description, p_tour_id))

    conn.commit()
    cursor.close()
    conn.close()

def delete_tour(p_tour_id):
    #Deletes a tour only if it has never received a reservation.
    has_res = has_reservations(p_tour_id)

    if has_res:
        return False
    
    query = "DELETE FROM tours WHERE id = ?"
    #dovrei eliminare anche le tabelle tour_weekly_plan, stops e tour_images, ma grazie al vincolo di foreign key con ON DELETE CASCADE, vengono eliminate automaticamente quando elimino la riga della tabella tours.

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query, (p_tour_id,))

    conn.commit()
    cursor.close()
    conn.close()
    return True

def count_tours():
    query = "SELECT COUNT(*) FROM tours"

    conn = sqlite3.connect("VisitAltamura_db.db")
    cursor = conn.cursor()

    cursor.execute(query)

    count = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return count