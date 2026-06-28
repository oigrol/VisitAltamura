"""
populate_db.py — VisitAltamura full database population script
Run from project root: python populate_db.py

Test reference dates:
  2026-06-28 (Sunday)    — today / start testing  (verified: date.weekday()=6)
  2026-07-01 (Wednesday) — presentation day        (verified: date.weekday()=2)

Calendar verification (Python date.weekday() — 0=Mon … 6=Sun):
  Jun 21 = Sun(6)   Jun 22 = Mon(0)   Jun 23 = Tue(1)   Jun 24 = Wed(2)
  Jun 25 = Thu(3)   Jun 26 = Fri(4)   Jun 27 = Sat(5)   Jun 28 = Sun(6)
  Jul  1 = Wed(2)   Jul  2 = Thu(3)   Jul  4 = Sat(5)   Jul  5 = Sun(6)
  Jul  6 = Mon(0)   Jul  7 = Tue(1)   Jul  8 = Wed(2)   Jul  9 = Thu(3)
  Jul 10 = Fri(4)   Jul 11 = Sat(5)   Jul 12 = Sun(6)   Jul 14 = Tue(1)
  Jul 21 = Tue(1)   Jul 22 = Wed(2)

TOUR WEEKLY PLAN (day_of_week: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun):
  Tour 1: Tue(1) 10:00, Sat(5) 10:30
  Tour 2: Wed(2) 09:00, Fri(4) 09:00
  Tour 3: Thu(3) 09:00, Sun(6) 11:00
  Tour 4: Mon(0) 17:00, Thu(3) 17:00
  Tour 5: Sat(5) 08:30, Sun(6) 08:30
  Tour 6: Tue(1) 16:00, Fri(4) 15:00
  Tour 7: Fri(4) 20:00, Sat(5) 20:00
  Tour 8: Sat(5) 09:00

Guides:
  Valentina (id=1): Tour 1, Tour 2, Tour 5
  Marco     (id=2): Tour 3, Tour 6, Tour 7
  Carmen    (id=3): Tour 4, Tour 8

══ PENDING REPORTS (visible on BOTH test dates Jun 28 AND Jul 1) ══
  Tour 2 / Jun 24 (Wed) → Valentina pending — Alice 1 persona
  Tour 6 / Jun 23 (Tue) → Marco    pending — Luca  2 persone

══ BECOMES PAST DURING Jun 28 TEST ══
  Tour 3 / Jun 28 (Sun) 11:00 → Marco    pending — FULL 10/10 (Alice 4 + Luca 4 + Emma 2)
  Tour 5 / Jun 28 (Sun) 08:30 → Valentina pending — Alice 3 persone (already past at 15:37)

══ BECOMES PAST DURING Jul 1 TEST ══
  Tour 2 / Jul 1  (Wed) 09:00 → Valentina pending — Alice 3 persone

══ FULL + NOT CANCELLABLE for Jun 28 ══
  Tour 3 / Jun 28 (Sun) 11:00 — cutoff Jun 27 11:00 — FULL 10/10
  (Alice 4 + Luca 4 + Emma 2)

══ FULL + NOT CANCELLABLE for Jul 1 ══
  Tour 3 / Jul 2  (Thu) 09:00 — cutoff Jul 1 09:00 — FULL 10/10
  (Alice 4 + Luca 4 + Emma 2)
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_NAME   = "VisitAltamura_db.db"
STATIC_DIR = "static"

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Clear all tables
# ─────────────────────────────────────────────────────────────────────────────
def clear_db(c):
    c.execute("PRAGMA foreign_keys = OFF")
    for table in [
        "tour_final_reports", "reservation_guests", "reservations",
        "tour_images", "tour_stops", "tour_weekly_plan", "tours",
        "guide_languages", "users", "sqlite_sequence",
    ]:
        c.execute(f"DELETE FROM [{table}]")
    c.execute("PRAGMA foreign_keys = ON")
    print("  Tables cleared.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Users
# ─────────────────────────────────────────────────────────────────────────────
def insert_users(c):
    credentials = {
        "valentina": "valentina123",
        "marco":     "marco123",
        "carmen":    "carmen123",
        "alice":     "alice123",
        "luca":      "luca123",
        "emma":      "emma123",
        "admin":     "admin123",
    }
    hashed = {k: generate_password_hash(v, method="scrypt") for k, v in credentials.items()}
    users = [
        # id, first_name, last_name, email, password, role, profile_img, created_at
        (1, "Valentina", "Longo",        "valentina@visitaltamura.it", hashed["valentina"], "guide",       "images/profile_imgs/user1.png", "2026-01-15 10:00:00"),
        (2, "Marco",     "Ferretti",     "marco@visitaltamura.it",     hashed["marco"],     "guide",       "images/profile_imgs/user2.png", "2026-01-20 11:00:00"),
        (3, "Carmen",    "Ruiz",         "carmen@visitaltamura.it",    hashed["carmen"],    "guide",       "images/profile_imgs/user3.png", "2026-02-01 09:30:00"),
        (4, "Alice",     "Bianchi",      "alice@visitaltamura.it",     hashed["alice"],     "participant", "images/profile_imgs/user4.png", "2026-03-10 14:00:00"),
        (5, "Luca",      "Martino",      "luca@visitaltamura.it",      hashed["luca"],      "participant", "images/profile_imgs/user5.png", "2026-03-15 16:00:00"),
        (6, "Emma",      "Fontana",      "emma@visitaltamura.it",      hashed["emma"],      "participant", None,                            "2026-04-05 10:00:00"),
        (7, "Admin",     "VisitAltamura","admin@visitaltamura.it",     hashed["admin"],     "admin",       None,                            "2026-01-10 09:00:00"),
    ]
    c.executemany(
        "INSERT INTO users (id, first_name, last_name, email, password, role, profile_img, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        users
    )
    print(f"  Inserted {len(users)} users.")
    return credentials


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Guide languages
# ─────────────────────────────────────────────────────────────────────────────
def insert_guide_languages(c):
    guide_languages = [
        (1, "Italian"),
        (2, "English"),
        (2, "German"),
        (3, "Spanish"),
        (3, "Portuguese"),
    ]
    c.executemany("INSERT INTO guide_languages (guide_id, language) VALUES (?,?)", guide_languages)
    print(f"  Inserted {len(guide_languages)} guide language records.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Tours
# Guide assignments: Valentina(1)=T1,T2,T5 | Marco(2)=T3,T6,T7 | Carmen(3)=T4,T8
# ─────────────────────────────────────────────────────────────────────────────
def insert_tours(c):
    tours = [
        (1,
         "Frederick II and the Cathedral: Altamura's Medieval Heart",
         "Walk through the medieval heart of Altamura in the footsteps of Frederick II of Swabia, the enlightened ruler who founded the city in 1232 and commissioned its magnificent Cathedral. From Corso Federico II to noble palaces, from the commemorative plaque of composer Mercadante to the ancient Peucetian Megalithic Walls — a journey through two thousand years of history in one of Puglia's most fascinating historic centres.",
         1, 90, "Italian",
         "Piazza Duomo",
         15, "2026-02-10 10:00:00"),

        (2,
         "The Tradition of Altamura DOP Bread",
         "Altamura is the \"City of Bread\" — its DOP Bread is the first bakery product in Europe to receive Protected Designation of Origin certification. Discover the centuries-old tradition that still perfumes the alleys of the historic centre: from medieval wood-fired ovens to the art of kneading durum wheat semolina with sourdough starter, through the ancient ritual of homemade bread brought to the communal neighbourhood oven.",
         1, 75, "Italian",
         "Antico Forno Santa Caterina",
         12, "2026-02-15 11:00:00"),

        (3,
         "The Altamura Man: 150,000 Years of Neanderthal History",
         "In 1993, in the caves of Lamalunga just a few kilometres from Altamura, one of the most complete Neanderthal skeletons in the world was discovered, dating back approximately 150,000 years. This English-language tour takes visitors through the National Archaeological Museum and the Museum Network sites to understand the story of the Altamura Man: the geological context of the Alta Murgia, the techniques used to study the finds, and the life of the first inhabitants of this territory.",
         2, 90, "English",
         "Museo Nazionale Archeologico di Altamura",
         10, "2026-03-01 09:00:00"),

        (4,
         "The Claustri of Altamura: Hidden Courtyards of the Medieval Village",
         "Over 80 claustri — known locally as gnostre — are tucked away among the white alleys of Altamura. These enclosed courtyards, born in the Middle Ages to separate and protect the different ethnic communities called by Frederick II to repopulate the city (Latins, Greeks, Jews, Saracens), are today one of the most fascinating features of the historic centre. A stroll through the medieval labyrinth of the \"Lioness of Puglia\" to uncover the hidden corners that escape the hurried tourist.",
         3, 60, "Spanish",
         "Piazza della Resistenza (Porta Matera)",
         12, "2026-03-10 10:00:00"),

        (5,
         "The Pulo and the Murgia: A Natural Wonder of Puglia",
         "The Pulo di Altamura is one of the most spectacular natural wonders in Puglia: a collapse sinkhole nearly 90 metres deep, set in the Alta Murgia plateau and immersed in the Alta Murgia National Park. A guided excursion along the edge of the sinkhole reveals unique Murgia landscapes, surprising biodiversity, and the geological history of a territory inhabited since prehistoric times. Comfortable clothing and walking shoes are recommended. The meeting point is reachable by car from Altamura.",
         1, 150, "Italian",
         "Pulo di Altamura — Panoramic Viewpoint",
         10, "2026-04-01 08:00:00"),

        (6,
         "Mercadante and the Arts: Altamura between Music and Noble Palaces",
         "Francesco Saverio Mercadante (1795-1870) was born in Altamura and became one of the most important opera composers of 19th-century Italy. This German-language tour leads through the cultural heritage of Altamura: noble palaces, sacred art collections, and the traces left by a musician who carried the name of his city across all of Europe.",
         2, 75, "German",
         "Piazza Unita d'Italia (Porta Bari)",
         12, "2026-03-20 09:00:00"),

        (7,
         "Altamura at Sunset: Discovering the Medieval Village",
         "When the sun sets on the limestone of Altamura's historic centre, the city transforms. The alleys empty, the churches light up, and the claustri become places of silence and magic. This evening tour — offered in English for international visitors — takes participants through the unique atmosphere of the medieval village during the golden hours of sunset and the first lights of the evening.",
         2, 60, "English",
         "Piazza Duomo",
         15, "2026-04-05 10:00:00"),

        (8,
         "Footprints of the Giants: Altamura and the Dinosaurs",
         "Cava Pontrelli in Altamura is one of the most extraordinary palaeontological sites in the world: tens of thousands of dinosaur footprints from the Upper Cretaceous, preserved in the limestone rock of the Alta Murgia. This Portuguese-language tour combines a scientific introduction at the National Museum with a guided visit to the quarry — subject to reservation — to offer a unique experience that takes visitors to \"walk with the dinosaurs\" in one of the most surprising places in Puglia.",
         3, 120, "Portuguese",
         "Museo Nazionale Archeologico di Altamura",
         10, "2026-04-15 09:00:00"),

        (9,
         "Flavours of Alta Murgia: Food and Wine Tasting Route",
         "A sensory journey through the food traditions of the Alta Murgia territory: extra virgin olive oil, local cheeses, Primitivo and Nero di Troia wines, traditional taralli and orecchiette. This draft tour will lead participants through selected artisan producers and local taverns in and around Altamura — a tasting route still being finalised.",
         1, 90, "Italian",
         "Covered Market of Altamura",
         12, "2026-06-28 10:00:00"),
    ]
    c.executemany(
        "INSERT INTO tours (id, title, description, guide_id, duration, language, meeting_point, max_participants, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        tours
    )
    print(f"  Inserted {len(tours)} tours.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Weekly schedule
# day_of_week: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri 5=Sat 6=Sun
# ─────────────────────────────────────────────────────────────────────────────
def insert_weekly_plan(c):
    plan = [
        (1, 1, "10:00"), (1, 5, "10:30"),  # Tour 1: Tue 10:00, Sat 10:30
        (2, 2, "09:00"), (2, 4, "09:00"),  # Tour 2: Wed 09:00, Fri 09:00
        (3, 3, "09:00"), (3, 6, "11:00"),  # Tour 3: Thu 09:00, Sun 11:00
        (4, 0, "17:00"), (4, 3, "17:00"),  # Tour 4: Mon 17:00, Thu 17:00
        (5, 5, "08:30"), (5, 6, "08:30"),  # Tour 5: Sat 08:30, Sun 08:30
        (6, 1, "16:00"), (6, 4, "15:00"),  # Tour 6: Tue 16:00, Fri 15:00
        (7, 4, "20:00"), (7, 5, "20:00"),  # Tour 7: Fri 20:00, Sat 20:00
        (8, 5, "09:00"),                   # Tour 8: Sat 09:00
    ]
    c.executemany("INSERT INTO tour_weekly_plan (tour_id, day_of_week, start_time) VALUES (?,?,?)", plan)
    print(f"  Inserted {len(plan)} weekly schedule slots.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Stops
# ─────────────────────────────────────────────────────────────────────────────
def insert_stops(c):
    stops = [
        (1, 1, "Porta Bari (Piazza Unita d'Italia)"),
        (1, 2, "Corso Federico II di Svevia"),
        (1, 3, "Cathedral of Santa Maria Assunta"),
        (1, 4, "Saverio Mercadante's Birthplace"),
        (1, 5, "Palazzo Baldassarre"),
        (1, 6, "Peucetian Megalithic Walls"),
        (2, 1, "Antico Forno Santa Caterina"),
        (2, 2, "Forno Antico Santa Chiara"),
        (2, 3, "Museum of Bread by Vito Forte"),
        (2, 4, "Piazza Duomo"),
        (2, 5, "Historic Bakery in the Claustro Courtyard"),
        (3, 1, "Museo Nazionale Archeologico di Altamura"),
        (3, 2, "Palazzo Baldassarre — Museum Network Exhibition Centre"),
        (3, 3, "Peucetian Megalithic Walls"),
        (3, 4, "Palaeolithic Hall — Virtual Reconstruction of the Lamalunga Cave"),
        (3, 5, "Piazza Duomo — Prehistoric Alta Murgia Narration"),
        (4, 1, "Porta Matera (Piazza della Resistenza)"),
        (4, 2, "Claustro della Giudecca — Jewish Quarter Courtyard"),
        (4, 3, "Claustro Patella"),
        (4, 4, "Claustro Tricarico"),
        (4, 5, "Corso Federico II — Side Alleys"),
        (4, 6, "Claustro Inferno"),
        (5, 1, "Pulo di Altamura — Panoramic Viewpoint"),
        (5, 2, "Trail Along the Edge of the Sinkhole"),
        (5, 3, "Grotta dell'Orco (External View)"),
        (5, 4, "Murgia Flora and Fauna Area"),
        (5, 5, "Narrative Stop — Lamalunga Cave and the Altamura Man"),
        (6, 1, "Porta Bari (Piazza Unita d'Italia)"),
        (6, 2, "Saverio Mercadante's Birthplace"),
        (6, 3, "Corso Federico II — 17th to 19th Century Noble Palaces"),
        (6, 4, "Palazzo Baldassarre"),
        (6, 5, "MUDIMA — Diocesan Museum of Altamura"),
        (7, 1, "Piazza Duomo — Illuminated Cathedral"),
        (7, 2, "Corso Federico II at Night"),
        (7, 3, "Altamura Viewpoint"),
        (7, 4, "Claustro Patella in the Evening"),
        (7, 5, "Porta Matera at Sunset"),
        (8, 1, "Museo Nazionale Archeologico — Cretaceous Hall"),
        (8, 2, "Cava Pontrelli — Entrance and External Area"),
        (8, 3, "Cava Pontrelli — Dinosaur Footprint Walkway"),
        (8, 4, "Surrounding Area — Geological Observation"),
        (8, 5, "Boscosauro — Dinosaur Theme Park"),
        # Tour 9 stops (draft — editable)
        (9, 1, "Covered Market of Altamura"),
        (9, 2, "Artisan Bakery on Via Roma"),
        (9, 3, "Cooperative Olive Oil Press"),
        (9, 4, "Winery of Altamura"),
        (9, 5, "Traditional Inn of the Borgo"),
    ]
    c.executemany("INSERT INTO tour_stops (tour_id, position, name) VALUES (?,?,?)", stops)
    print(f"  Inserted {len(stops)} stops.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Tour images (5 per tour, filename: tour{N}-{P}.webp)
# ─────────────────────────────────────────────────────────────────────────────
def insert_images(c):
    images = []
    for tour_id in range(1, 10):
        for pos in range(1, 6):
            images.append((tour_id, f"images/tours/tour{tour_id}-{pos}.webp", pos))
    c.executemany("INSERT INTO tour_images (tour_id, path_img, position) VALUES (?,?,?)", images)
    print(f"  Inserted {len(images)} image records (5 per tour).")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Reservations
#
# Participants: Alice=4, Luca=5, Emma=6   |   max people_count per row = 4
#
# ══ MANDATORY TEST SCENARIOS ═══════════════════════════════════════════════════
#
# ① PENDING REPORTS — visible on BOTH Jun 28 AND Jul 1:
#     R1:  Tour 2 (Valentina) Jun 24 (Wed) — Alice 1 persona
#     R2:  Tour 6 (Marco)     Jun 23 (Tue) — Luca  2 persone
#
# ② BECOMES PAST DURING Jun 28 TEST:
#     R3:  Tour 3 (Marco) Jun 28 (Sun) 11:00 — Emma  2 persone  ← part of FULL group
#     R4:  Tour 3 (Marco) Jun 28 (Sun) 11:00 — Alice 4 persone  ← FULL 10/10
#     R5:  Tour 3 (Marco) Jun 28 (Sun) 11:00 — Luca  4 persone  ← FULL 10/10
#     R6:  Tour 5 (Valentina) Jun 28 (Sun) 08:30 — Alice 3 persone
#
# ③ BECOMES PAST DURING Jul 1 TEST:
#     R7:  Tour 2 (Valentina) Jul 1 (Wed) 09:00 — Alice 3 persone
#
# ④ FULL + NOT CANCELLABLE for Jul 1 (Tour 3 Jul 2 Thu 09:00, cutoff Jul 1 09:00):
#     R8:  Tour 3 Jul 2 — Alice 4
#     R9:  Tour 3 Jul 2 — Luca  4
#     R10: Tour 3 Jul 2 — Emma  2  → FULL 10/10
#
# ⑤ CANCELLABLE (5+ days from Jul 1):
#     R11: Tour 4 (Carmen) Jul 6 (Mon) 17:00 — Emma 2 persone
#
# ⑥ ALMOST FULL (8/10) — Tour 3 Jul 9 (Thu) 09:00:
#     R12: Tour 3 Jul 9 — Alice 4
#     R13: Tour 3 Jul 9 — Luca  4  → 8/10
#
# ⑦ NON-OVERLAPPING same day — Luca: Tour3 Jul9 09:00-10:30 + Tour4 Jul9 17:00-18:00:
#     R14: Tour 4 Jul 9 (Thu) 17:00 — Luca 1 persona
#
# ⑧ CANCELLED — Emma Tour 1 Jul 14 (Tue):
#     R15: Tour 1 Jul 14 — Emma 2 — cancelled
#
# ⑨ FUTURE NORMAL bookings (Jul 4 – Jul 22):
#     R16–R27
#
# ⑩ PAST HISTORY (April–June <Jun 28): R28 onwards
#    - people_count MAX = 4 (DB CHECK constraint)
#    - at least 3-4 past dates per tour
#    - at least 2-3 past bookings per guide
# ═══════════════════════════════════════════════════════════════════════════════
def insert_reservations(c):
    reservations = [
        # fmt: (id, tour_id, participant_id, tour_date, people_count, status, created_at, cancelled_at)

        # ────────────────────────────────────────────────────────────────────
        # ① PENDING (both test dates)
        # ────────────────────────────────────────────────────────────────────
        #  R1 — Tour 2 / Jun 24 (Wed) — Valentina PENDING — Alice 1 persona
        ( 1, 2, 4, "2026-06-24", 1, "confirmed", "2026-06-18 10:00:00", None),
        #  R2 — Tour 6 / Jun 23 (Tue) — Marco PENDING — Luca 2 persone
        ( 2, 6, 5, "2026-06-23", 2, "confirmed", "2026-06-17 09:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ② BECOMES PAST Jun 28 — Tour 3 Jun 28 (Sun) 11:00 — FULL 10/10
        #    cutoff = Jun 27 11:00 → NOT CANCELLABLE during entire Jun 28
        #    Marco PENDING report
        # ────────────────────────────────────────────────────────────────────
        #  R3 — Emma 2 persone
        ( 3, 3, 6, "2026-06-28", 2, "confirmed", "2026-06-20 12:00:00", None),
        #  R4 — Alice 4 persone
        ( 4, 3, 4, "2026-06-28", 4, "confirmed", "2026-06-19 10:00:00", None),
        #  R5 — Luca 4 persone  (total = 2+4+4 = 10/10 FULL)
        ( 5, 3, 5, "2026-06-28", 4, "confirmed", "2026-06-21 11:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ② BECOMES PAST Jun 28 — Tour 5 Jun 28 (Sun) 08:30
        #    Valentina PENDING report (already past at 15:37)
        # ────────────────────────────────────────────────────────────────────
        #  R6 — Alice 3 persone
        ( 6, 5, 4, "2026-06-28", 3, "confirmed", "2026-06-22 08:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ③ BECOMES PAST Jul 1 — Tour 2 Jul 1 (Wed) 09:00
        #    Valentina PENDING report (becomes past at ~10:15)
        # ────────────────────────────────────────────────────────────────────
        #  R7 — Alice 3 persone
        ( 7, 2, 4, "2026-07-01", 3, "confirmed", "2026-06-25 16:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ④ FULL + NOT CANCELLABLE for Jul 1 — Tour 3 Jul 2 (Thu) 09:00
        #    cutoff = Jul 1 09:00 → NOT CANCELLABLE all day Jul 1
        # ────────────────────────────────────────────────────────────────────
        #  R8  — Alice 4
        ( 8, 3, 4, "2026-07-02", 4, "confirmed", "2026-06-22 10:00:00", None),
        #  R9  — Luca  4
        ( 9, 3, 5, "2026-07-02", 4, "confirmed", "2026-06-23 11:00:00", None),
        #  R10 — Emma  2  → FULL 10/10
        (10, 3, 6, "2026-07-02", 2, "confirmed", "2026-06-24 12:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑤ CANCELLABLE — Tour 4 Jul 6 (Mon) 17:00 — Emma 2 persone
        #    5+ days from Jul 1 → always cancellable
        # ────────────────────────────────────────────────────────────────────
        (11, 4, 6, "2026-07-06", 2, "confirmed", "2026-06-26 15:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑥ ALMOST FULL (8/10) — Tour 3 Jul 9 (Thu) 09:00
        # ────────────────────────────────────────────────────────────────────
        (12, 3, 4, "2026-07-09", 4, "confirmed", "2026-06-25 14:00:00", None),  # Alice 4
        (13, 3, 5, "2026-07-09", 4, "confirmed", "2026-06-26 09:00:00", None),  # Luca  4  → 8/10

        # ────────────────────────────────────────────────────────────────────
        # ⑦ NON-OVERLAPPING same day — Tour 4 Jul 9 (Thu) 17:00 — Luca
        # ────────────────────────────────────────────────────────────────────
        (14, 4, 5, "2026-07-09", 1, "confirmed", "2026-06-27 10:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑧ CANCELLED — Tour 1 Jul 14 (Tue) — Emma 2 persone
        # ────────────────────────────────────────────────────────────────────
        (15, 1, 6, "2026-07-14", 2, "cancelled", "2026-06-20 15:00:00", "2026-06-24 09:00:00"),

        # ────────────────────────────────────────────────────────────────────
        # ⑨ FUTURE NORMAL bookings
        # ────────────────────────────────────────────────────────────────────
        # Alice Tour 1 Jul 7 (Tue) 10:00 — 2 persone
        (16, 1, 4, "2026-07-07", 2, "confirmed", "2026-06-25 09:00:00", None),
        # Luca Tour 1 Jul 7 (Tue) 10:00 — 1 persona
        (17, 1, 5, "2026-07-07", 1, "confirmed", "2026-06-26 10:00:00", None),
        # Alice Tour 6 Jul 10 (Fri) 15:00 — 2 persone
        (18, 6, 4, "2026-07-10", 2, "confirmed", "2026-06-26 16:00:00", None),
        # Emma Tour 7 Jul 10 (Fri) 20:00 — 1 persona
        (19, 7, 6, "2026-07-10", 1, "confirmed", "2026-06-27 17:00:00", None),
        # Alice Tour 5 Jul 4 (Sat) 08:30 — 3 persone
        (20, 5, 4, "2026-07-04", 3, "confirmed", "2026-06-26 08:00:00", None),
        # Emma Tour 2 Jul 8 (Wed) 09:00 — 2 persone
        (21, 2, 6, "2026-07-08", 2, "confirmed", "2026-06-30 09:00:00", None),
        # Luca Tour 7 Jul 11 (Sat) 20:00 — 2 persone
        (22, 7, 5, "2026-07-11", 2, "confirmed", "2026-06-27 20:00:00", None),
        # Alice Tour 8 Jul 11 (Sat) 09:00 — 2 persone
        (23, 8, 4, "2026-07-11", 2, "confirmed", "2026-06-27 09:00:00", None),
        # Emma Tour 5 Jul 12 (Sun) 08:30 — 1 persona
        (24, 5, 6, "2026-07-12", 1, "confirmed", "2026-06-28 08:00:00", None),
        # Alice Tour 3 Jul 12 (Sun) 11:00 — 2 persone  (Jul 12=Sun → Tour3 Sun 11:00 ✓)
        (25, 3, 4, "2026-07-12", 2, "confirmed", "2026-06-28 10:00:00", None),
        # Luca Tour 2 Jul 22 (Wed) 09:00 — 3 persone
        (26, 2, 5, "2026-07-22", 3, "confirmed", "2026-06-28 09:00:00", None),
        # Emma Tour 1 Jul 21 (Tue) 10:00 — 2 persone
        (27, 1, 6, "2026-07-21", 2, "confirmed", "2026-06-28 10:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑩ PAST HISTORY — ALICE (April–June <Jun 28)
        # ────────────────────────────────────────────────────────────────────
        # Apr 9 = Thu  → Tour 3 Thu 09:00 ✓
        (28, 3, 4, "2026-04-09", 2, "confirmed", "2026-04-03 10:00:00", None),
        # Apr 4 = Sat  → Tour 7 Sat 20:00 ✓  (Tour 1 Sat 10:30 also fine)
        (29, 7, 4, "2026-04-04", 3, "confirmed", "2026-03-28 15:00:00", None),
        # Apr 15 = Wed → Tour 2 Wed 09:00 ✓
        (30, 2, 4, "2026-04-15", 1, "confirmed", "2026-04-09 09:00:00", None),
        # Apr 30 = Thu → Tour 4 Thu 17:00 ✓
        (31, 4, 4, "2026-04-30", 2, "confirmed", "2026-04-24 11:00:00", None),
        # Apr 11 = Sat → Tour 8 Sat 09:00 ✓
        (32, 8, 4, "2026-04-11", 2, "confirmed", "2026-04-05 08:00:00", None),
        # May 9 = Sat  → Tour 7 Sat 20:00 ✓ (was Tour 5 — kept as Tour 7 so Tour 5 has 0 past)
        (33, 7, 4, "2026-05-09", 2, "confirmed", "2026-05-03 09:00:00", None),
        # May 15 = Fri → Tour 6 Fri 15:00 ✓
        (34, 6, 4, "2026-05-15", 1, "confirmed", "2026-05-09 14:00:00", None),
        # May 19 = Tue → Tour 1 Tue 10:00 ✓
        (35, 1, 4, "2026-05-19", 4, "confirmed", "2026-05-13 10:00:00", None),
        # May 3 = Sun  → Tour 3 Sun 11:00 ✓
        (36, 3, 4, "2026-05-03", 2, "confirmed", "2026-04-27 09:00:00", None),
        # May 4 = Mon  → Tour 4 Mon 17:00 ✓
        (37, 4, 4, "2026-05-04", 2, "confirmed", "2026-04-28 10:00:00", None),
        # Jun 4 = Wed  → Tour 2 Wed 09:00 ✓
        (38, 2, 4, "2026-06-04", 1, "confirmed", "2026-05-29 09:00:00", None),
        # Jun 6 = Sat  → Tour 1 Sat 10:30 ✓ (was Tour 5 — kept as Tour 1 so Tour 5 has 0 past)
        (39, 1, 4, "2026-06-06", 3, "confirmed", "2026-05-31 08:00:00", None),
        # Jun 13 = Fri → Tour 7 Fri 20:00 ✓  (also Tour 2 Fri, Tour 6 Fri)
        (40, 7, 4, "2026-06-13", 2, "confirmed", "2026-06-07 20:00:00", None),
        # Jun 19 = Fri → Tour 6 Fri 15:00 ✓
        (41, 6, 4, "2026-06-19", 2, "confirmed", "2026-06-13 14:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑩ PAST HISTORY — LUCA (April–June <Jun 28)
        # ────────────────────────────────────────────────────────────────────
        # Apr 4 = Sat  → Tour 1 Sat 10:30 ✓
        (42, 1, 5, "2026-04-04", 2, "confirmed", "2026-03-29 11:00:00", None),
        # Apr 30 = Thu → Tour 3 Thu 09:00 ✓
        (43, 3, 5, "2026-04-30", 2, "confirmed", "2026-04-24 09:00:00", None),
        # Apr 28 = Tue → Tour 6 Tue 16:00 ✓
        (44, 6, 5, "2026-04-28", 2, "confirmed", "2026-04-22 16:00:00", None),
        # Apr 18 = Sat → Tour 7 Sat 20:00 ✓
        (45, 7, 5, "2026-04-18", 3, "confirmed", "2026-04-12 20:00:00", None),
        # May 9 = Sat  → Tour 8 Sat 09:00 ✓
        (46, 8, 5, "2026-05-09", 2, "confirmed", "2026-05-03 08:00:00", None),
        # May 11 = Mon → Tour 4 Mon 17:00 ✓
        (47, 4, 5, "2026-05-11", 1, "confirmed", "2026-05-05 17:00:00", None),
        # May 15 = Fri → Tour 2 Fri 09:00 ✓
        (48, 2, 5, "2026-05-15", 2, "confirmed", "2026-05-09 09:00:00", None),
        # May 10 = Sun → Tour 3 Sun 11:00 ✓ (was Tour 5 — kept as Tour 3 so Tour 5 has 0 past)
        (49, 3, 5, "2026-05-10", 2, "confirmed", "2026-05-04 08:00:00", None),
        # Jun 2 = Tue  → Tour 1 Tue 10:00 ✓
        (50, 1, 5, "2026-06-02", 2, "confirmed", "2026-05-27 10:00:00", None),
        # Jun 11 = Wed → Tour 2 Wed 09:00 ✓
        (51, 2, 5, "2026-06-11", 2, "confirmed", "2026-06-05 09:00:00", None),
        # Jun 12 = Fri → Tour 6 Fri 15:00 ✓
        (52, 6, 5, "2026-06-12", 1, "confirmed", "2026-06-06 15:00:00", None),
        # Jun 20 = Sat → Tour 8 Sat 09:00 ✓
        (53, 8, 5, "2026-06-20", 1, "confirmed", "2026-06-14 09:00:00", None),
        # Jun 26 = Fri → Tour 7 Fri 20:00 ✓
        (54, 7, 5, "2026-06-26", 2, "confirmed", "2026-06-20 20:00:00", None),

        # ────────────────────────────────────────────────────────────────────
        # ⑩ PAST HISTORY — EMMA (April–June <Jun 28)
        # ────────────────────────────────────────────────────────────────────
        # Apr 4 = Sat  → Tour 8 Sat 09:00 ✓
        (55, 8, 6, "2026-04-04", 2, "confirmed", "2026-03-29 08:00:00", None),
        # Apr 9 = Thu  → Tour 4 Thu 17:00 ✓
        (56, 4, 6, "2026-04-09", 2, "confirmed", "2026-04-03 17:00:00", None),
        # Apr 11 = Sat → Tour 1 Sat 10:30 ✓
        (57, 1, 6, "2026-04-11", 2, "confirmed", "2026-04-05 10:00:00", None),
        # Apr 12 = Sun → Tour 3 Sun 11:00 ✓
        (58, 3, 6, "2026-04-12", 3, "confirmed", "2026-04-06 11:00:00", None),
        # Apr 18 = Sat → Tour 8 Sat 09:00 ✓ (was Tour 5 — kept as Tour 8 so Tour 5 has 0 past)
        (59, 8, 6, "2026-04-18", 1, "confirmed", "2026-04-12 08:00:00", None),
        # May 4 = Mon  → Tour 4 Mon 17:00 ✓
        (60, 4, 6, "2026-05-04", 2, "confirmed", "2026-04-28 17:00:00", None),
        # May 6 = Wed  → Tour 2 Wed 09:00 ✓
        (61, 2, 6, "2026-05-06", 3, "confirmed", "2026-04-30 09:00:00", None),
        # May 19 = Tue → Tour 1 Tue 10:00 ✓
        (62, 1, 6, "2026-05-19", 4, "confirmed", "2026-05-13 10:00:00", None),
        # May 17 = Sun → Tour 3 Sun 11:00 ✓
        (63, 3, 6, "2026-05-17", 2, "confirmed", "2026-05-11 11:00:00", None),
        # May 25 = Mon → Tour 4 Mon 17:00 ✓
        (64, 4, 6, "2026-05-25", 2, "confirmed", "2026-05-19 17:00:00", None),
        # Jun 2 = Tue  → Tour 6 Tue 16:00 ✓
        (65, 6, 6, "2026-06-02", 2, "confirmed", "2026-05-27 16:00:00", None),
        # Jun 4 = Wed  → Tour 2 Wed 09:00 ✓
        (66, 2, 6, "2026-06-04", 1, "confirmed", "2026-05-29 09:00:00", None),
        # Jun 7 = Sun  → Tour 3 Sun 11:00 ✓
        (67, 3, 6, "2026-06-07", 2, "confirmed", "2026-06-01 11:00:00", None),
        # Jun 21 = Sun → Tour 3 Sun 11:00 ✓ (was Tour 5 — kept as Tour 3 so Tour 5 has 0 past)
        (68, 3, 6, "2026-06-21", 3, "confirmed", "2026-06-14 08:00:00", None),
        # Jun 27 = Sat → Tour 7 Sat 20:00 ✓
        (69, 7, 6, "2026-06-27", 2, "confirmed", "2026-06-21 20:00:00", None),
    ]

    c.executemany(
        "INSERT INTO reservations (id, tour_id, participant_id, tour_date, people_count, status, created_at, cancelled_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        reservations
    )
    print(f"  Inserted {len(reservations)} reservations.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Guests (additional companions beyond the participant themselves)
# people_count = 1 means participant only (no extra guest row needed)
# people_count = N means participant + (N-1) guests
# ─────────────────────────────────────────────────────────────────────────────
def insert_guests(c):
    guests = [
        # ── R1  Alice Tour2 Jun24 (1 persona — no guests) ──
        # ── R2  Luca Tour6 Jun23 (2 persone) ──────────────
        ( 2, "Matteo",     "Villa"),
        # ── R3  Emma Tour3 Jun28 (2 persone) ──────────────
        ( 3, "Paolo",      "Ricci"),
        # ── R4  Alice Tour3 Jun28 (4 persone) ─────────────
        ( 4, "Giulia",     "Neri"),
        ( 4, "Pietro",     "Costa"),
        ( 4, "Anna",       "Russo"),
        # ── R5  Luca Tour3 Jun28 (4 persone) ──────────────
        ( 5, "Carlo",      "Brun"),
        ( 5, "Sara",       "Miele"),
        ( 5, "Simone",     "Ferro"),
        # ── R6  Alice Tour5 Jun28 (3 persone) ─────────────
        ( 6, "Leonardo",   "Conti"),
        ( 6, "Marta",      "Ferrari"),
        # ── R7  Alice Tour2 Jul1 (3 persone) ──────────────
        ( 7, "Sara",       "Conti"),
        ( 7, "Marco",      "Bello"),
        # ── R8  Alice Tour3 Jul2 (4 persone) ──────────────
        ( 8, "Laura",      "Bianco"),
        ( 8, "Giovanni",   "Serra"),
        ( 8, "Marta",      "Ricci"),
        # ── R9  Luca Tour3 Jul2 (4 persone) ───────────────
        ( 9, "Paolo",      "Greco"),
        ( 9, "Claudia",    "Rana"),
        ( 9, "Dario",      "Vola"),
        # ── R10 Emma Tour3 Jul2 (2 persone) ───────────────
        (10, "Fabio",      "Gallo"),
        # ── R11 Emma Tour4 Jul6 (2 persone) ───────────────
        (11, "Monica",     "Frei"),
        # ── R12 Alice Tour3 Jul9 (4 persone) ──────────────
        (12, "Serena",     "Fiore"),
        (12, "Flavia",     "Costa"),
        (12, "Roberto",    "De Luca"),
        # ── R13 Luca Tour3 Jul9 (4 persone) ───────────────
        (13, "Valentina",  "Roma"),
        (13, "Giorgia",    "Asti"),
        (13, "Marco",      "Lisi"),
        # ── R14 Luca Tour4 Jul9 (1 persona — no guests) ───
        # ── R15 Emma Tour1 Jul14 CANCELLED (2 persone) ────
        (15, "Davide",     "Mari"),
        # ── R16 Alice Tour1 Jul7 (2 persone) ──────────────
        (16, "Andrea",     "Lumi"),
        # ── R17 Luca Tour1 Jul7 (1 persona — no guests) ───
        # ── R18 Alice Tour6 Jul10 (2 persone) ─────────────
        (18, "Sofia",      "Greco"),
        # ── R19 Emma Tour7 Jul10 (1 persona — no guests) ──
        # ── R20 Alice Tour5 Jul4 (3 persone) ──────────────
        (20, "Luca",       "Carbone"),
        (20, "Marta",      "Esposito"),
        # ── R21 Emma Tour2 Jul8 (2 persone) ───────────────
        (21, "Roberto",    "Conti"),
        # ── R22 Luca Tour7 Jul11 (2 persone) ──────────────
        (22, "Elisa",      "Marini"),
        # ── R23 Alice Tour8 Jul11 (2 persone) ─────────────
        (23, "Marco",      "Ferri"),
        # ── R24 Emma Tour5 Jul12 (1 persona — no guests) ──
        # ── R25 Alice Tour3 Jul12 (2 persone) ─────────────
        (25, "Rossella",   "Bianchi"),
        # ── R26 Luca Tour2 Jul22 (3 persone) ──────────────
        (26, "Veronica",   "Caruso"),
        (26, "Enrico",     "Conti"),
        # ── R27 Emma Tour1 Jul21 (2 persone) ──────────────
        (27, "Davide",     "Pellegrini"),

        # ── PAST HISTORY — ALICE ────────────────────────────
        # R28 Tour3 Apr9 (2 persone)
        (28, "Giorgio",    "Ferri"),
        # R29 Tour7 Apr4 (3 persone)
        (29, "Stefano",    "Caruso"),
        (29, "Francesca",  "Marini"),
        # R30 Tour2 Apr15 (1 persona — no guests)
        # R31 Tour4 Apr30 (2 persone)
        (31, "Elena",      "Romano"),
        # R32 Tour8 Apr11 (2 persone)
        (32, "Federico",   "Barbieri"),
        # R33 Tour5 May9 (2 persone)
        (33, "Antonio",    "De Luca"),
        # R34 Tour6 May15 (1 persona — no guests)
        # R35 Tour1 May19 (4 persone)
        (35, "Marco",      "Esposito"),
        (35, "Claudia",    "Gallo"),
        (35, "Pietro",     "Moretti"),
        # R36 Tour3 May3 (2 persone)
        (36, "Valentina",  "Serra"),
        # R37 Tour4 May4 (2 persone)
        (37, "Antonio",    "Fontana"),
        # R38 Tour2 Jun4 (1 persona — no guests)
        # R39 Tour5 Jun6 (3 persone)
        (39, "Leonardo",   "Ferrari"),
        (39, "Marta",      "Greco"),
        # R40 Tour7 Jun13 (2 persone)
        (40, "Rossella",   "De Luca"),
        # R41 Tour6 Jun19 (2 persone)
        (41, "Antonio",    "Russo"),

        # ── PAST HISTORY — LUCA ─────────────────────────────
        # R42 Tour1 Apr4 (2 persone)
        (42, "Paola",      "Russo"),
        # R43 Tour3 Apr30 (2 persone)
        (43, "Enrico",     "Longo"),
        # R44 Tour6 Apr28 (2 persone)
        (44, "Maria",      "Fontana"),
        # R45 Tour7 Apr18 (3 persone)
        (45, "Francesco",  "Leone"),
        (45, "Veronica",   "Mancini"),
        # R46 Tour8 May9 (2 persone)
        (46, "Roberto",    "Pellegrini"),
        # R47 Tour4 May11 (1 persona — no guests)
        # R48 Tour2 May15 (2 persone)
        (48, "Irene",      "Esposito"),
        # R49 Tour5 May10 (2 persone)
        (49, "Davide",     "Caruso"),
        # R50 Tour1 Jun2 (2 persone)
        (50, "Sofia",      "Romano"),
        # R51 Tour2 Jun11 (2 persone)
        (51, "Lorenzo",    "Ferrari"),
        # R52 Tour6 Jun12 (1 persona — no guests)
        # R53 Tour8 Jun20 (1 persona — no guests)
        # R54 Tour7 Jun26 (2 persone)
        (54, "Chiara",     "Moro"),

        # ── PAST HISTORY — EMMA ─────────────────────────────
        # R55 Tour8 Apr4 (2 persone)
        (55, "Giovanni",   "Russo"),
        # R56 Tour4 Apr9 (2 persone)
        (56, "Cristina",   "Barbieri"),
        # R57 Tour1 Apr11 (2 persone)
        (57, "Luca",       "Pellegrini"),
        # R58 Tour3 Apr12 (3 persone)
        (58, "Marco",      "Conti"),
        (58, "Laura",      "Fontana"),
        # R59 Tour5 Apr18 (1 persona — no guests)
        # R60 Tour4 May4 (2 persone)
        (60, "Fabio",      "Moretti"),
        # R61 Tour2 May6 (3 persone)
        (61, "Pietro",     "Gallo"),
        (61, "Sara",       "Neri"),
        # R62 Tour1 May19 (4 persone)
        (62, "Carlo",      "Longo"),
        (62, "Anna",       "Greco"),
        (62, "Federico",   "Serra"),
        # R63 Tour3 May17 (2 persone)
        (63, "Simone",     "Ferraro"),
        # R64 Tour4 May25 (2 persone)
        (64, "Giovanna",   "Rossi"),
        # R65 Tour6 Jun2 (2 persone)
        (65, "Simone",     "Gallo"),
        # R66 Tour2 Jun4 (1 persona — no guests)
        # R67 Tour3 Jun7 (2 persone)
        (67, "Marco",      "Villa"),
        # R68 Tour5 Jun21 (3 persone)
        (68, "Matteo",     "Neri"),
        (68, "Chiara",     "Ricci"),
        # R69 Tour7 Jun27 (2 persone)
        (69, "Roberto",    "Leone"),
    ]
    c.executemany(
        "INSERT INTO reservation_guests (reservation_id, first_name, last_name) VALUES (?,?,?)",
        guests
    )
    print(f"  Inserted {len(guests)} guests.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — Reports (auto-generated for all past confirmed dates)
#
# Completed reports are auto-generated for ALL (tour_id, tour_date) pairs
# where:
#   - status = 'confirmed'
#   - tour_date < '2026-06-28'    (strictly before today)
#   - (tour_id, tour_date) NOT IN PENDING_PAIRS
#
# PENDING_PAIRS (intentionally left without a report):
#   (2, '2026-06-24') — Tour 2 Wed Jun 24  Valentina pending (both test dates)
#   (6, '2026-06-23') — Tour 6 Tue Jun 23  Marco    pending (both test dates)
#   (3, '2026-06-28') — Tour 3 Sun Jun 28  Marco    pending (becomes past Jun 28 pomeriggio)
#   (5, '2026-06-28') — Tour 5 Sun Jun 28  Valentina pending (already past Jun 28 ore 15:37)
#   (2, '2026-07-01') — Tour 2 Wed Jul 1   Valentina pending (becomes past Jul 1 morning)
#
# NOTE: Tour 3 Jun 28 and Tour 5 Jun 28 have tour_date = '2026-06-28' which is
#       NOT < '2026-06-28', so the SQL query already excludes them automatically.
#       They are listed in PENDING_PAIRS as documentation only.
# ─────────────────────────────────────────────────────────────────────────────
def insert_reports(c):
    # Pairs intentionally left pending (no completed report inserted)
    PENDING_PAIRS = {
        (2, "2026-06-24"),   # Tour 2 Wed Jun 24 — Valentina pending
        (6, "2026-06-23"),   # Tour 6 Tue Jun 23 — Marco    pending
        (3, "2026-06-28"),   # Tour 3 Sun Jun 28 — Marco    pending  (excluded by date < clause anyway)
        (5, "2026-06-28"),   # Tour 5 Sun Jun 28 — Valentina pending (excluded by date < clause anyway)
        (2, "2026-07-01"),   # Tour 2 Wed Jul 1  — Valentina pending (future, excluded by date < clause)
    }

    report_imgs = [f"images/reports/report{i}.png" for i in range(1, 40)]
    img_idx = 0

    # Auto-generate completed reports for all past confirmed (tour_id, tour_date) pairs
    c.execute("""
        SELECT tour_id, tour_date, SUM(people_count) AS total
        FROM reservations
        WHERE status = 'confirmed' AND tour_date < '2026-06-28'
        GROUP BY tour_id, tour_date
        ORDER BY tour_date
    """)

    count = 0
    for tour_id, tour_date, total in c.fetchall():
        if (tour_id, tour_date) in PENDING_PAIRS:
            continue
        img = report_imgs[img_idx % len(report_imgs)]
        img_idx += 1
        # Realistic attendance: large groups may have 1 no-show
        final = max(1, total - (1 if total >= 5 else 0))
        c.execute(
            "INSERT INTO tour_final_reports (tour_id, tour_date, final_participants, group_img, created_at) "
            "VALUES (?,?,?,?,?)",
            (tour_id, tour_date, final, img, f"{tour_date} 22:00:00")
        )
        count += 1

    print(f"  Auto-generated {count} completed reports "
          f"({len(PENDING_PAIRS)} pairs intentionally pending).")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n=== VisitAltamura — Full Database Population ===")
    print("    Test dates: 2026-06-28 (today / Sunday) | 2026-07-01 (presentation / Wednesday)\n")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    print("\n[1] Clearing database:")
    clear_db(c)

    print("\n[2] Users:")
    credentials = insert_users(c)

    print("\n[3] Guide languages:")
    insert_guide_languages(c)

    print("\n[4] Tours:")
    insert_tours(c)

    print("\n[5] Weekly schedule:")
    insert_weekly_plan(c)

    print("\n[6] Stops:")
    insert_stops(c)

    print("\n[7] Tour images:")
    insert_images(c)

    print("\n[8] Reservations:")
    insert_reservations(c)

    print("\n[9] Guests:")
    insert_guests(c)

    print("\n[10] Reports:")
    insert_reports(c)

    conn.commit()

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n=== SUMMARY ===")
    for table in ["users", "tours", "tour_weekly_plan", "tour_stops", "tour_images",
                  "reservations", "reservation_guests", "tour_final_reports"]:
        c.execute(f"SELECT COUNT(*) FROM [{table}]")
        print(f"  {table:30s}: {c.fetchone()[0]}")

    conn.close()

    print("\n" + "=" * 66)
    print("DATABASE POPULATED SUCCESSFULLY")
    print("=" * 66)
    print("\nCREDENTIALS:\n")
    print(f"  [GUIDE 1  Italian]          valentina@visitaltamura.it / {credentials['valentina']}")
    print(f"  [GUIDE 2  English+German]   marco@visitaltamura.it     / {credentials['marco']}")
    print(f"  [GUIDE 3  Spanish+Portug.]  carmen@visitaltamura.it    / {credentials['carmen']}")
    print(f"  [PARTICIPANT 1]             alice@visitaltamura.it     / {credentials['alice']}")
    print(f"  [PARTICIPANT 2]             luca@visitaltamura.it      / {credentials['luca']}")
    print(f"  [PARTICIPANT 3]             emma@visitaltamura.it      / {credentials['emma']}")
    print(f"  [ADMIN]                     admin@visitaltamura.it     / {credentials['admin']}")
    print("\n" + "=" * 66 + "\n")


if __name__ == "__main__":
    main()
