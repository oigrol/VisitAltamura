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
            filter_date = ''

    if filter_language not in LANGUAGES:
        filter_language = ''

    if filter_duration not in ('', 'short', 'medium', 'long'):
        filter_duration = ''

    db_tours = tours_dao.get_tours_by_filters(filter_date, filter_language, filter_duration)
    db_guide_languages = languages_dao.get_guide_languages()

    count_guides = users_dao.count_guides()
    count_tours = tours_dao.count_tours()
    count_reservations = reservations_dao.count_reservations_confirmed()
    count_guide_languages = languages_dao.count_guide_languages()

    return render_template('index.html', 
                           p_tours=db_tours, 
                           p_guide_languages=db_guide_languages, 
                           p_count_guides=count_guides, 
                           p_count_tours=count_tours, 
                           p_count_reservations=count_reservations, 
                           p_count_guide_languages=count_guide_languages,  
                           p_filter_date=filter_date, 
                           p_filter_language=filter_language, 
                           p_filter_duration=filter_duration, 
                           today=today)


# --- Tour details ---

@app.route("/tours/<int:tour_id>")
def tour(tour_id):
    db_tour = tours_dao.get_tour_by_id(tour_id)
    if not db_tour:
        flash("Tour not found", "danger")
        return redirect(url_for("home"))
    
    db_stops = tours_dao.get_tour_stops(tour_id)
    db_weekly_plan = tours_dao.get_tour_weekly_plan(tour_id)
    guide_id = db_tour['guide_id']
    db_guide = users_dao.get_user_by_id(guide_id)
    '''if not db_guide:
        flash("Guide not found", "danger")
        return redirect(url_for("home"))'''
    
    images_path = []
    for image in tours_dao.get_tour_images(tour_id):
        images_path.append(image['path_img'])

    '''weekly_plan = [{
        'day_of_week': plan['day_of_week'],
        'start_time': plan['start_time']
        } for plan in tours_dao.get_tour_weekly_plan(tour_id)]

    guide_languages = languages_dao.get_languages_by_guide(guide_id)
    #stops = tours_dao.get_tour_stops(tour_id)'''

    return render_template("tour.html", p_tour=db_tour, p_images=images_path, p_stops=db_stops, p_weekly_plan=db_weekly_plan, p_guide=db_guide, p_days=DAYS)


# --- Authentication ---

@app.route("/signup")
def signup():
    #if current_user.is_authenticated:
        #return redirect(url_for("profile"))
    
    role = request.args.get('role', 'participant')
    if role not in ("participant", "guide"):
        role = "participant"
    return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = [])

@app.route("/register", methods=["POST"])
def register():
    #if current_user.is_authenticated:
        #return redirect(url_for("profile"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = generate_password_hash(request.form.get("password"), method='scrypt')
    role = request.form.get("role")   
    languages = request.form.getlist("languages")
    selected_languages = []
    for language in languages:
        if language in LANGUAGES:
            selected_languages.append(language)

    if not first_name or not last_name or not email or not password or not role:
        flash("Please complete all the required fields", "danger")
        return redirect(url_for("signup"))
    
    if role not in ("participant", "guide"):
        flash("Please select a valid role", "danger")
        return redirect(url_for("signup"))
    
    if role == "guide" and not selected_languages:
        flash("Please select at least one language for guides", "danger")
        return redirect(url_for("signup"))
    
    if users_dao.get_user_by_email(email):
        flash("The email is already registered", "danger")
        return redirect(url_for("signup"))

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
    #if current_user.is_authenticated:
        #return redirect(url_for("profile"))
    
    return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
    #if current_user.is_authenticated:
        #return redirect(url_for("profile"))
    
    form_user = request.form.to_dict() 

    db_user = users_dao.get_user_by_email(form_user["email"])

    #per evitare che il malintenzionato possa capire se l'email esiste o meno, si fa un controllo combinato: se l'utente non esiste o la password non corrisponde, si mostra lo stesso messaggio di errore
    if not db_user or not check_password_hash(db_user['password'], form_user['password']):
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
    
    return redirect(url_for("home"))

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

    guide_languages = languages_dao.get_languages_by_guide(user.id)
    
    db_tours = tours_dao.get_tours_by_guide(user.id)
    tours_data = []
    for tour in db_tours:
        has_reservations = tours_dao.has_reservations(tour['id'])
        tours_data.append({
            'tour': tour, 
            'has_reservations': has_reservations
            })
        #if tours have no reservations, the guide can delete them, otherwise not
        
    totals = {
        "tours": users_dao.count_tours_by_guide(user.id),
        "stops": users_dao.count_stops_by_guide(user.id),
        "reports_due": 0, #reports_dao.count_reports_due_by_guide(user.id)
        }
    
    return render_template("profile_guide.html", p_guide=user, p_guide_languages=guide_languages, p_totals=totals, p_tours_data=tours_data)

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
            if plan["day_of_week"] == tour_weekday:
                start_time = plan["start_time"]
                break
            
        #24h before the tour start time, the participant can cancel the reservation
        cancellable = False
        if reservation["status"] == "confirmed" and start_time is not None:
            tour_datetime = datetime.fromisoformat(reservation["tour_date"] + " " + start_time)
            cancellable = (tour_datetime - current_datetime >= timedelta(hours=24))
            #timedelta is the difference between two datetime objects, and we check if it's greater than or equal to 24 hours
            if tour_datetime >= current_datetime:
                upcoming_reservations.append({
                    "reservation": reservation,
                    "guests": guests,
                    "start_time": start_time,
                    "cancellable": cancellable
                    })
                number_upcoming_reservations += 1
                number_people += reservation["people_count"]
        elif tour_datetime < current_datetime:
            history_reservations.append({
            "reservation": reservation,
            "guests": guests,
            "start_time": start_time,
            "cancellable": cancellable
            })
            if ( reservation["status"] == "confirmed" ):
                number_completed_reservations += 1

    totals = {
        "upcoming": number_upcoming_reservations,
        "people": number_people, 
        "completed": number_completed_reservations }
    
    return render_template("profile_participant.html", p_participant=user, p_totals=totals, p_upcoming_reservations=upcoming_reservations, p_reservation_history=history_reservations)