import requests
from datetime import datetime, date, timedelta
import json
from typing import Any, Dict, List, Optional, Tuple, Union
import socket
def listen_for_broadcast(port=37020):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(f"Listening for server IP on UDP port {port}...")

    while True:
        data, addr = sock.recvfrom(1024)
        server_ip = data.decode("utf-8")
        print(f"Detected server at IP: {server_ip}")
        return server_ip  
BASE_URL = "http://" + listen_for_broadcast() + ":5000"
print(BASE_URL)

def _parse_datetime(value: str) -> date:
    """Parse date string in YYYY-MM-DD format to date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()

def _parse_timedelta(value: str) -> timedelta:
    """Parse timedelta string (HH:MM:SS) to timedelta object."""
    h, m, s = map(int, value.split(':'))
    return timedelta(hours=h, minutes=m, seconds=s)

def _desanitize(obj: Any) -> Any:
    """Convert serialized types back to Python objects."""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in ['Date', 'EarliestDate'] and isinstance(v, str):
                result[k] = _parse_datetime(v)
            elif k in ['StartTime', 'EndTime'] and isinstance(v, str):
                result[k] = _parse_timedelta(v)
            else:
                result[k] = _desanitize(v)
        return result
    elif isinstance(obj, list):
        return [_desanitize(item) for item in obj]
    return obj

def _make_request(endpoint: str, method: str = 'GET', **kwargs) -> Any:
    print(kwargs)
    """Make an HTTP request to the server and handle the response."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, json=kwargs.get('data'))
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return _desanitize(response.json())
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        raise

def list_events(event_type: str = None) -> List[Dict[str, Any]]:
    """List all events, optionally filtered by type."""
    print(event_type)
    params = {}
    if event_type:
        return _make_request("list_events", event_type=event_type)
    return _make_request("list_events")

def get_event_name(event_id: int) -> str:
    """Get the name of an event by its ID."""
    return _make_request("get_event_name", event_id=event_id)

def get_event_shows(event_name: str) -> List[Dict[str, Any]]:
    """Get all shows for a specific event name."""
    return _make_request("get_event_shows", event_name=event_name)

def get_event_types() -> List[str]:
    """Get all distinct event types."""
    return _make_request("get_event_types")

def register_user(username: str, password: str, name: str) -> bool:
    """Register a new user."""
    return _make_request(
        "register_user", 
        method='POST', 
        data={'username': username, 'password': password, 'name': name}
    )

def check_credentials(username: str, password: str) -> bool:
    """Check if the provided credentials are valid."""
    return _make_request(
        "check_credentials", 
        method='POST', 
        data={'username': username, 'password': password}
    )

def get_venue_seats(event_id: int) -> Tuple[List[str], List[str], List[str]]:
    """Get all, unavailable, and booked seats for an event."""
    result = _make_request("get_venue_seats", event_id=event_id)
    return result['all'], result['unavailable'], result['booked']

def lock_seats(selected_seats: List[str], event_id: int) -> bool:
    print(selected_seats, event_id)
    return _make_request(
        "lock_seats", 
        method='POST', 
        data={'selected_seats': selected_seats, 'event_id': event_id}
    )

def create_ticket(event_id: int, username: str, seats: List[str]) -> Optional[int]:

    return _make_request(
        "create_ticket",
        method='POST',
        data={'event_id': event_id, 'username': username, 'seats': seats}
    )

def get_user_tickets(username: str) -> List[Dict[str, Any]]:
    """Get all tickets for a user."""
    return _make_request("get_user_tickets", username=username)

def release_locked_seats(event_id: int, seats: List[str]) -> None:
    """Release locked seats after a delay."""
    _make_request(
        "release_locked_seats",
        method='POST',
        data={'event_id': event_id, 'seats': seats}
    )
