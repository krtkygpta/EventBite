import flet as ft
import json
import urllib.parse
from database_operations import (
    list_events,
    get_event_shows,
    get_event_types,
    check_credentials,
    get_venue_seats,
    lock_seats,
    create_ticket,
    get_user_tickets,
    release_locked_seats,
    register_user,
    get_event_name,
)

def create_auth_view(page, is_register=False):
    def handle_auth(e):
        username = username_field.value.strip()
        password = password_field.value
        
        if not username or not password:
            update_error("Username and password are required")
            return
            
        if is_register:
            name = name_field.value.strip()
            if not name:
                update_error("Name is required")
                return
                
            if register_user(username, password, name):

                page.session.set("is_logged_in", True)
                page.session.set("username", username)
                page.client_storage.set("is_logged_in", True)
                page.client_storage.set("username", username)
                page.go("/")
            else:
                update_error("Username already exists")
        else:
            if check_credentials(username, password):
                page.session.set("is_logged_in", True)
                page.session.set("username", username)
                page.client_storage.set("is_logged_in", True)
                page.client_storage.set("username", username)
                page.go("/")
            else:
                update_error("Invalid username or password")
    
    def update_error(message: str):
        error_text.value = message
        error_text.visible = True
        page.update()

    field_style = {
        "width": 300,
        "border_color": "white",
        "border_width": 1,
        "border_radius": 30,
        "text_size": 16
    }

    username_field = ft.TextField(hint_text="Username", **field_style)
    password_field = ft.TextField(hint_text="Password", password=True, can_reveal_password=True, **field_style)
    error_text = ft.Text(color="red", visible=False)
    
    controls = [username_field, password_field]
    
    if is_register:
        name_field = ft.TextField(hint_text="Name", **field_style)
        controls.insert(-1, name_field)
        title = "EventBite Register"
        button_text = "Register"
        route = "/register"
    else:
        title = "EventBite Login"
        button_text = "Login"
        route = "/login"
        controls.append(
            ft.Row([
                ft.ElevatedButton(button_text, on_click=handle_auth, icon=ft.Icons.LOGIN),
                ft.OutlinedButton("Register", on_click=lambda _: page.go("/register"), icon=ft.Icons.PERSON_ADD_ALT_1)
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

    if is_register:
        controls.append(ft.ElevatedButton(button_text, on_click=handle_auth))
    
    controls.append(error_text)

    return ft.View(
        route,
        [
            ft.AppBar(title=ft.Text(title), center_title=True, bgcolor="surface_variant"),
            ft.Column(
                controls,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20
    )

class EventCard(ft.Container):
    def __init__(self, event, on_click):
        super().__init__(
            width=180, height=240, border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE,
            on_click=on_click, data=event['EventName'],
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.BLACK26, offset=ft.Offset(0, 5)),
            content=ft.Stack([
                ft.Image(
                    src=event['image'] or "https://linda-hoang.com/wp-content/uploads/2014/10/img-placeholder-dark.jpg",
                    fit=ft.ImageFit.COVER, width=180, height=240, border_radius=10,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(event['EventName'], color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, 
                               size=16, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{event['EarliestDate']} • {event['ShowCount']} shows", 
                               color=ft.Colors.WHITE, size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=4, alignment=ft.MainAxisAlignment.END),
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.bottom_center, end=ft.alignment.top_center,
                        colors=[ft.Colors.with_opacity(0.9, ft.Colors.BLACK), ft.Colors.with_opacity(0.1, ft.Colors.BLACK)]
                    ),
                    padding=10, expand=True,
                ),
            ], expand=True),
        )
def create_show_details_view_single(page, event_id):
    event_name = get_event_name(event_id)
    all_shows = get_event_shows(event_name)
    show_data = next((event for event in all_shows if event["EventID"] == int(event_id)), None)
    
    if not show_data:
        print(f"Show with ID {event_id} not found.")
        return ft.View(
            f"/show/{event_id}",
            [
                ft.AppBar(title=ft.Text("Error"), bgcolor="surface_variant", actions=[
                    ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda e: page.go("/tickets"),
                        tooltip="Back"
                    )
                ]),
                ft.Text("Show not found."),
            ]
        )

    print(f"Loading show with ID {event_id}.")
    return ft.View(
        f"/show/{event_id}", 
        [
            ft.AppBar(title=ft.Text(show_data['EventName']), bgcolor="surface_variant", actions=[
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda e: page.go("/"),
                    tooltip="Back"
                ),
                ft.IconButton(
                    ft.Icons.LOCAL_MOVIES,
                    on_click=lambda e: page.go("/tickets"),
                    tooltip="Tickets"
                ),
            ]),
            ft.Column(
                [
                    ft.Text(f"Venue: {show_data['VenueName']}"),
                    ft.Text(f"Date: {show_data['Date'].strftime('%A, %B %d, %Y')}"),
                    ft.Text(f"Time: {show_data['StartTime']} - {show_data['EndTime']}", text_align=ft.TextAlign.CENTER),
                    ft.Text(f'Date: {show_data["Date"]}'),
                    ft.Divider(height=20),
                    ft.ElevatedButton("Book Seats", on_click=lambda _: page.go(f"/seating/{event_id}"), icon=ft.Icons.BOOKMARK)
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=page.width 
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
def create_homepage_view(page):
    event_types = ['All'] + get_event_types()
    
    def on_type_selected(e):
        event_type = e.control.data
        events_grid.content = create_events_grid(page, event_type)
        page.update()
    
    type_tabs = ft.Row(scroll="auto", spacing=0, height=48, vertical_alignment=ft.CrossAxisAlignment.START)
    
    for event_type in event_types:
        tab = ft.Container(
            content=ft.Text(event_type, size=14, weight=ft.FontWeight.W_500),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=20, ink=True, on_click=on_type_selected, data=event_type,
        )
        type_tabs.controls.append(tab)
    
    events_grid = ft.Container(content=create_events_grid(page, 'All'), expand=True)
    
    return ft.View(
        "/",
        [
            ft.AppBar(
                title=ft.Text("EventBite Events", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                center_title=False, bgcolor=ft.Colors.SURFACE, elevation=0,
                actions=[
                    ft.IconButton(icon=ft.Icons.LOGOUT, on_click=lambda e: (page.client_storage.set("is_logged_in", False), page.session.set("is_logged_in", False), page.go("/login")), tooltip="logout"),
                    ft.IconButton(icon=ft.Icons.CONFIRMATION_NUMBER, on_click=lambda e: page.go("/tickets"), tooltip="My Tickets"),
                ]
            ),
            ft.Container(
                content=type_tabs,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            ),
            ft.Container(content=events_grid, padding=16, expand=True),
        ],
        padding=0, spacing=0,
    )

def create_events_grid(page, event_type):
    events = list_events(event_type if event_type != 'All' else None)
    
    if not events:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.EVENT_BUSY, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text("No events found", style=ft.TextThemeStyle.BODY_LARGE),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
            expand=True,
        )
    
    grid = ft.GridView(runs_count=2, max_extent=200, child_aspect_ratio=0.7, spacing=16, run_spacing=16, padding=0)
    
    for event in events:
        card_event = {
            'EventName': event['EventName'], 'type': event['type'], 'image': event['image'],
            'EarliestDate': event['EarliestDate'], 'ShowCount': event['ShowCount']
        }

        grid.controls.append(
            EventCard(event=card_event, on_click=lambda e, name=event['EventName']: page.go(f"/event/{urllib.parse.quote(name)}"))
        )
    
    return grid

def create_show_details_view(page, event_name):
    event_name = urllib.parse.unquote(event_name)
    shows = get_event_shows(event_name)
    
    if not shows:
        return ft.View(
            f"/event/{urllib.parse.quote(event_name)}",
            [
                ft.AppBar(
                    title=ft.Text("Event Not Found"), center_title=True, bgcolor="surface_variant",
                    actions=[ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/"), tooltip="Back")]
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.EVENT_BUSY, size=48, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Text("No upcoming shows found for this event.", style=ft.TextThemeStyle.BODY_LARGE),
                        ft.ElevatedButton("Back to Events", on_click=lambda e: page.go("/"), icon=ft.Icons.ARROW_BACK)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True),
                    expand=True, padding=20
                )
            ]
        )
    
    shows_by_date = {}
    for show in shows:
        if show['Date'] not in shows_by_date:
            shows_by_date[show['Date']] = []
        shows_by_date[show['Date']].append(show)
    
    show_tabs = []
    for date, date_shows in sorted(shows_by_date.items()):
        show_grid = ft.GridView(runs_count=3, max_extent=200, child_aspect_ratio=1.2, spacing=12, run_spacing=12, padding=16, expand=True)
        
        for show in sorted(date_shows, key=lambda x: x['StartTime']):
            show_grid.controls.append(
                ft.Card(
                    elevation=2,
                    content=ft.Container(
                        width=180, padding=12,
                        content=ft.Column([
                            ft.Text(show['StartTime'], style=ft.TextThemeStyle.HEADLINE_SMALL, weight=ft.FontWeight.BOLD),
                            ft.Text(show['VenueName'], style=ft.TextThemeStyle.BODY_MEDIUM, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(height=8),
                            ft.ElevatedButton("Book Now",icon=ft.Icons.BOOK_OUTLINED, on_click=lambda e, sid=show['EventID']: page.go(f"/seating/{sid}"), expand=True, height=36)
                        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ),
                )
            )
        
        show_tabs.append(ft.Tab(text=date.strftime("%a, %b %d"), content=show_grid))
    
    return ft.View(
        f"/event/{urllib.parse.quote(event_name)}",
        [
            ft.AppBar(
                title=ft.Text(event_name, style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                center_title=False, bgcolor=ft.Colors.SURFACE, elevation=0,
                actions=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/"), tooltip="Back"),
                    ft.IconButton(icon=ft.Icons.CONFIRMATION_NUMBER, on_click=lambda e: page.go("/tickets"), tooltip="My Tickets"),
                ]
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src=shows[0]['image'] or "https://linda-hoang.com/wp-content/uploads/2014/10/img-placeholder-dark.jpg",
                            width=page.width, height=200, fit=ft.ImageFit.COVER,
                        ),
                        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(event_name, style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                            ft.Text(shows[0].get('description', 'No description available.'), style=ft.TextThemeStyle.BODY_MEDIUM),
                        ], spacing=16),
                        padding=16,
                    ),
                    ft.Divider(height=1, thickness=1),
                    ft.Container(content=ft.Tabs(tabs=show_tabs, expand=True), expand=True),
                ], expand=True, spacing=0),
                expand=True,
            ),
        ],
        padding=0, spacing=0,
    )

def create_seating_view(page, event_id):
    seat_controls = {}
    feedback_text = ft.Text()
    all_seats, unavailable_seats, booked_seats = get_venue_seats(event_id)
    event_name = get_event_name(event_id)
    def book_clicked(e):
        selected_labels = [label for label, checkbox in seat_controls.items() if checkbox.value and not checkbox.disabled]
        if selected_labels:
            lock_seats(selected_labels, event_id)
            encoded_seats = urllib.parse.quote(json.dumps(selected_labels))
            page.go(f"/payment/{event_id}/{encoded_seats}")
        else:
            feedback_text.value = "Please select at least one available seat."
            page.update()

    row_letters = sorted(set(label[0] for label in all_seats))
    col_numbers = sorted({int(label[1:]) for label in all_seats})
    seat_set = set(all_seats)
    container_style = dict(width=30, height=30, padding=0, margin=0)

    seat_grid = ft.Column([
        ft.Row([ft.Container(width=24)] + [
            ft.Text(str(col), size=12, weight="bold", width=30, text_align=ft.TextAlign.CENTER)
            for col in col_numbers
        ], spacing=2)
    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    for row_letter in row_letters:
        row_controls = [ft.Text(row_letter, size=12, weight="bold", width=24, text_align=ft.TextAlign.CENTER)]
        
        for col_number in col_numbers:
            seat_label = f"{row_letter}{col_number}"
            if seat_label not in seat_set:
                row_controls.append(ft.Container(width=30))
                continue

            if seat_label in unavailable_seats:
                control = ft.Container(
                    content=ft.Checkbox(value=False, disabled=True, visible=False),
                    border=ft.BorderSide(1, ft.Colors.AMBER_ACCENT), border_radius=5, **container_style
                )
            else:
                is_booked = seat_label in booked_seats
                checkbox = ft.Checkbox(value=is_booked, disabled=is_booked)
                if not is_booked:
                    seat_controls[seat_label] = checkbox
                control = ft.Container(content=checkbox, **container_style)
                
            row_controls.append(control)
            
        seat_grid.controls.append(ft.Row(row_controls, spacing=2))

    return ft.View(
        "/seating",
        [
            ft.AppBar(
                title=ft.Text("Select Your Seats"), center_title=True, bgcolor="surface_variant",
                actions=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go(f"/event/{event_name}"))]
            ),
            ft.Text("Select available seats from the grid below.", text_align=ft.TextAlign.CENTER),
            ft.Row([
                ft.Row([
                    ft.Column([seat_grid], height=400, scroll=ft.ScrollMode.ALWAYS,
                             horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, scroll=ft.ScrollMode.ALWAYS, width="90%"),
            ft.Row([ft.ElevatedButton("Book Selected Seats", on_click=book_clicked, icon=ft.Icons.CHECK_CIRCLE_OUTLINE)], 
                  alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([feedback_text], alignment=ft.MainAxisAlignment.CENTER)
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

def create_payment_view(page, event_id, encoded_labels):
    def pay_clicked(event_id, selected_labels):
        username = page.session.get("username")
        if not username:
            page.go("/login")
            return
            
        ticket_id = create_ticket(event_id, username, selected_labels)
        if ticket_id:
            page.go('/')
        else:
            pass

    try:
        selected_labels = json.loads(urllib.parse.unquote(encoded_labels))
    except (json.JSONDecodeError, ValueError):
        selected_labels = []

    return ft.View(
        "/payment",
        [
            ft.AppBar(
                title=ft.Text("Payment"), center_title=True, bgcolor="surface_variant",
                actions=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go(f"/seating/{event_id}"))]
            ),
            ft.Text("Confirm Payment", text_align=ft.TextAlign.CENTER),
            ft.Text(f"Seats: {', '.join(selected_labels)}", text_align=ft.TextAlign.CENTER),
            ft.Row([ft.ElevatedButton("Pay", on_click=lambda e: pay_clicked(event_id, selected_labels), icon=ft.Icons.CREDIT_CARD)],
                  alignment=ft.MainAxisAlignment.CENTER)
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

def create_tickets_view(page):
    
    def show_ticket_details(ticket):
        try:
            seats = json.loads(ticket['Seats'])
            seats_text = ", ".join(seats)
        except (json.JSONDecodeError, TypeError):
            seats_text = str(ticket['Seats'] or "N/A")

        details = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Ticket #{ticket['TicketID']}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text(f"Event: {ticket['EventName']}", size=16, weight=ft.FontWeight.W_500),
                    ft.Text(f"Date: {ticket['Date'].strftime('%A, %B %d, %Y')}"),
                    ft.Text(f"Time: {ticket['StartTime']}"),
                    ft.Text(f"Seats: {seats_text}"),
                    ft.Divider(),
                    ft.Text("Venue Details", size=16, weight=ft.FontWeight.W_500),
                    ft.Text(f"{ticket['VenueName']}"),
                    ft.OutlinedButton("Event Details", icon=ft.Icons.INFO_OUTLINED, on_click=lambda e: page.go(f"/event_single/{ticket['EventID']}")),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=20,
        )

        bottom_sheet = ft.BottomSheet(
            ft.Container(
                content=details,
                padding=10,
            ),
            open=True,
            on_dismiss=lambda _: setattr(bottom_sheet, "open", False) or page.update(),
        )
        
        page.overlay.append(bottom_sheet)
        page.update()
    username = page.client_storage.get("username")
    if not username:
        page.go("/login")
        return
    
    tickets = get_user_tickets(username)
    
    ticket_items = []
    for ticket in tickets:
        try:
            seats = json.loads(ticket['Seats'])
        except (json.JSONDecodeError, TypeError):
            seats = [s.strip() for s in str(ticket['Seats']).split(',')]
            
        ticket_items.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.CONFIRMATION_NUMBER),
                                title=ft.Text(f"{ticket['EventName']}"),
                                subtitle=ft.Text(
                                    f"{ticket['Date']} at {ticket['StartTime']}\n"
                                    f"Venue: {ticket['VenueName']}\n"
                                    f"Seats: {', '.join(seats)}"
                                ),
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=10,
                ),
                margin=5,
            )
        )
    
    if not ticket_items:
        ticket_items.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.CONFIRMATION_NUMBER, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No tickets found", size=16, color=ft.Colors.GREY_600),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
                alignment=ft.alignment.center,
            )
        )
    ticket_list = ft.ListView(expand=True, spacing=10, padding=20)
    for ticket in tickets:
        ticket_control = ft.ListTile(
            title=ft.Text(f"{ticket['EventName']}"),
            subtitle=ft.Text(f"{ticket['Date'].strftime('%b %d, %Y')} • {ticket['StartTime']}"),
            trailing=ft.Text(f"#{ticket['TicketID']}", style=ft.TextThemeStyle.BODY_SMALL),
            on_click=lambda e, t=ticket: show_ticket_details(t),
        )
        ticket_list.controls.append(ticket_control)

    return ft.View(
        "/tickets",
        [
            ft.AppBar(
                title=ft.Text("My Tickets"), center_title=True, bgcolor="surface_variant",
                actions=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: page.go("/"), tooltip="Back to Home")]
            ),
            ft.Container(
                content=ft.Column([
                    ft.Divider(),
                    ft.Text(f"Showing {len(tickets)} ticket{'s' if len(tickets) != 1 else ''}", 
                           style=ft.TextThemeStyle.BODY_MEDIUM, color=ft.Colors.ON_SURFACE_VARIANT),
                    ticket_list if tickets else ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, size=48),
                            ft.Text("No tickets found", style=ft.TextThemeStyle.BODY_LARGE),
                            ft.Text("You haven't booked any tickets yet.", style=ft.TextThemeStyle.BODY_MEDIUM),
                            ft.ElevatedButton("Browse Events", on_click=lambda e: page.go("/"), icon=ft.Icons.EVENT_AVAILABLE)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                        alignment=ft.alignment.center, padding=40, expand=True,
                    )
                ], spacing=20, expand=True),
                padding=20, expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )

def main(page: ft.Page):
    page.title = "EventBite"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREY_50)
    
    
    
    def route_change(route):
        page.views.clear()
        if page.route == "/login":
            if page.client_storage.get("is_logged_in"):
                page.go("/")
                return
            page.views.append(create_auth_view(page, is_register=False))
        elif page.route == "/register":
            page.views.append(create_auth_view(page, is_register=True))
        elif page.route == "/":
            if not page.client_storage.get("is_logged_in"):
                page.go("/login")
                return
            page.views.append(create_homepage_view(page))
        elif page.route.startswith("/event/"):
            event_id = page.route.split("/")[-1]
            page.views.append(create_show_details_view(page, event_id))
        elif page.route.startswith("/event_single/"):
            event_id = page.route.split("/")[-1]
            page.views.append(create_show_details_view_single(page, event_id))
        elif page.route.startswith("/seating"):
            event_id = page.route.split("/")[-1]
            page.views.append(create_seating_view(page, event_id))
        elif page.route.startswith("/payment"):
            try:
                parts = page.route.split("/")
                event_id = parts[-2]
                encoded_labels = parts[-1]
                page.views.append(create_payment_view(page, event_id, encoded_labels))
            except Exception as ex:
                print(f"Error parsing payment route: {ex}")
        elif page.route == "/tickets":
            page.views.append(create_tickets_view(page))
                
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go('/login')

if __name__ == "__main__":
    ft.app(target=main, name="EventBite")