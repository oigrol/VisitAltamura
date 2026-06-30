# VisitAltamura

VisitAltamura is a Flask web application for managing free walking tours in Altamura.
The project was developed for the Introduction to Web Applications exam.

## Technologies

- Python
- Flask
- Flask-Login
- SQLite
- HTML5
- CSS3
- Bootstrap
- JavaScript
- Jinja templates

## Target Device

The application is designed primarily for desktop browsers and includes some responsive adaptations for smaller screens.

## Deployment URL

PythonAnywhere URL:

```text
s322424Giovanni.pythonanywhere.com
```

## Local Test Instructions

1. Extract the project archive.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment, if desired.
4. Install the dependencies:

```bash
pip install -r requirements.txt
```

5. Run the application:

```bash
flask --app app run
```

6. Open the local application in the browser:

```text
http://127.0.0.1:5000
```

The application uses the SQLite database file included in the project:

```text
VisitAltamura_db.db
```

No additional database setup is required for normal testing.

## Included Files

- `app.py`: main Flask application and route definitions.
- `models.py`: Flask-Login user model.
- `users_dao.py`: user and profile database queries.
- `languages_dao.py`: guide language database queries.
- `tours_dao.py`: tour, schedule, stop, and image database queries.
- `reservations_dao.py`: reservation and guest database queries.
- `reports_dao.py`: post-tour report database queries.
- `populate_db.py`: script used to recreate the sample database.
- `VisitAltamura_db.db`: SQLite database used by the application.
- `templates/`: Jinja HTML templates.
- `static/`: CSS, JavaScript, images, tour photos, profile images, and report images.

## Accounts Credentials

| Role | Email | Password | Notes |
| --- | --- | --- | --- |
| Guide | `valentina@visitaltamura.it` | `valentina123` | Italian guide |
| Guide | `marco@visitaltamura.it` | `marco123` | English and German guide |
| Guide | `carmen@visitaltamura.it` | `carmen123` | Spanish and Portuguese guide |
| Participant | `alice@visitaltamura.it` | `alice123` | Participant with reservations |
| Participant | `luca@visitaltamura.it` | `luca123` | Participant with reservations |
| Participant | `emma@visitaltamura.it` | `emma123` | Participant with reservations |
| Administrator | `admin@visitaltamura.it` | `admin123` | Admin profile |

## Type of Accounts

### Public Visitor

- Browse all tours

### Participant

- Log in / Sign up
- Profile page
- Reserve or cancel a tour date

### Guide

- Log in / Sign up
- Profile page
- Create a new tour
- Edit tours
- Reservations page for each tour.
- Post-tour report

### Administrator

The administrator page shows:
- total number of guides;
- total number of participants;
- total number of tours;
- total number of reservations;
- reservations grouped by language;
- guide list with guide languages and created tours.


## The Sample Database

The submitted project already includes `VisitAltamura_db.db`.