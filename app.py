from flask import Flask, render_template, request, redirect, url_for
import os
from dotenv import load_dotenv
from db_connection import get_db_connection as get_conn

load_dotenv()  # reads .env

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/maintenance")
def maintenance():
    return render_template("maintenance.html")

@app.route("/index")
@app.route("/index.html")
def index_page():
    return render_template("index.html")

@app.route("/home_page")
def home_page():
    return render_template("index.html")

@app.route("/imprint")
def imprint():
    return render_template("imprint.html")

@app.route("/persons/new")
def persons_new():
    return render_template("persons_new.html")

@app.route("/persons/create", methods=["POST"])
def persons_create():
    data = {
        "first_name": request.form.get("first_name","").strip(),
        "last_name": request.form.get("last_name","").strip(),
        "email": request.form.get("email") or None,
        "phone": request.form.get("phone") or None,
        "dob": request.form.get("date_of_birth") or None,
    }
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO persons (first_name, last_name, email, phone, date_of_birth)
                VALUES (%s,%s,%s,%s,%s)
            """, (data["first_name"], data["last_name"], data["email"], data["phone"], data["dob"]))
        return render_template("feedback.html", title="Create Person", message="Person created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Person", message=f"Error: {e}")

@app.route("/venues/new")
def venues_new():
    return render_template("venues_new.html")

@app.route("/venues/create", methods=["POST"])
def venues_create():
    v_name = request.form.get("v_name","").strip()
    v_address = request.form.get("v_address") or None
    city = request.form.get("city") or None
    country = request.form.get("country") or None
    capacity = request.form.get("capacity") or None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO venues (v_name, v_address, city, country, capacity)
                VALUES (%s,%s,%s,%s,%s)
            """, (v_name, v_address, city, country, capacity))
        return render_template("feedback.html", title="Create Venue", message="Venue created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Venue", message=f"Error: {e}")

def get_venues():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT venue_id, CONCAT(v_name,' — ',COALESCE(city,''),', ',COALESCE(country,'')) AS label FROM venues ORDER BY v_name")
        return cur.fetchall()

@app.route("/events/new")
def events_new():
    return render_template("events_new.html", venues=get_venues())

@app.route("/events/create", methods=["POST"])
def events_create():
    title = request.form.get("title","").strip()
    e_description = request.form.get("e_description") or None
    venue_id = request.form.get("venue_id")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time") or None
    e_status = request.form.get("e_status","scheduled")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (title, e_description, venue_id, start_time, end_time, e_status)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (title, e_description, venue_id, start_time, end_time, e_status))
        return render_template("feedback.html", title="Create Event", message="Event created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Event", message=f"Error: {e}")

def get_events():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT event_id, CONCAT(title,' — ', DATE_FORMAT(start_time,'%Y-%m-%d %H:%i')) AS label
          FROM events ORDER BY start_time DESC
        """)
        return cur.fetchall()

def get_seats():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT s.seat_id,
                 CONCAT(COALESCE(s.seat_section,''),'-',COALESCE(s.row_label,''),'-',COALESCE(s.seat_number,''),' @ ',v.v_name) AS label
          FROM seats s JOIN venues v ON v.venue_id = s.venue_id
          ORDER BY v.v_name, s.seat_section, s.row_label, s.seat_number
        """)
        return cur.fetchall()

@app.route("/tickets/new")
def tickets_new():
    return render_template("tickets_new.html", events=get_events(), seats=get_seats())

@app.route("/tickets/create", methods=["POST"])
def tickets_create():
    event_id = request.form.get("event_id")
    seat_id = request.form.get("seat_id") or None
    face_value = request.form.get("face_value")
    currency = request.form.get("currency","EUR")
    ticket_status = request.form.get("ticket_status","available")
    issued_at = request.form.get("issued_at") or None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO tickets (event_id, seat_id, face_value, currency, ticket_status, issued_at)
              VALUES (%s,%s,%s,%s,%s,%s)
            """, (event_id, seat_id, face_value, currency, ticket_status, issued_at))
        return render_template("feedback.html", title="Create Ticket", message="Ticket created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Ticket", message=f"Error: {e}")

def get_customers_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT c.person_id,
                 CONCAT(p.first_name,' ',p.last_name,' — ',COALESCE(p.email,'no email')) AS label
          FROM customers c JOIN persons p ON p.person_id=c.person_id
          ORDER BY p.last_name, p.first_name
        """)
        return cur.fetchall()

@app.route("/purchases/new")
def purchases_new():
    return render_template("purchases_new.html", customers=get_customers_for_dropdown())

@app.route("/purchases/create", methods=["POST"])
def purchases_create():
    customer_id = request.form.get("customer_id")
    purchase_time = request.form.get("purchase_time") or None
    total_amount = request.form.get("total_amount")
    purch_status = request.form.get("purch_status","pending")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO purchases (customer_id, purchase_time, total_amount, purch_status)
              VALUES (%s,%s,%s,%s)
            """, (customer_id, purchase_time, total_amount, purch_status))
        return render_template("feedback.html", title="Create Purchase", message="Purchase created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Purchase", message=f"Error: {e}")


def get_purchases_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT purchase_id,
                 CONCAT('#',purchase_id,' — ',DATE_FORMAT(purchase_time,'%Y-%m-%d %H:%i'),' — €',total_amount) AS label
          FROM purchases ORDER BY purchase_time DESC
        """)
        return cur.fetchall()

@app.route("/payments/new")
def payments_new():
    return render_template("payments_new.html", purchases=get_purchases_for_dropdown())

@app.route("/payments/create", methods=["POST"])
def payments_create():
    purchase_id = request.form.get("purchase_id")
    amount = request.form.get("amount")
    method = request.form.get("method","card")
    transaction_ref = request.form.get("transaction_ref") or None
    paid_at = request.form.get("paid_at") or None
    payment_status = request.form.get("payment_status","ok")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO payments (purchase_id, amount, method, transaction_ref, paid_at, payment_status)
              VALUES (%s,%s,%s,%s,%s,%s)
            """, (purchase_id, amount, method, transaction_ref, paid_at, payment_status))
        return render_template("feedback.html", title="Create Payment", message="Payment recorded successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Payment", message=f"Error: {e}")

def get_persons_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT person_id, CONCAT(first_name,' ',last_name,' — ',COALESCE(email,'no email')) AS label
          FROM persons ORDER BY last_name, first_name
        """)
        return cur.fetchall()

@app.route("/event_organizers/new")
def event_organizers_new():
    return render_template("event_organizers_new.html", events=get_events(), persons=get_persons_for_dropdown())

@app.route("/event_organizers/create", methods=["POST"])
def event_organizers_create():
    event_id = request.form.get("event_id")
    person_id = request.form.get("person_id")
    person_role = request.form.get("person_role") or None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO event_organizers (event_id, person_id, person_role)
              VALUES (%s,%s,%s)
            """, (event_id, person_id, person_role))
        return render_template("feedback.html", title="Assign Organizer", message="Organizer assigned.")
    except Exception as e:
        return render_template("feedback.html", title="Assign Organizer", message=f"Error: {e}")

def get_available_tickets():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT t.ticket_id,
                 CONCAT('#',t.ticket_id,' — ',e.title,' — ',
                        COALESCE(CONCAT(s.seat_section,'-',s.row_label,'-',s.seat_number),'GENERAL'),
                        ' — €',t.face_value) AS label
          FROM tickets t
          JOIN events e ON e.event_id=t.event_id
          LEFT JOIN seats s ON s.seat_id=t.seat_id
          WHERE NOT EXISTS (SELECT 1 FROM purchase_items pi WHERE pi.ticket_id=t.ticket_id)
          ORDER BY e.start_time DESC, t.ticket_id
        """)
        return cur.fetchall()

@app.route("/purchase_items/new")
def purchase_items_new():
    return render_template("purchase_items_new.html",
                           purchases=get_purchases_for_dropdown(),
                           tickets=get_available_tickets())

@app.route("/purchase_items/create", methods=["POST"])
def purchase_items_create():
    purchase_id = request.form.get("purchase_id")
    ticket_id = request.form.get("ticket_id")
    price_paid = request.form.get("price_paid")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO purchase_items (purchase_id, ticket_id, price_paid)
              VALUES (%s,%s,%s)
            """, (purchase_id, ticket_id, price_paid))
        return render_template("feedback.html", title="Add Ticket to Purchase", message="Ticket added to purchase.")
    except Exception as e:
        return render_template("feedback.html", title="Add Ticket to Purchase", message=f"Error: {e}")

@app.route("/event-venue/new")
def event_venue_new():
    return render_template("events_venue_new.html", events=get_events(), venues=get_venues())

@app.route("/event-venue/create", methods=["POST"])
def event_venue_create():
    event_id = request.form.get("event_id")
    venue_id = request.form.get("venue_id")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE events SET venue_id=%s WHERE event_id=%s", (venue_id, event_id))
        return render_template("feedback.html", title="Link Event ↔ Venue", message="Event venue updated.")
    except Exception as e:
        return render_template("feedback.html", title="Link Event ↔ Venue", message=f"Error: {e}")
