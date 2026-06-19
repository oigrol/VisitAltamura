from datetime import date
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
    today = date.today().isoformat() #YYYY-MM-DD

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

# --- Authentication ---

@app.route("/signup")
def signup():
    role = request.args.get('role', 'participant')
    if role not in ("participant", "guide"):
        role = "participant"
    return render_template("registration.html", p_languages=LANGUAGES, selected_role = role, selected_languages = [])

@app.route("/register", methods=["POST"])
def register():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email").lower()
    password = generate_password_hash(request.form.get("password"), method='scrypt')
    role = request.form.get("role")        
    languages = request.form.getlist("languages")

    if not first_name or not last_name or not email or not password or not role:
        flash("Please complete all the required fields", "danger")
        return redirect(url_for("signup"))
    
    if role not in ("participant", "guide"):
        flash("Please select a valid role", "danger")
        return redirect(url_for("signup"))
    
    if role == "guide" and not languages:
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
        img_path = 'images/profile_imgs/user.jpg'


    users_dao.new_user(first_name, last_name, email, password, role, img_path)

    if role == 'guide':
        guide_id = users_dao.get_id_by_email(email)['id']
        for language in languages:
            if language in LANGUAGES:
                languages_dao.new_guide_language(guide_id, language)

    flash("Registration successful! You can now login.", "success")

    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
    form_user = request.form.to_dict() 

    db_user = users_dao.get_user_by_email(form_user["email"])

    if not db_user:
        flash("The user does not exist", "danger")
        return redirect(url_for("login"))
    elif not check_password_hash(db_user['password'], form_user['password']):
        flash("The password is wrong", "danger")
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

'''@app.route("/profile")
@login_required
def profile():
    user = current_user
    return render_template("profile.html", p_user=user)'''

@app.route("/tour/<int:tour_id>")
def tour(tour_id):
    db_tour = tours_dao.get_tour_by_id(tour_id)

    if not db_tour:
        flash("Tour not found", "danger")
        return redirect(url_for("home"))
    
    guide_id = db_tour['guide_id']
    db_guide = users_dao.get_user_by_id(guide_id)
    if not db_guide:
        flash("Guide not found", "danger")
        return redirect(url_for("home"))
    
    guide_languages = languages_dao.get_languages_by_guide(guide_id)
    images = tours_dao.get_tour_images(tour_id)

    return render_template("tour.html", p_tour=db_tour, p_guide=db_guide, p_guide_languages=guide_languages, p_images=images)