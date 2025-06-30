# EventBite - Event Management System

EventBite is a comprehensive event management system that allows users to create, manage, and book events. The project comes in two versions:

1. **Single Application Version** (`/EventBite` folder): A standalone application that combines both server and client functionality in one package.
2. **Client-Server Version** (`/EventBite_Final` folder): A distributed system with separate server and client applications that can run on different devices within the same local network.

## Features

- User authentication (login/registration)
- Event creation and management
- Event browsing and search
- Seat selection and booking
- Real-time event updates
- Cross-platform compatibility (PC and mobile)

## Prerequisites

- Python 3.7+
- MySQL Server
- Required Python packages (install using `pip install -r requirements.txt`)

## Single Application Version

### Setup

1. Navigate to the `EventBite` directory
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Configure your MySQL database settings in `config.py`
4. Run the application:
   ```
   python main.py
   ```

## Client-Server Version

### Server Setup

1. Navigate to the `EventBite_Final/server` directory
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Configure your MySQL database settings in the server configuration
4. Start the server:
   ```
   python server.py
   ```
   The server will run on `http://[your-local-ip]:5000`

### Client Setup

1. Navigate to the `EventBite_Final/client` directory
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the client application:
   ```
   python main.py
   ```
4. When prompted, enter the server's IP address and port (e.g., `http://192.168.1.100:5000`)

## Database Setup

1. Create a new MySQL database
2. Import the database schema from `database/schema.sql`
3. Update the database connection settings in the respective configuration files

## Project Structure

### Single Application Version
```
EventBite/
├── main.py              # Main application with user interface and core functionality
├── event_manager.py     # Handles database operations for events and venues
└── ...
```

### Client-Server Version
```
EventBite_Final/
├── client/              # Client application
│   ├── main.py          # Client application entry point
│   ├── assets/          # Static assets (images, styles)
│   └── ...
├── server/              # Server application
│   ├── server.py        # Server implementation
│   ├── database.py      # Database operations
│   └── ...
└── storage/             # File storage
```

## Usage

1. **Single Application Version**:
   - Launch the application
   - Log in or register a new account
   - Browse or create events
   - Book seats for events

2. **Client-Server Version**:
   - Start the server on a host machine
   - Run the client on any device in the same network
   - Connect to the server using the server's local IP address
   - Multiple clients can connect to the same server simultaneously

## Requirements

- MySQL Server 5.7+
- Python 3.7+
- Required Python packages:
  - Flask (for server)
  - mysql-connector-python
  - PyQt5 (for GUI)
  - Requests (for client)

## Troubleshooting

- Ensure MySQL server is running
- Verify database credentials in configuration
- Check that the server and client are on the same network
- Ensure no firewall is blocking the connection (default port: 5000)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
