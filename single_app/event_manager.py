import flet as ft
import mysql.connector
from mysql.connector import Error
import datetime


def create_database(host, user, password, db_name):
    try:

        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    Name VARCHAR(30),
    username VARCHAR(30),
    pwd VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS events (
    EventID INT NOT NULL PRIMARY KEY,
    EventName VARCHAR(60),
    StartTime TIME,
    EndTime TIME,
    Date DATE,
    VenueID VARCHAR(12),
    type VARCHAR(30),
    image VARCHAR(1000),
    description VARCHAR(1000)
);

CREATE TABLE IF NOT EXISTS venues (
    VenueName VARCHAR(30),
    VenueID VARCHAR(30),
    RowsColumns VARCHAR(6),
    NoSeats VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS tickets (
    TicketID VARCHAR(100),
    Username VARCHAR(30),
    Seats VARCHAR(256),
    EventID VARCHAR(30),
    VenueID VARCHAR(30)
);


CREATE TABLE IF NOT EXISTS lockedseats (
    EventID VARCHAR(30),
    username VARCHAR(30),
    seats VARCHAR(100)
);''')
            print(f"Database '{db_name}' created successfully (or already exists).")

    except Error as e:
        print(f"Error: {e}")
    
    finally:
        if connection.is_connected():
            connection.close()

def add_venue(venue_name, venue_id, rowscolumn, noseats):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="eventdb"
        )

        noseats_json = ""
        for i in noseats:
            noseats_json += i + ","
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO venues (VenueName, VenueID, RowsColumns, NoSeats) 
                VALUES (%s, %s, %s, %s)
            """, (venue_name, venue_id, rowscolumn, noseats_json))
            connection.commit()
    
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

def add_event(event_name, event_id, event_date, event_start_time, event_end_time, event_description, venue_id, event_image, event_type):
    connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",   # Replace with your actual password
    database="eventdb")
    cursor = connection.cursor()
    cursor.execute("SELECT venueid FROM venues where venueid = %s", (venue_id,))
    venues = cursor.fetchone()
    
    
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="admin",
            database="eventdb"
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO events (EventName, EventID, Date, StartTime, EndTime, Description, VenueID, image, type) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (event_name, event_id, event_date, event_start_time, event_end_time, event_description, venue_id, event_image, event_type))
            connection.commit()
            # print("Event added successfully.")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            connection.close()


def create_seating_view(page):
    rows_input = ft.TextField(label="Rows", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    columns_input = ft.TextField(label="Columns", width=120, keyboard_type=ft.KeyboardType.NUMBER)
    mode = ft.Text(value="Mode: Add", size=16, weight="bold")
    grid_container = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    seat_controls = {}  
    feedback_text = ft.Text()
    container_style = dict(width=30, height=30, padding=0, margin=0)

    def generate_grid(e):
        try:
            rows = int(rows_input.value)
            cols = int(columns_input.value)
            if rows <= 0 or cols <= 0:
                raise ValueError("Rows and columns must be positive numbers")
            grid_container.controls = []
            seat_controls.clear()

        
            header_row = ft.Row([
                ft.Container(width=24)
            ] + [
                ft.Text(str(col+1), size=12, weight="bold", width=30, text_align=ft.TextAlign.CENTER)
                for col in range(cols)
            ], spacing=2)
            grid_container.controls.append(header_row)

            # Grid rows
            for row in range(rows):
                row_letter = chr(65 + row)
                row_controls = [ft.Text(row_letter, size=12, weight="bold", width=24, text_align=ft.TextAlign.CENTER)]
                for col in range(cols):
                    seat_label = f"{row_letter}{col+1}"
                    checkbox = ft.Checkbox(value=False, data=seat_label, active_color=(ft.Colors.ON_SURFACE_VARIANT if mode.value == "Mode: Add" else ft.Colors.BLACK))
                    seat_controls[seat_label] = checkbox
                    control = ft.Container(content=checkbox, **container_style)
                    row_controls.append(control)
                grid_container.controls.append(ft.Row(row_controls, spacing=2))
            page.update()
        except ValueError as e:
            page.snack_bar = ft.SnackBar(ft.Text(str(e)))
            page.snack_bar.open = True
            page.update()

    def toggle_mode(e):
        if mode.value == "Mode: Add":
            mode.value = "Mode: Remove"
        else:
            mode.value = "Mode: Add"
        mode.update()

    def submit(e):
        checkboxes = []
        for seat_label, checkbox in seat_controls.items():
            if mode.value == "Mode: Add" and not checkbox.value:
                checkboxes.append(seat_label)
            elif mode.value == "Mode: Remove" and checkbox.value:
                checkboxes.append(seat_label)
        result_text = "Selected seats: " + ", ".join(checkboxes) if checkboxes else "No seats selected"
        venue_id = page.session.get("venue_id")
        venue_name = page.session.get("venue_name")
        rowscolumn = f"{rows_input.value}x{columns_input.value}"
        add_venue(venue_name, venue_id, rowscolumn, checkboxes)
        page.snack_bar = ft.SnackBar(ft.Text(result_text))
        page.snack_bar.open = True
        page.update()

    generate_button = ft.OutlinedButton(
        "Generate Grid",
        on_click=generate_grid,
        icon=ft.Icons.GRID_VIEW
    )
    toggle_button = ft.OutlinedButton(
        "Toggle Mode",
        on_click=toggle_mode,
        icon=ft.Icons.SWAP_HORIZ
    )
    submit_button = ft.OutlinedButton(
        "Submit",
        on_click=submit,
        icon=ft.Icons.CHECK_CIRCLE
    )

    return ft.View(
        "/seating",
        [
            ft.AppBar(
                title=ft.Text("Seating Arrangement"),
                center_title=True,
                bgcolor="surface_variant",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: page.go("/")
                    )
                ]
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [rows_input, columns_input, generate_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20
                        ),
                        ft.Row(
                            [mode, toggle_button, submit_button],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20
                        ),
                        ft.Divider(),
                        grid_container,
                        ft.Row([feedback_text], alignment=ft.MainAxisAlignment.CENTER)
                    ],
                    expand=True,
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO
                ),
                padding=20,
                expand=True
            )
        ]
    )

def create_venue_view(page):
    venue_name = ft.TextField(hint_text="Venue Name")
    venue_id = ft.TextField(hint_text="Venue ID")
    
    controls = [
        venue_name,
        venue_id,
        ft.OutlinedButton("Proceed To seating creation", icon=ft.Icons.EVENT_SEAT_ROUNDED, on_click=lambda _:(page.session.set("venue_id", venue_id.value), page.session.set("venue_name", venue_name.value),page.go("/seating")))
    ]   
    return ft.View(
        '/venue',
        [
            ft.AppBar(
                title=ft.Text("Create Venue"), center_title=True, bgcolor="surface_variant",
                actions=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: (page.go("/"))) ]
            ),
            ft.Column(controls)
        ]
    )



def create_home_view(page):
    return ft.View(
        "/",
        [
            ft.AppBar(
                title=ft.Text("EventBite Manager"), center_title=True, bgcolor="surface_variant"
            ),
            ft.Column(
                [
                    ft.Text("Welcome to EventBite Manager"),
                    ft.OutlinedButton("Add Venue", on_click=lambda _: page.go("/venue"), icon=ft.Icons.STADIUM),
                    ft.OutlinedButton("Add Event", on_click=lambda _: page.go("/event"), icon=ft.Icons.THEATERS)
                ]
            )
        ]
    )

def create_event_view(page):
    connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",   # Replace with your actual password
    database="eventdb")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM venues")
    venues = cursor.fetchall()
    event_name = ft.TextField(hint_text="Name of Event")
    event_id = ft.TextField(hint_text="Event ID")
    event_date = ft.DatePicker(
        first_date=datetime.datetime.today(),
        last_date=datetime.datetime.today() + datetime.timedelta(days=365)
    )
    event_start_time = ft.TimePicker(
        confirm_text="Confirm",
        cancel_text="Cancel",   
        help_text="Start Time",
    )
    event_end_time = ft.TimePicker(
        confirm_text="Confirm",
        cancel_text="Cancel",   
        help_text="End Time",
    )
    event_description = ft.TextField(hint_text="Event Description")

    event_image = ft.TextField(hint_text="Image url of the banner")
    event_type = ft.TextField(hint_text="Event Type")
    venue_dropdown = ft.Dropdown(
        label="Select Venue",
        options=[ft.dropdown.Option(venue[1] + ', ' + venue[0]) for venue in venues]
    )
    controls = [
        event_name,
        event_id,
        ft.Row([
            
        ft.OutlinedButton(
            'Date',
            on_click=lambda _: page.open(event_date),
            icon=ft.Icons.CALENDAR_TODAY_ROUNDED
        ),
        ft.OutlinedButton(
            'Start Time',
            on_click=lambda _: page.open(event_start_time),
            icon=ft.Icons.ALARM_OUTLINED
        ),  
        ft.OutlinedButton(
            'End Time',
            on_click=lambda _: page.open(event_end_time),
            icon=ft.Icons.ALARM_OUTLINED
        ),
        ]),
        event_description,
        ft.Row([
            event_image,
            event_type,
        ]),
        venue_dropdown,
        ft.OutlinedButton("Create Event", icon=ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, on_click=lambda _: add_event(event_name.value, event_id.value, event_date.value, event_start_time.value, event_end_time.value, event_description.value, event_image.value, venue_dropdown.value.split(",")[0], event_image, event_type.value))
    ]
    return ft.View(
        '/event',
        [
            ft.AppBar(
                title=ft.Text("Create Event"), center_title=True, bgcolor="surface_variant",
                actions=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: (page.go("/"))) ]
            ),
            ft.Column(
                controls,
                expand=True,
                spacing=20,
                scroll=ft.ScrollMode.AUTO
            )
        ]
    )
def main(page: ft.Page):
    page.title = "EventBite Venue"
    page.theme_mode = ft.ThemeMode.DARK
    page.fonts = {
        "Roboto": "Roboto-Regular.ttf",
    }
    page.theme = ft.Theme(font_family="Roboto")
    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(create_home_view(page))
        elif page.route == "/venue":
            page.views.append(create_venue_view(page))
        elif page.route == "/seating":
            page.views.append(create_seating_view(page))
        elif page.route == "/event":
            page.views.append(create_event_view(page))
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go('/')

create_database(
    host="localhost",
    user="root",
    password="admin",   # Replace with your actual password
    db_name="EventDB")    

ft.app(target=main)

