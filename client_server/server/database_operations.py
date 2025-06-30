
import json
import random
import time
from typing import List, Dict, Any, Optional, Tuple
from mysql.connector import connect

# Database connection
conn = connect(
    host="localhost",
    user="root",
    password="admin",
    database="EventDB"
)
cursor = conn.cursor(dictionary=True)

def execute_query(query: str, params: tuple = None, fetch: str = None) -> Any:
    """Execute a query and return results.
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch: 'one' for single row, 'all' for all rows, None for no results
    """
    try:
        cursor.execute(query, params or ())
        if fetch == 'one':
            return cursor.fetchone()
        elif fetch == 'all':
            return cursor.fetchall()
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise

def get_event_name(event_id: int) -> str:
    query = "SELECT EventName FROM Events WHERE EventID = %s"
    return execute_query(query, (event_id,), fetch='one')['EventName']

def list_events(event_type: str = None) -> List[Dict[str, Any]]:
    """List all events, optionally filtered by type."""
    if event_type and event_type.lower() != "all":
        query = """
            SELECT E.*, V.VenueName 
            FROM Events E 
            JOIN Venues V ON E.VenueID = V.VenueID 
            WHERE E.Date >= CURDATE() AND LOWER(E.type) = %s
            ORDER BY E.EventName, E.Date, E.StartTime
        """
        rows = execute_query(query, (event_type.lower(),), fetch='all') or []
    else:
        query = """
            SELECT E.*, V.VenueName 
            FROM Events E 
            JOIN Venues V ON E.VenueID = V.VenueID 
            WHERE E.Date >= CURDATE()
            ORDER BY E.EventName, E.Date, E.StartTime
        """
        rows = execute_query(query, fetch='all') or []
    
    events_by_name = {}
    for row in rows:
        name = row['EventName']
        if name not in events_by_name:
            events_by_name[name] = {
                'EventName': name,
                'type': row['type'],
                'image': row['image'],
                'description': row['description'],
                'EarliestDate': row['Date'],
                'ShowCount': 0,
                'shows': []
            }
        events_by_name[name]['shows'].append(row)
        events_by_name[name]['ShowCount'] += 1
        if row['Date'] < events_by_name[name]['EarliestDate']:
            events_by_name[name]['EarliestDate'] = row['Date']
    
    result = list(events_by_name.values())
    result.sort(key=lambda e: (e['EarliestDate'], e['EventName']))
    return result

def get_event_shows(event_name: str) -> List[Dict[str, Any]]:
    """Get all shows for a specific event name."""
    query = """
        SELECT E.*, V.VenueName, V.VenueID 
        FROM Events E 
        JOIN Venues V ON E.VenueID = V.VenueID 
        WHERE E.EventName = %s AND E.Date >= CURDATE()
        ORDER BY E.Date, E.StartTime
    """
    return execute_query(query, (event_name,), fetch='all') or []

def get_event_types() -> List[str]:
    """Get all distinct event types."""
    query = "SELECT DISTINCT type FROM Events WHERE Date >= CURDATE() AND type IS NOT NULL"
    results = execute_query(query, fetch='all') or []
    return [row['type'] for row in results]

def register_user(username: str, password: str, name: str) -> bool:
    """Register a new user.
    
    Args:
        username: The username for the new account
        password: The password for the new account
        name: The user's full name
        
    Returns:
        bool: True if registration was successful, False if username already exists
    """
    # Check if username already exists
    check_query = "SELECT 1 FROM Users WHERE Username = %s LIMIT 1"
    if execute_query(check_query, (username,), fetch='one'):
        return False
    
    # Create new user
    insert_query = """
        INSERT INTO Users (Username, pwd, Name) 
        VALUES (%s, %s, %s)
    """
    try:
        execute_query(insert_query, (username, password, name))
        return True
    except Exception as e:
        print(f"Error registering user: {e}")
        return False

def check_credentials(username: str, password: str) -> bool:
    """Check if the provided credentials are valid."""
    query = "SELECT 1 FROM Users WHERE Username = %s AND pwd = %s LIMIT 1"
    return bool(execute_query(query, (username, password), fetch='one'))

def get_venue_seats(event_id: int) -> Tuple[List[str], List[str], List[str]]:
    """Get all, unavailable, and booked seats for an event."""
    query = """
        SELECT V.RowsColumns, V.NoSeats 
        FROM Events E 
        JOIN Venues V ON E.VenueID = V.VenueID 
        WHERE E.EventID = %s
    """
    venue = execute_query(query, (event_id,), fetch='one')
    
    if not venue:
        return [], [], []
    
    rows, cols = map(int, venue['RowsColumns'].split('x'))
    all_seats = [f"{chr(65 + r)}{c}" for r in range(rows) for c in range(1, cols + 1)]
    
    unavailable = venue['NoSeats'].replace(" ", "").split(',') if venue['NoSeats'] else []
    
    booked = []
    query = "SELECT Seats FROM tickets WHERE EventID = %s"
    results = execute_query(query, (event_id,), fetch='all') or []
    for row in results:
        seats = row['Seats']
        if seats:
            try:
                booked.extend(json.loads(seats))
            except (json.JSONDecodeError, TypeError):
                booked.extend([s.strip() for s in str(seats).split(',')])
    
    locked = []
    query = "SELECT seats FROM lockedseats WHERE EventID = %s"
    results = execute_query(query, (event_id,), fetch='all') or []
    
    for row in results:
        seats = row['seats']
        if seats:
            try:
                locked.extend(json.loads(seats))
            except (json.JSONDecodeError, TypeError):
                locked.extend([s.strip() for s in str(seats).split(',')])

    for seat in locked:
        booked.append(seat)
    print(list(set(booked)))
    return all_seats, unavailable, list(set(booked))

def lock_seats(selected_seats: List[str], event_id: int) -> bool:
    """Lock selected seats for an event."""
    try:
        query = """
            INSERT INTO lockedseats (EventID, Seats) 
            VALUES (%s, %s)
        """
        execute_query(query, (event_id, json.dumps(selected_seats)))
        release_locked_seats(event_id, json.dumps(selected_seats))
        return True
    except Exception as e:
        print(f"Error locking seats: {e}")
        return False

def create_ticket(event_id: int, username: str, seats: List[str]) -> Optional[int]:
    """Create a new ticket and return the ticket ID."""
    ticket_id = random.randint(100000, 999999)
    query = """
        INSERT INTO tickets (TicketID, EventID, Seats, Username) 
        VALUES (%s, %s, %s, %s)
    """
    try:
        execute_query(query, (ticket_id, event_id, json.dumps(seats), username))
        return ticket_id
    except Exception as e:
        print(f"Error creating ticket: {e}")
        return None

def get_user_tickets(username: str) -> List[Dict[str, Any]]:
    """Get all tickets for a user."""
    query = """
        SELECT t.*, e.EventName, e.Date, e.StartTime, v.VenueName
        FROM tickets t
        JOIN Events e ON t.EventID = e.EventID
        JOIN Venues v ON e.VenueID = v.VenueID
        WHERE t.Username = %s
        ORDER BY e.Date DESC, e.StartTime DESC
    """
    return execute_query(query, (username,), fetch='all') or []

def release_locked_seats(event_id: int, seats: str) -> None:
    """Release locked seats after a delay."""
    import threading
    
    def _release():
        time.sleep(300)  # 10 second delay
        query = "DELETE FROM lockedseats WHERE EventID = %s AND Seats = %s"
        execute_query(query, (event_id, seats))
    
    thread = threading.Thread(target=_release)
    thread.daemon = True
    thread.start()


# print(list_events())