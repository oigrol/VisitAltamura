from datetime import date, datetime, timedelta
import email
import time

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from models import User
import languages_dao, reservations_dao, users_dao, tours_dao, reports_dao

LANGUAGES = ['Italian', 'English', 'Spanish', 'Portuguese', 'German']
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTHS = ['','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app = Flask(__name__)

app.config["SECRET_KEY"] = "Key for VisitAltamura"

login_manager = LoginManager() 
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

def get_upcoming_dates(p_weekly_plan):
    upcoming_dates = []
    today = date.today()
    current_datetime = datetime.now()

    #controllo i prossimi 91 giorni (13 settimane) per trovare le date corrispondenti al piano settimanale del tour
    p_weeks_end=13
    p_days_end = p_weeks_end * 7
    for i in range(p_days_end): 
        check_date = today + timedelta(days=i)
        for plan in p_weekly_plan:
            day_of_week = int(plan['day_of_week'])
            if day_of_week != check_date.weekday():
                continue
            
            check_datetime = datetime.fromisoformat(check_date.isoformat() + " " + plan['start_time'])
            if check_datetime <= current_datetime:
                continue

            upcoming_dates.append({
                "date": check_date.isoformat(),
                "day_of_week": DAYS[day_of_week],
                "start_time": plan['start_time']
            })

            break

    return upcoming_dates

def is_allowed_image(p_filename):
    filename = secure_filename(p_filename)
    if not filename or '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_IMAGE_EXTENSIONS

def is_allowed_time(p_time):
    try:
        datetime.strptime(p_time, "%H:%M")
        return True
    except ValueError:
        return False

@app.route('/')
def home():
    today = date.today().isoformat()

    #prende i filtri dalla query string (stringa URL), se presenti, altrimenti li imposta a stringa vuota
    filter_date = request.args.get('date', '').strip()
    filter_language = request.args.get('language', '').strip()
    filter_duration = request.args.get('duration', '').strip()

    if filter_date:
        try:
            filter_date = date.fromisoformat(filter_date)
            if filter_date < date.today():
                flash("Please do not choose a past date.", "danger")
                filter_date = ''
        except ValueError:
            filter_date = ''


    if filter_language not in LANGUAGES:
        filter_language = ''

    if filter_duration not in ('', 'short', 'medium', 'long'):
        filter_duration = ''

    db_tours = tours_dao.get_tours_by_filters(filter_date, filter_language, filter_duration)
    db_guide_languages = languages_dao.get_guide_languages()

    stats = {
        "count_guides": users_dao.count_guides(),
        "count_tours": tours_dao.count_tours(),
        "count_reservations": reservations_dao.count_reservations_confirmed(),
        "count_guide_languages": languages_dao.count_guide_languages()
    }

    return render_template('index.html', 
                           p_tours=db_tours, 
                           p_guide_languages=db_guide_languages, 
                           p_stats=stats, 
                           p_filter_date=filter_date, 
                           p_filter_language=filter_language, 
                           p_filter_duration=filter_duration, 
                           p_today=today)


# --- Tour ---

@app.route("/tours/<int:tour_id>")
def tour(tour_id):
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour:
        flash("Tour not found", "danger")
        return redirect(url_for("home"))
    
    db_stops = tours_dao.get_tour_stops(tour_id)
    db_weekly_plan = tours_dao.get_tour_weekly_plan(tour_id)
    db_has_reservations = tours_dao.has_confirmed_reservations(tour_id)

    guide_id = db_tour['guide_id']
    db_guide = users_dao.get_user_by_id(guide_id)
    if not db_guide:
        flash("Guide not found", "danger")
        return redirect(url_for("home"))
    
    images = []
    for image in tours_dao.get_tour_images(tour_id):
        images.append(image['path_img'])

    upcoming_dates = []
    if current_user.is_authenticated and current_user.role == 'participant':
        upcoming_dates = get_upcoming_dates(db_weekly_plan)

    return render_template("tour.html", p_tour=db_tour, p_images=images, p_stops=db_stops, p_weekly_plan=db_weekly_plan, p_has_reservations=db_has_reservations, p_upcoming_dates=upcoming_dates, p_guide=db_guide, p_days=DAYS)

@app.route("/tours/new_tour")
@login_required
def new_tour():
    user = current_user

    if user.role != 'guide':
        flash("Access denied: only guides can create tours", "danger")
        return redirect(url_for("home"))

    guide_languages = languages_dao.get_languages_by_guide(user.id)

    return render_template("new_tour.html", p_languages=guide_languages, p_days=DAYS)

@app.route("/tours/create", methods=["POST"])
@login_required
def create_tour():
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can create tours", "danger")
        return redirect(url_for("home"))
    
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    language = request.form.get("language", "").strip()
    duration = request.form.get("duration", "").strip()
    meeting_point = request.form.get("meeting_point", "").strip()
    max_participants = request.form.get("max_participants", "").strip()

    if not title or not description or not language or not duration or not meeting_point or not max_participants:
        flash("Please complete all the required fields", "danger")
        return redirect(url_for("new_tour"))
    
    if len(title) > 120 or len(meeting_point) > 200:
        flash("Title cannot exceed 120 characters and meeting point cannot exceed 200 characters.", "danger")
        return redirect(url_for("new_tour"))

    try:
        duration = int(duration)
        max_participants = int(max_participants)
    except ValueError:
        flash("Duration and max participants must be valid numbers.", "danger")
        return redirect(url_for("new_tour"))

    if duration <= 0 or max_participants <= 0:
        flash("Duration and max participants must be positive numbers", "danger")
        return redirect(url_for("new_tour"))
    
    guide_id = user.id
    guide_languages = languages_dao.get_languages_by_guide(guide_id)
    if language not in guide_languages:
        flash("You can only create tours in languages you speak", "danger")
        return redirect(url_for("new_tour"))
    
    weekly_plan = []
    for i, day in enumerate(DAYS):
        day_enabled = request.form.get(f"day_{i}", "")
        start_time = request.form.get(f"start_time_{i}", "").strip()
        if not day_enabled:
            continue
        if not start_time or not is_allowed_time(start_time):
            flash(f"Please select a start time for {day}", "danger")
            return redirect(url_for("new_tour"))
        weekly_plan.append({
            "day_of_week": i,
            "start_time": start_time
        })

    if not weekly_plan:
        flash("Please select at least one start time for the weekly plan", "danger")
        return redirect(url_for("new_tour"))
        
    db_stops =  request.form.getlist("stops")
    stops = []
    for i, stop in enumerate(db_stops, start=1):
        stop = stop.strip()
        if stop:
            stops.append({
                "position": i,
                "name": stop
            })

    if len(stops) < 4:
        flash("Please add at least 4 stops", "danger")
        return redirect(url_for("new_tour"))
    
    images = request.files.getlist("images")
    valid_images = [image for image in images if image and image.filename != '']
    if len(valid_images) != 5:
        flash("Please upload exactly 5 images for the tour", "danger")
        return redirect(url_for("new_tour"))
    if not all(is_allowed_image(image.filename) for image in valid_images):
        flash("Invalid image format. Allowed formats: png, jpg, jpeg, webp", "danger")
        return redirect(url_for("new_tour"))

    image_paths = []
    for position, image in enumerate(valid_images, start=1):
        filename_old = secure_filename(image.filename)
        filename_new = f"{int(time.time())}_{filename_old}"
        img_path = "images/tours/" + filename_new
        image.save("static/" + img_path)
        image_paths.append({
            "position": position,
            "path_img": img_path
        })

    tours_dao.new_tour(title, description, guide_id, duration, language, meeting_point, max_participants, weekly_plan, stops, image_paths)
    flash("Tour created successfully!", "success")
    return redirect(url_for("profile_guide"))
    

@app.route("/tours/<int:tour_id>/edit")
@login_required
def edit_tour(tour_id):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can edit tours", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to edit this tour", "danger")
        return redirect(url_for("profile_guide"))
    
    guide_languages = languages_dao.get_languages_by_guide(user.id)
    db_stops = tours_dao.get_tour_stops(tour_id)
    db_weekly_plan = tours_dao.get_tour_weekly_plan(tour_id)
    db_images = tours_dao.get_tour_images(tour_id)
    db_has_reservations = tours_dao.has_reservations(tour_id)

    return render_template("edit_tour.html", p_tour=db_tour, p_languages=guide_languages, p_stops=db_stops, p_weekly_plan=db_weekly_plan, p_images=db_images, p_days=DAYS, p_has_reservations=db_has_reservations)

@app.route("/tours/<int:tour_id>/update", methods=["POST"])
@login_required
def update_tour(tour_id):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can update tours", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to update this tour", "danger")
        return redirect(url_for("profile_guide"))
    
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Please complete all the required fields", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    db_has_reservation = tours_dao.has_reservations(tour_id)
    if db_has_reservation:
        tours_dao.update_tour_with_reservations(tour_id, title, description)
        flash("Tour updated successfully!", "success")
        return redirect(url_for("profile_guide"))
    
    # If the tour has no reservations, allow updating all fields
    language = request.form.get("language", "").strip()
    duration = request.form.get("duration", "").strip()
    meeting_point = request.form.get("meeting_point", "").strip()
    max_participants = request.form.get("max_participants", "").strip()

    if not language or not duration or not meeting_point or not max_participants:
        flash("Please complete all the required fields", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    if len(title) > 120 or len(meeting_point) > 200:
        flash("Title cannot exceed 120 characters and meeting point cannot exceed 200 characters.", "danger")
        return redirect(url_for("new_tour"))
    
    try:
        duration = int(duration)
        max_participants = int(max_participants)
    except ValueError:
        flash("Duration and max participants must be valid numbers.", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    if duration <= 0 or max_participants <= 0:
        flash("Duration and max participants must be positive numbers", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))

    guide_id = user.id
    guide_languages = languages_dao.get_languages_by_guide(guide_id)
    if language not in guide_languages:
        flash("You can only create tours in languages you speak", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    weekly_plan = []
    for i, day in enumerate(DAYS):
        day_enabled = request.form.get(f"day_{i}", "")
        start_time = request.form.get(f"start_time_{i}", "").strip()
        if not day_enabled:
            continue
        if not start_time or not is_allowed_time(start_time):
            flash(f"Please select a start time for {day}", "danger")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        weekly_plan.append({
            "day_of_week": i,
            "start_time": start_time
        })

    if not weekly_plan:
        flash("Please select at least one start time for the weekly plan", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    db_stops =  request.form.getlist("stops")
    stops = []

    for stop in db_stops:
        stop = stop.strip()
        if stop:
            stops.append({
                "position": len(stops) + 1,
                "name": stop
            })

    if len(stops) < 4:
        flash("Please add at least 4 stops to the tour", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    updated_image_paths = []
    for position in range(1, 6):
        image = request.files.get(f"image_{position}")
        if image is None or not image.filename:
            continue

        if not is_allowed_image(image.filename):
            flash(f"Invalid image format for image {position}. Allowed formats: png, jpg, jpeg, webp", "danger")
            return redirect(url_for("edit_tour", tour_id=tour_id))

        filename_old = secure_filename(image.filename)
        filename_new = f"{int(time.time())}_{filename_old}"
        img_path = "images/tours/" + filename_new
        image.save("static/" + img_path)
        updated_image_paths.append({
            "position": position, 
            "path_img": img_path
        })

    tours_dao.update_tour(tour_id, title, description, duration, language, meeting_point, max_participants, weekly_plan, stops, updated_image_paths)

    flash("Tour updated successfully!", "success")
    return redirect(url_for("profile_guide"))

@app.route("/tours/<int:tour_id>/delete", methods=["POST"])
@login_required
def delete_tour(tour_id):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can delete tours", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to delete this tour", "danger")
        return redirect(url_for("profile_guide"))
    
    if tours_dao.has_reservations(tour_id):
        flash("Cannot delete a tour that has reservation history, including possible cancelled reservations.", "danger")
        return redirect(url_for("edit_tour", tour_id=tour_id))
    
    tours_dao.delete_tour(tour_id)
    flash("Tour deleted successfully!", "success")
    return redirect(url_for("profile_guide"))


# --- Reservations ---
@app.route("/tours/<int:tour_id>/reserve", methods=["POST"])
@login_required
def reserve_tour(tour_id):
    user = current_user
    if user.role != 'participant':
        flash("Access denied: only participants can reserve tours", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour:
        flash("Tour not found", "danger")
        return redirect(url_for("home"))
    
    tour_date_str = request.form.get("tour_date", "").strip()
    guests = request.form.get("guests", "0").strip()

    if not tour_date_str or not guests:
        flash("Please select a date and number of guests", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    try:
        tour_date = date.fromisoformat(tour_date_str)
    except ValueError:
        flash("Invalid date.", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    if tour_date < date.today():
        flash("Please select a future date.", "danger")
        return redirect(url_for("tour", tour_id=tour_id))

    try:
        guests = int(guests)
    except ValueError:
        flash("Guests must be valid numbers.", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    if guests < 0 or guests > 3:
        flash("Number of guests must be between 0 and 3", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    people_count = 1 + guests

    already_reserved = reservations_dao.get_reservation(user.id, tour_id, tour_date_str)
    if already_reserved:
        flash("You have already reserved this tour on the selected date", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    booked_places = reservations_dao.count_people_for_tour_date(tour_id, tour_date_str)
    if booked_places is None:
        booked_places = 0
    available_places = db_tour['max_participants'] - booked_places
    if people_count > available_places:
        flash("Not enough available places for the selected date. Only " + str(available_places) + " places available. Select a different date or reduce the number of guests.", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    db_weekly_plan = tours_dao.get_tour_weekly_plan(tour_id)
    tour_weekday = tour_date.weekday()
    start_time = None
    for plan in db_weekly_plan:
        if int(plan["day_of_week"]) == tour_weekday:
            start_time = plan['start_time']
            break
    
    if start_time is None:
        flash("The selected date does not match the tour's weekly plan", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    tour_datetime = datetime.fromisoformat(tour_date_str + " " + start_time)
    if tour_datetime < datetime.now():
        flash("You cannot reserve a tour in the past", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
        
    if reservations_dao.check_conflicting_reservation(user.id, tour_date_str, tour_id, start_time, db_tour['duration']):
        flash("You already have a reservation for another tour at the same date and time", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    guest_first_names = request.form.getlist("guest_first_names")
    guest_last_names = request.form.getlist("guest_last_names")
    if len(guest_first_names) != guests or len(guest_last_names) != guests:
        flash("Please provide first and last names for all guests", "danger")
        return redirect(url_for("tour", tour_id=tour_id))
    
    guests_full_names = []
    for i in range(guests):
        guest_first_name = guest_first_names[i].strip()
        guest_last_name = guest_last_names[i].strip()
        if not guest_first_name or not guest_last_name:
            flash(f"Please provide the first and last names for guest {i + 1}", "danger")
            return redirect(url_for("tour", tour_id=tour_id))
        guests_full_names.append({
            "first_name": guest_first_name,
            "last_name": guest_last_name
        })
    
    reservation_id = reservations_dao.new_reservation(user.id, tour_id, tour_date_str, people_count, "confirmed", guests_full_names)

    if not reservation_id:
        flash("Error creating reservation", "danger")
        return redirect(url_for("tour", tour_id=tour_id))

    flash("Reservation successful!", "success")
    return redirect(url_for("profile_participant"))

@app.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation(reservation_id):
    user = current_user
    if user.role != 'participant':
        flash("Access denied: only participants can cancel reservations", "danger")
        return redirect(url_for("home"))
    
    db_reservation = reservations_dao.get_reservation_by_id(reservation_id)
    if not db_reservation or db_reservation['participant_id'] != user.id:
        flash("Reservation not found", "danger")
        return redirect(url_for("home"))

    if db_reservation['status'] == 'cancelled':
        flash("Reservation is already cancelled", "danger")
        return redirect(url_for("profile_participant"))
    
    tour_weekday = date.fromisoformat(db_reservation['tour_date']).weekday()
    weekly_plan = tours_dao.get_tour_weekly_plan(db_reservation['tour_id'])
    start_time = None
    for plan in weekly_plan:
        if int(plan["day_of_week"]) == tour_weekday:
            start_time = plan['start_time']
            break
    
    if not start_time:
        flash("Could not find the start time for the tour on the reservation date", "danger")
        return redirect(url_for("profile_participant"))
    
    tour_datetime = datetime.fromisoformat(db_reservation['tour_date'] + " " + start_time)
    if datetime.now() > tour_datetime - timedelta(hours=24):
        flash("You can only cancel reservations at least 24 hours before the tour starts", "danger")
        return redirect(url_for("profile_participant"))
    
    reservations_dao.cancel_reservation(reservation_id)
    flash("Reservation cancelled successfully", "success")
    return redirect(url_for("profile_participant"))


# --- Reservation ---
@app.route("/tours/<int:tour_id>/reservations")
@login_required
def tour_reservations(tour_id):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can view reservations", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to view reservations for this tour", "danger")
        return redirect(url_for("profile_guide"))

    reservation_dates = reservations_dao.get_dates_with_confirmed_reservations(tour_id)
    cancelled_reservation_dates = reservations_dao.get_dates_with_cancelled_reservations(tour_id)
    current_datetime = datetime.now()

    upcoming_reservations = []
    pending_reports_reservations = []
    completed_reports_reservations = []
    cancelled_reservations = []

    for reservation_date in reservation_dates:
        reservation_tour_in_date = reservations_dao.get_reservations_for_tour_date(tour_id, reservation_date['tour_date'])
        guests_per_reservation = {}
        for reservation in reservation_tour_in_date:
            guests_per_reservation[reservation['id']] = reservations_dao.get_guests_by_reservation(reservation['id'])

        tour_start_datetime = datetime.fromisoformat(reservation_date['tour_date'] + " " + reservation_date['start_time'])
        tour_end_datetime = tour_start_datetime + timedelta(minutes=db_tour['duration'])
        is_past_reservation = tour_end_datetime < current_datetime

        if is_past_reservation:
            report = reports_dao.get_report(tour_id, reservation_date['tour_date'])
        else:
            report = None
        
        reservation_info = {
            'tour_date': reservation_date['tour_date'],
            'start_time': reservation_date['start_time'],
            "expected_people": reservation_date['expected_people'],
            "reservations": reservation_tour_in_date,
            "guests_per_reservation": guests_per_reservation,
            "is_past_reservation": is_past_reservation,
            "report": report
        }
        if is_past_reservation:
            if report:
                completed_reports_reservations.append(reservation_info)
            else:
                pending_reports_reservations.append(reservation_info)
        else:
            upcoming_reservations.append(reservation_info)

    completed_reports_reservations.reverse()
        
    for reservation_date in cancelled_reservation_dates:
        reservation_tour_in_date = reservations_dao.get_cancelled_reservations_for_tour_date(tour_id, reservation_date['tour_date'])
        guests_per_reservation = {}
        for reservation in reservation_tour_in_date:
            guests_per_reservation[reservation['id']] = reservations_dao.get_guests_by_reservation(reservation['id'])
        
        reservation_info = {
            'tour_date': reservation_date['tour_date'],
            'start_time': reservation_date['start_time'],
            "cancelled_people": reservation_date['cancelled_people'],
            "reservations": reservation_tour_in_date,
            "guests_per_reservation": guests_per_reservation,
        }
        cancelled_reservations.append(reservation_info)

    totals = {
        "upcoming_reservations": len(upcoming_reservations),
        "pending_reports": len(pending_reports_reservations),
        "completed_reports": len(completed_reports_reservations),
    }

    return render_template("tour_reservations.html", p_tour=db_tour, p_upcoming_reservations=upcoming_reservations, p_pending_reports_reservations=pending_reports_reservations, p_completed_reports_reservations=completed_reports_reservations, p_cancelled_reservations=cancelled_reservations, p_totals=totals, p_months=MONTHS)

@app.route("/tours/<int:tour_id>/report/<tour_date>")
@login_required
def tour_report(tour_id, tour_date):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can view reports", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to view the report for this tour", "danger")
        return redirect(url_for("profile_guide"))

    report = reports_dao.get_report(tour_id, tour_date)
    if report:
        flash("Report already submitted for this tour and date", "warning")
        return redirect(url_for("tour_reservations", tour_id=tour_id))
 
    try:
        date.fromisoformat(tour_date)
    except ValueError:
        flash("Invalid date format", "danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))

    reservation_dates = reservations_dao.get_dates_with_confirmed_reservations(tour_id, tour_date)

    if not reservation_dates:
        flash("No confirmed reservations found for this tour and date", "danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))
    
    reservation_dates_ok = reservation_dates[0]

    start_datetime = datetime.fromisoformat(reservation_dates_ok['tour_date'] + " " + reservation_dates_ok['start_time'])
    end_datetime = start_datetime + timedelta(minutes=db_tour['duration'])
    if end_datetime > datetime.now():
        flash("You can only submit a report after the tour has ended", "danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))
    
    expected_people = reservation_dates_ok['expected_people']
    start_time = reservation_dates_ok['start_time']

    return render_template("tour_report.html", p_tour=db_tour, p_tour_date=tour_date, p_start_time=start_time, p_expected_people=expected_people)

@app.route("/tours/<int:tour_id>/report/<tour_date>/submit", methods=["POST"])
@login_required
def submit_tour_report(tour_id, tour_date):
    user = current_user
    if user.role != 'guide':
        flash("Access denied: only guides can submit reports", "danger")
        return redirect(url_for("home"))
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour or db_tour['guide_id'] != user.id:
        flash("Tour not found or you do not have permission to submit the report for this tour", "danger")
        return redirect(url_for("profile_guide"))

    report = reports_dao.get_report(tour_id, tour_date)
    if report:
        flash("Report already submitted for this tour and date", "warning")
        return redirect(url_for("tour_reservations", tour_id=tour_id))
        
    try:
        date.fromisoformat(tour_date)
    except ValueError:
        flash("Invalid date format", "danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))

    reservation_dates = reservations_dao.get_dates_with_confirmed_reservations(tour_id,tour_date)

    if not reservation_dates:
        flash("No confirmed reservations found for this tour and date","danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))

    reservation_date_ok = reservation_dates[0]

    start_datetime = datetime.fromisoformat(reservation_date_ok["tour_date"]+ " "+ reservation_date_ok["start_time"])
    end_datetime = start_datetime + timedelta(minutes=db_tour["duration"])
    if end_datetime > datetime.now():
        flash("You can only submit a report after the tour has ended","danger")
        return redirect(url_for("tour_reservations", tour_id=tour_id))

    final_participants_count = request.form.get("final_participants_count", "").strip()
    if not final_participants_count:
        flash("Please provide the final number of participants", "danger")
        return redirect(url_for("tour_report", tour_id=tour_id, tour_date=tour_date))

    expected_people = reservation_date_ok["expected_people"]
    
    try:
        final_participants_count = int(final_participants_count)
    except ValueError:
        flash("Final participants count must be a valid number.", "danger")
        return redirect(url_for("tour_report", tour_id=tour_id, tour_date=tour_date))
    
    if final_participants_count < 0 or final_participants_count > expected_people:
        flash("Final number of participants cannot be negative and cannot exceed the number of expected participants.", "danger")
        return redirect(url_for("tour_report", tour_id=tour_id, tour_date=tour_date))

    group_img = request.files.get('group_img')
    group_img_path = None
    if group_img and group_img.filename != '':
        if not is_allowed_image(group_img.filename):
            flash("Invalid group image format. Allowed formats: png, jpg, jpeg, webp", "danger")
            return redirect(url_for("tour_report", tour_id=tour_id, tour_date=tour_date))
        
        filename_old = secure_filename(group_img.filename)
        filename_new = f"{int(time.time())}_{filename_old}"
        group_img_path = "images/reports/" + filename_new
        group_img.save("static/" + group_img_path)

    if not group_img_path:
        flash("Please upload a group image for the report", "danger")
        return redirect(url_for("tour_report", tour_id=tour_id, tour_date=tour_date))
    
    reports_dao.new_report(tour_id, tour_date, final_participants_count, group_img_path)
    flash("Report submitted successfully!", "success")
    return redirect(url_for("tour_reservations", tour_id=tour_id))



# --- Authentication ---

@app.route("/signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    
    role = request.args.get('role', 'participant')
    if role not in ("participant", "guide"):
        role = "participant"
    return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = [], first_name='', last_name='', email='')

@app.route("/register", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role")   

    languages = request.form.getlist("languages")
    selected_languages = [language for language in languages if language in LANGUAGES]

    if not first_name or not last_name or not email or not password or not role:
        flash("Please complete all the required fields", "danger")
        return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)
    
    if len(first_name) > 80 or len(last_name) > 80:
        flash("First name and last name cannot exceed 80 characters.", "danger")
        return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)

    if role not in ("participant", "guide"):
        flash("Please select a valid role", "danger")
        return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)
                
    if role == "guide" and not selected_languages:
        flash("Please select at least one language for guides", "danger")
        return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)
    
    if users_dao.get_user_by_email(email):
        flash("The email is already registered", "danger")
        return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)

    password = generate_password_hash(password, method='scrypt')
    
    profile_img = request.files.get('profile_img')
    img_path = None
    if profile_img and profile_img.filename != '':
        if not is_allowed_image(profile_img.filename):
            flash("Invalid profile image format. Allowed formats: png, jpg, jpeg, webp", "danger")
            return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = selected_languages, first_name=first_name, last_name=last_name, email=email)
        
        filename_old = secure_filename(profile_img.filename)
        filename_new = f"{int(time.time())}_{filename_old}"
        img_path = "images/profile_imgs/" + filename_new
        profile_img.save("static/" + img_path)

    users_dao.new_user(first_name, last_name, email, password, role, img_path, selected_languages)

    flash("Registration successful! You can now login.", "success")
    return redirect(url_for("login"))

@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    
    return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    db_user = users_dao.get_user_by_email(email)

    #per evitare che il malintenzionato possa capire se l'email esiste o meno, si fa un controllo combinato: se l'utente non esiste o la password non corrisponde, si mostra lo stesso messaggio di errore
    if not db_user or not check_password_hash(db_user['password'], password):
        flash("The user does not exist or the password is wrong", "danger")
        return redirect(url_for("login"))
    
    new = User(
        id = db_user["id"],
        first_name = db_user["first_name"],
        last_name = db_user["last_name"],
        email = db_user["email"],
        password = db_user["password"],
        role = db_user["role"],
        profile_img = db_user["profile_img"]
    )

    login_user(new)
    flash("Welcome back! " + db_user["first_name"] + " " + db_user["last_name"] + "!", "success")
    
    return redirect(url_for("profile"))

@login_manager.user_loader
def load_user(user_id):
    db_user = users_dao.get_user_by_id(user_id)
    if db_user is not None:
        user = User(
            id = db_user['id'],
            first_name = db_user['first_name'],
            last_name = db_user['last_name'],
            email = db_user['email'],
            password = db_user['password'],
            role = db_user['role'],
            profile_img = db_user['profile_img'],
        )
    else:
        user = None
        
    return user

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for("home"))

@app.route("/profile")
@login_required
def profile():
    user = current_user
    if user.role == 'guide':
        return redirect(url_for("profile_guide"))
    elif user.role == 'participant':
        return redirect(url_for("profile_participant"))
    return redirect(url_for("home"))

@app.route("/profile/guide")
@login_required
def profile_guide():
    user = current_user
    if user.role != 'guide':
        flash("Access denied: this page is only for guides", "danger")
        return redirect(url_for("home"))

    current_datetime = datetime.now()

    guide_languages = languages_dao.get_languages_by_guide(user.id)
    
    tours_data = []

    db_tours = tours_dao.get_tours_by_guide(user.id)
    for tour in db_tours:
        reservation_dates = reservations_dao.get_dates_with_confirmed_reservations(tour['id'])
        has_any_reservations = tours_dao.has_reservations(tour['id'])
        next_reservations = []

        #if tours have no reservations, the guide can delete them, otherwise not

        for reservation_date in reservation_dates:
            tour_date = reservation_date['tour_date']
            tour_start_time = reservation_date['start_time']
            tour_start_datetime = datetime.fromisoformat(tour_date + " " + tour_start_time)
            tour_end_datetime = tour_start_datetime + timedelta(minutes=tour['duration'])

            if tour_end_datetime >= current_datetime:
                next_reservations.append({
                    'tour_date': tour_date,
                    'start_time': tour_start_time,
                    'expected_people': reservation_date['expected_people'],
                    'total_people': tour['max_participants']
                })

        tours_data.append({
            'tour': tour, 
            'has_any_reservations': has_any_reservations,
            'next_reservations': next_reservations[:5]  # Limit to first 5 upcoming reservations
            })

    totals = {
        "tours": users_dao.count_tours_by_guide(user.id),
        "stops": users_dao.count_stops_by_guide(user.id),
        "reservations": users_dao.count_active_reservations_by_guide(user.id)
    }
    
    return render_template("profile_guide.html", p_guide=user, p_guide_languages=guide_languages, p_totals=totals, p_tours_data=tours_data)

@app.route("/profile/participant")
@login_required
def profile_participant():
    user = current_user
    if user.role != 'participant':
        flash("Access denied: this page is only for participants", "danger")
        return redirect(url_for("home"))
    
    current_datetime = datetime.now() 

    db_reservations = reservations_dao.get_reservations_for_participant(user.id)

    number_people = 0
    upcoming_reservations = []
    number_upcoming_reservations = 0
    history_reservations = []
    number_completed_reservations = 0
    for reservation in db_reservations: 
        guests = reservations_dao.get_guests_by_reservation(reservation["id"])
        #un tour può avere al massimo un orario di partenza per ogni giorno della settimana.
        tour_weekday = date.fromisoformat(reservation["tour_date"]).weekday()
        weekly_plan = tours_dao.get_tour_weekly_plan(reservation["tour_id"])
        start_time = None
        for plan in weekly_plan:
            if int(plan["day_of_week"]) == tour_weekday:
                start_time = plan["start_time"]
                break
            
        #24h before the tour start time, the participant can cancel the reservation
        cancellable = False
        if start_time is not None:
            tour_datetime = datetime.fromisoformat(reservation["tour_date"] + " " + start_time)

            if reservation["status"] == "cancelled":
                history_reservations.append({
                    "reservation": reservation,
                    "guests": guests,
                    "start_time": start_time,
                    "cancellable": cancellable
                })

            elif reservation["status"] == "confirmed":
                if tour_datetime > current_datetime:
                    cancellable = (tour_datetime - current_datetime >= timedelta(hours=24))
                    #timedelta is the difference between two datetime objects, and we check if it's greater than or equal to 24 hours
                    upcoming_reservations.append({
                        "reservation": reservation,
                        "guests": guests,
                        "start_time": start_time,
                        "cancellable": cancellable
                        })
                    number_upcoming_reservations += 1
                    number_people += reservation["people_count"]
                else:
                    history_reservations.append({
                        "reservation": reservation,
                        "guests": guests,
                        "start_time": start_time,
                        "cancellable": cancellable
                    })
                    number_completed_reservations += 1


    totals = {
        "upcoming": number_upcoming_reservations,
        "people": number_people, 
        "completed": number_completed_reservations 
        }
    
    return render_template("profile_participant.html", p_participant=user, p_totals=totals, p_upcoming_reservations=upcoming_reservations, p_reservation_history=history_reservations)


@app.route("/admin")
@login_required
def admin():
    user = current_user
    if user.role != 'admin':
        flash("Access denied: this page is only for administrators", "danger")
        return redirect(url_for("home"))
    
    stats = {
        "count_guides": users_dao.count_guides(),
        "count_participants": users_dao.count_participants(),
        "count_tours": tours_dao.count_tours(),
        "count_reservations": reservations_dao.count_reservations()
    }

    reservations_by_lang = reservations_dao.get_reservations_by_language()

    guides_data = []

    db_guides = users_dao.get_guides()
    for guide in db_guides:
        guide_tours = []
        db_tours = tours_dao.get_tours_by_guide(guide['id'])

        for tour in db_tours:
            guide_tours.append({
                'tour': tour,
                'weekly_plan': tours_dao.get_tour_weekly_plan(tour['id']),
                'stops': tours_dao.get_tour_stops(tour['id']),
                'images': tours_dao.get_tour_images(tour['id']),
            })

        guides_data.append({
            'guide': guide,
            'languages': languages_dao.get_languages_by_guide(guide['id']),
            'tours': guide_tours
        })
    
    return render_template("admin.html", p_stats=stats, p_reservations_by_lang=reservations_by_lang, p_guides_data=guides_data, p_days=DAYS)

