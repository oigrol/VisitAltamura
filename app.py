from datetime import date, datetime, timedelta
import time

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from models import User
import languages_dao, reservations_dao, users_dao, tours_dao, reports_dao

LANGUAGES = ['Italian', 'English', 'Spanish', 'Portuguese', 'German']
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

app = Flask(__name__)

app.config["SECRET_KEY"] = "Key for VisitAltamura"

login_manager = LoginManager() 
login_manager.init_app(app)

@app.route('/')
def home():
    today = date.today().isoformat()

    #prende i filtri dalla query string (stringa URL), se presenti, altrimenti li imposta a stringa vuota
    filter_date = request.args.get('date', '').strip()
    filter_language = request.args.get('language', '').strip()
    filter_duration = request.args.get('duration', '').strip()

    if filter_date:
        filter_date = date.fromisoformat(filter_date) #converte la stringa in oggetto date
        if filter_date < date.today():
            flash("Please do not choose a past date.", "danger")
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
    today = date.today().isoformat()
    
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour:
        flash("Tour not found", "danger")
        return redirect(url_for("home"))
    
    db_stops = tours_dao.get_tour_stops(tour_id)
    db_weekly_plan = tours_dao.get_tour_weekly_plan(tour_id)

    guide_id = db_tour['guide_id']
    db_guide = users_dao.get_user_by_id(guide_id)
    if not db_guide:
        flash("Guide not found", "danger")
        return redirect(url_for("home"))
    
    images = []
    for image in tours_dao.get_tour_images(tour_id):
        images.append(image['path_img'])

    return render_template("tour.html", p_tour=db_tour, p_images=images, p_stops=db_stops, p_weekly_plan=db_weekly_plan, p_guide=db_guide, p_days=DAYS, p_today=today)

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
    
    duration = int(duration)
    max_participants = int(max_participants)
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
        if not start_time:
            flash(f"Please select a start time for {day}", "danger")
            return redirect(url_for("edit_tour", tour_id=tour_id))
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
    if len(images) != 5:
        flash("Please upload exactly 5 images for the tour", "danger")
        return redirect(url_for("new_tour"))

    image_paths = []
    for position, image in enumerate(images, start=1):
        if image and image.filename != '':
            filename_old = secure_filename(image.filename)
            filename_new = f"{int(time.time())}_{filename_old}"
            img_path = "images/tour_imgs/" + filename_new
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
    
    duration = int(duration)
    max_participants = int(max_participants)
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
        if not start_time:
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
    for i, stop in enumerate(db_stops, start=1):
        stop = stop.strip()
        if not stop:
            flash(f"Please provide a name for stop {i}", "danger")
            return redirect(url_for("edit_tour", tour_id=tour_id))
        stops.append({
            "position": i,
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
        flash("Cannot delete a tour that has reservations", "danger")
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
    
    tour_date = request.form.get("tour_date", "").strip()
    guests = request.form.get("guests", "").strip()

    


# --- Authentication ---

@app.route("/signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    
    role = request.args.get('role', 'participant')
    if role not in ("participant", "guide"):
        role = "participant"
    return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = [])

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
    selected_languages = []
    for language in languages:
        if language in LANGUAGES:
            selected_languages.append(language)

    if not first_name or not last_name or not email or not password or not role:
        flash("Please complete all the required fields", "danger")
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
    if profile_img and profile_img.filename != '':
        filename_old = secure_filename(profile_img.filename)
        filename_new = f"{int(time.time())}_{filename_old}"
        img_path = "images/profile_imgs/" + filename_new
        profile_img.save("static/" + img_path)
    else:
        img_path = None

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
    else:
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
    if current_user.role != 'guide':
        flash("Access denied: this page is only for guides", "danger")
        return redirect(url_for("home"))

    user = current_user
    current_datetime = datetime.now()

    guide_languages = languages_dao.get_languages_by_guide(user.id)
    
    tours_data = []
    missing_reports = []
    completed_reports = []

    db_tours = tours_dao.get_tours_by_guide(user.id)
    for tour in db_tours:
        reservation_dates = reservations_dao.get_dates_with_confirmed_reservations_for_tour(tour['id'])
        has_reservations = tours_dao.has_reservations(tour['id'])
        tours_data.append({
            'tour': tour, 
            'has_reservations': has_reservations
            })
        #if tours have no reservations, the guide can delete them, otherwise not

        for reservation_date in reservation_dates:
            tour_date = reservation_date['tour_date']
            tour_start_time = reservation_date['start_time']
            tour_start_datetime = datetime.fromisoformat(tour_date + " " + tour_start_time)
            tour_end_datetime = tour_start_datetime + timedelta(minutes=tour['duration'])

            '''if tour_end_datetime < current_datetime:
                report = reports_dao.get_report_by_tour_and_date(tour['id'], tour_date)
                tour_info = {
                    'tour': tour,
                    'tour_date': tour_date,
                    'start_time': tour_start_time,
                    "expected_people": reservation_date['expected_people'],
                    "report": report
                }
                if report:
                    completed_reports.append(tour_info)
                else:
                    missing_reports.append(tour_info)'''

    totals = {
        "tours": users_dao.count_tours_by_guide(user.id),
        "stops": users_dao.count_stops_by_guide(user.id),
        "missing_reports": len(missing_reports),
        }
    
    return render_template("profile_guide.html", p_guide=user, p_guide_languages=guide_languages, p_totals=totals, p_tours_data=tours_data, p_missing_reports=missing_reports, p_completed_reports=completed_reports)

@app.route("/profile/participant")
@login_required
def profile_participant():
    if current_user.role != 'participant':
        flash("Access denied: this page is only for participants", "danger")
        return redirect(url_for("home"))
    
    user = current_user    
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

