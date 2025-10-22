# Ticketmeister Setup Guide

This guide will help you set up and run the Ticketmeister concert ticketing system.

## Prerequisites

- Python 3.8 or higher
- MariaDB/MySQL database server
- pip (Python package manager)

## Installation Steps

### 1. Clone the Repository

```bash
cd /home/rjashari/ticketmeister
```

### 2. Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

#### Create Database

Login to your MariaDB/MySQL server and create a database:

```sql
CREATE DATABASE ticketmeister CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### Update .env File

Create or update the `.env` file in the project root with your database credentials:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=your_database_username
DB_PASS=your_database_password
DB_NAME=ticketmeister
DB_PORT=3306

# Application Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development
```

**Important:** Change the `SECRET_KEY` to a random string in production!

### 5. Set Up Database Schema

Run the following SQL files in order:

```bash
# 1. Create the main schema
mysql -u your_username -p ticketmeister < database.sql

# 2. Create the users table for authentication
mysql -u your_username -p ticketmeister < users_schema.sql

# 3. (Optional) Load sample data
mysql -u your_username -p ticketmeister < sample_data.sql
```

OR using MySQL command line:

```bash
mysql -u your_username -p
```

Then in MySQL:

```sql
USE ticketmeister;
SOURCE /home/rjashari/ticketmeister/database.sql;
SOURCE /home/rjashari/ticketmeister/users_schema.sql;
SOURCE /home/rjashari/ticketmeister/sample_data.sql;
```

### 6. Create an Admin User

After setting up the database, you'll need to create an admin user. You can do this by:

1. Register a normal user through the web interface at `/register`
2. Then manually update the database to make them an admin:

```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

OR create a user directly in MySQL:

```sql
-- First create a person
INSERT INTO persons (first_name, last_name, email, phone)
VALUES ('Admin', 'User', 'admin@ticketmeister.com', '+1234567890');

-- Get the person_id (will be shown in the output)
SET @person_id = LAST_INSERT_ID();

-- Create customer record
INSERT INTO customers (person_id, loyalty_points)
VALUES (@person_id, 0);

-- Create admin user (password is 'admin123')
INSERT INTO users (person_id, username, password_hash, is_admin)
VALUES (@person_id, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIwnoSy6.K', 1);
```

Default credentials:
- Username: `admin`
- Password: `admin123`

**Important:** Change this password immediately after first login!

### 7. Run the Application

```bash
# Make sure your virtual environment is activated
python app.py
```

The application will start on `http://127.0.0.1:5000/`

## Features Implemented

### ✅ User Features
- **User Registration & Login** - Secure authentication with password hashing
- **Profile Management** - View and edit personal information
- **Purchase History** - View all past ticket purchases
- **Forgot Password** - Password reset functionality with tokens
- **Search Events** - Real-time search (activates after 2 letters)
- **Browse by Genre** - Filter concerts by music genre
- **Event Details** - Detailed information about each event
- **Ticket Selection** - Select and purchase tickets
- **Checkout** - Complete purchase with payment method selection

### ✅ Admin Features
- **Admin-Only Maintenance Page** - Protected by admin role
- **CRUD Operations** for:
  - Persons
  - Venues
  - Events (with genre support)
  - Tickets
  - Purchases
  - Payments
  - Event Organizers
  - Purchase Items
  - Event-Venue Links

### ✅ Security Features
- **Password Hashing** - Using Flask-Bcrypt
- **SQL Injection Protection** - Parameterized queries with PyMySQL
- **Session Management** - Secure Flask sessions
- **Admin Role Verification** - Route protection decorators
- **CSRF Protection** - Built into Flask

### ✅ UI/UX Features
- **Clickable Logo** - Returns to home page
- **Database-Driven** - All events loaded from database
- **Responsive Design** - Works on mobile and desktop
- **Flash Messages** - User feedback for all actions
- **Modern UI** - Netflix-inspired dark theme

## Application Structure

```
ticketmeister/
├── app.py                 # Main Flask application
├── db_connection.py       # Database connection handler
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── database.sql          # Main database schema
├── users_schema.sql      # User authentication schema
├── sample_data.sql       # Sample data for testing
├── static/
│   ├── style.css         # Main stylesheet
│   ├── design.css        # Maintenance page styles
│   └── img/              # Images
└── templates/
    ├── base.html              # Base template for maintenance
    ├── index.html             # Home page
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── profile.html           # User profile
    ├── edit_profile.html      # Edit profile
    ├── forgot_password.html   # Forgot password
    ├── reset_password.html    # Reset password
    ├── event_details.html     # Event details
    ├── checkout.html          # Checkout page
    ├── genre_events.html      # Genre listing
    ├── maintenance.html       # Admin maintenance
    ├── imprint.html           # Imprint page
    └── [other admin forms]    # CRUD forms
```

## Usage

### For Regular Users:

1. **Register**: Go to `/register` and create an account
2. **Browse Events**: View upcoming concerts on the home page
3. **Search**: Click the search icon (🔍) and type to search events
4. **View Event**: Click on any event card to see details
5. **Buy Tickets**: Select tickets and proceed to checkout
6. **View Profile**: See your purchases and edit your information

### For Admin Users:

1. **Login**: Use admin credentials
2. **Access Maintenance**: Click "Maintenance" in the navigation
3. **Manage Data**: Use the admin panel to create/manage:
   - Events
   - Venues
   - Tickets
   - Customers
   - And more...

## Troubleshooting

### Database Connection Issues

If you get database connection errors:

1. Check your `.env` file has correct credentials
2. Make sure MariaDB/MySQL is running:
   ```bash
   sudo systemctl status mysql  # On Linux
   ```
3. Verify the database exists:
   ```sql
   SHOW DATABASES;
   ```

### Import Errors

If you get module import errors:

1. Make sure virtual environment is activated
2. Reinstall requirements:
   ```bash
   pip install -r requirements.txt
   ```

### Template Not Found

If you get template errors:

1. Make sure all templates are in the `templates/` folder
2. Check file names match exactly (case-sensitive)

## Development

### Adding New Features

1. Update `app.py` with new routes
2. Create corresponding templates in `templates/`
3. Update `style.css` for styling
4. Test with sample data

### Database Changes

1. Update `database.sql` for schema changes
2. Create migration SQL if needed
3. Test with sample data

## Security Notes

- Change default admin password
- Use strong `SECRET_KEY` in production
- Use HTTPS in production
- Regularly update dependencies
- Don't commit `.env` file to git

## Support

For issues or questions:
1. Check this documentation
2. Review the code comments
3. Check Flask documentation: https://flask.palletsprojects.com/

## License

This is a student project for educational purposes.

