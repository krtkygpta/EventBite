from flask import Flask, request, jsonify
from database_operations import *
from datetime import datetime, date, timedelta
import json
from functools import wraps

app = Flask(__name__)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, timedelta):
        # Convert timedelta to HH:MM:SS format
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    raise TypeError(f"Type {type(obj)} not serializable")

def api_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # Convert result to JSON-serializable format
            response_data = json.loads(json.dumps(result, default=json_serial))
            return jsonify(response_data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return wrapper

@app.route("/get_event_name")
@api_response
def api_get_event_name():
    event_id = int(request.args.get('event_id'))
    if not event_id:
        raise ValueError("event_id parameter is required")
    return get_event_name(event_id)

@app.route("/list_events")
@api_response
def api_list_events():
    event_type = request.args.get("event_type")
    return list_events(event_type)

@app.route("/get_event_shows")
@api_response
def api_get_event_shows():
    event_name = request.args.get("event_name")
    if not event_name:
        raise ValueError("event_name parameter is required")
    return get_event_shows(event_name)

@app.route("/get_event_types")
@api_response
def api_get_event_types():
    return get_event_types()

@app.route("/register_user", methods=["POST"])
@api_response
def api_register_user():
    data = request.get_json()
    if not all(k in data for k in ['username', 'password', 'name']):
        raise ValueError("Missing required fields: username, password, name")
    return register_user(data['username'], data['password'], data['name'])

@app.route("/check_credentials", methods=["POST"])
@api_response
def api_check_credentials():
    data = request.get_json()
    if not all(k in data for k in ['username', 'password']):
        raise ValueError("Missing required fields: username, password")
    return check_credentials(data['username'], data['password'])

@app.route("/get_venue_seats")
@api_response
def api_get_venue_seats():
    try:
        event_id = int(request.args.get("event_id"))
    except (TypeError, ValueError):
        raise ValueError("Invalid or missing event_id parameter")
    all_seats, unavailable, booked = get_venue_seats(event_id)
    return {
        "all": all_seats,
        "unavailable": unavailable,
        "booked": booked
    }

@app.route("/lock_seats", methods=["POST"])
@api_response
def api_lock_seats():
    data = request.get_json()
    if not all(k in data for k in ['selected_seats', 'event_id']):
        raise ValueError("Missing required fields: selected_seats, event_id")
    return lock_seats(data['selected_seats'], data['event_id'])

@app.route("/create_ticket", methods=["POST"])
@api_response
def api_create_ticket():
    data = request.get_json()
    if not all(k in data for k in ['event_id', 'username', 'seats']):
        raise ValueError("Missing required fields: event_id, username, seats")
    ticket_id = create_ticket(data['event_id'], data['username'], data['seats'])
    if not ticket_id:
        raise RuntimeError("Failed to create ticket")
    return {"ticket_id": ticket_id}

@app.route("/get_user_tickets")
@api_response
def api_get_user_tickets():
    username = request.args.get("username")
    if not username:
        raise ValueError("username parameter is required")
    return get_user_tickets(username)

@app.route("/release_locked_seats", methods=["POST"])
@api_response
def api_release_locked_seats():
    data = request.get_json()
    if not all(k in data for k in ['event_id', 'seats']):
        raise ValueError("Missing required fields: event_id, seats")
    release_locked_seats(data['event_id'], data['seats'])
    return {"status": "released"}

if __name__ == "__main__":
    # Run on all available network interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
