from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this for production!

BOOKINGS_FILE = "bookings.json"
AUDIT_LOG_FILE = "audit_log.json"
CUSTOMERS_FILE = "customers.json"
USERS_FILE = "users.json"

def load_file(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_file(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def save_booking(booking):
    bookings = load_file(BOOKINGS_FILE)
    bookings.append(booking)
    save_file(BOOKINGS_FILE, bookings)

def log_action(action_type, user, description):
    audit_log = load_file(AUDIT_LOG_FILE)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action_type,
        "user": user,
        "description": description
    }
    audit_log.append(log_entry)
    save_file(AUDIT_LOG_FILE, audit_log)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/book", methods=["POST"])
def book():
    booking = {
        "booking_name": request.form["booking_name"],
        "phone": request.form["phone"],
        "email": request.form["email"],
        "billing_address": request.form["billing_address"],
        "pickup_address": request.form["pickup_address"],
        "trip_date": request.form["trip_date"],
        "pickup_time": request.form["pickup_time"],
        "return_time": request.form["return_time"],
        "trip_type": request.form["trip_type"],
        "passengers": request.form["passengers"],
        "rate": request.form["rate"],
        "driver_bus": request.form["driver_bus"],
        "notes": request.form["notes"],
        "timestamp": datetime.now().isoformat()
    }

    save_booking(booking)
    log_action("Booking Created", booking["booking_name"],
               f"{booking['booking_name']} booked a trip on {booking['trip_date']} at {booking['pickup_time']}")

    return jsonify({"success": True, "message": "Booking submitted successfully!"})

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_file(USERS_FILE)
        username = request.form["username"]
        password = request.form["password"]

        for user in users:
            if user["username"] == username and user["password"] == password:
                session["user"] = username
                return redirect("/dashboard")
        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    bookings = load_file(BOOKINGS_FILE)
    return render_template("dashboard.html", bookings=bookings, user=session["user"])

@app.route("/customers")
def customers():
    if "user" not in session:
        return redirect("/login")
    customers = load_file(CUSTOMERS_FILE)
    return render_template("customers.html", customers=customers)

@app.route("/add-customer", methods=["GET", "POST"])
def add_customer():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        customer = {
            "name": request.form["name"],
            "email": request.form["email"],
            "phone": request.form["phone"],
            "address": request.form["address"]
        }
        customers = load_file(CUSTOMERS_FILE)
        customers.append(customer)
        save_file(CUSTOMERS_FILE, customers)

        log_action("Customer Added", session["user"], f"Added customer {customer['name']}")
        return redirect("/customers")

    return render_template("add_customer.html")

@app.route("/customer-login", methods=["GET", "POST"])
def customer_login():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        bookings = load_file(BOOKINGS_FILE)

        match = any(b["booking_name"] == name and b["email"] == email for b in bookings)
        if match:
            session["customer"] = name
            session["customer_email"] = email
            return redirect("/customer-dashboard")
        else:
            return render_template("customer_login.html", error="No booking found with that info.")

    return render_template("customer_login.html")

@app.route("/customer-dashboard")
def customer_dashboard():
    if "customer" not in session:
        return redirect("/customer-login")

    name = session["customer"]
    email = session["customer_email"]
    bookings = load_file(BOOKINGS_FILE)
    user_bookings = [b for b in bookings if b["booking_name"] == name and b["email"] == email]

    return render_template("customer_dashboard.html", bookings=user_bookings, customer=name)

@app.route("/customer-logout")
def customer_logout():
    session.pop("customer", None)
    session.pop("customer_email", None)
    return redirect("/customer-login")

@app.route("/audit-log")
def audit_log():
    if "user" not in session:
        return redirect("/login")
    return jsonify(load_file(AUDIT_LOG_FILE))

if __name__ == "__main__":
    app.run(debug=True)
