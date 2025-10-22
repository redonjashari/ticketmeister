# 🎫 Ticketmeister - Concert Ticketing System

A modern, full-featured concert ticketing platform built with Flask and MariaDB.

## ✨ Features

### For Customers
- 🔐 **Secure Authentication** - Register, login, and password reset
- 🎵 **Browse Events** - Database-driven event listings with genres
- 🔍 **Smart Search** - Real-time search (activates after 2 letters)
- 🎟️ **Buy Tickets** - Select and purchase tickets with secure checkout
- 👤 **User Profile** - View and edit profile, check purchase history
- 🎭 **Genre Filtering** - Find concerts by music genre

### For Administrators
- 🛠️ **Admin Panel** - Protected maintenance page
- ➕ **CRUD Operations** - Manage events, venues, tickets, and more
- 👥 **User Management** - Full control over all system entities
- 📊 **Data Management** - Create and link events to venues

### Security
- 🔒 **Password Hashing** - Bcrypt encryption
- 🛡️ **SQL Injection Protection** - Parameterized queries
- 🔑 **Role-Based Access** - Admin and user roles
- 🚪 **Protected Routes** - Login and admin decorators

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   cd /home/rjashari/ticketmeister
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Database**
   
   Update `.env` with your credentials:
   ```env
   DB_HOST=localhost
   DB_USER=your_username
   DB_PASS=your_password
   DB_NAME=ticketmeister
   DB_PORT=3306
   SECRET_KEY=your-secret-key
   ```

3. **Set Up Database**
   ```bash
   mysql -u your_user -p ticketmeister < database.sql
   mysql -u your_user -p ticketmeister < users_schema.sql
   mysql -u your_user -p ticketmeister < sample_data.sql
   ```

4. **Create Admin User**
   ```bash
   python create_admin.py
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Site**
   - Home: http://localhost:5000/
   - Login: http://localhost:5000/login
   - Register: http://localhost:5000/register

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Complete setup guide
- **[FEATURES_CHECKLIST.md](FEATURES_CHECKLIST.md)** - All implemented features
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical details

## 🛠️ Tech Stack

- **Backend**: Flask 3.0.0, Python 3.12
- **Database**: MariaDB/MySQL
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Frontend**: HTML5, CSS3, JavaScript

## 📁 Project Structure

```
ticketmeister/
├── app.py                      # Main Flask application
├── db_connection.py            # Database connection
├── create_admin.py             # Admin user creation script
├── requirements.txt            # Python dependencies
├── database.sql                # Main database schema
├── users_schema.sql            # User authentication schema
├── sample_data.sql             # Sample data
├── static/
│   ├── style.css               # Main styles
│   └── img/                    # Images
└── templates/
    ├── index.html              # Home page
    ├── login.html              # Login page
    ├── register.html           # Registration
    ├── profile.html            # User profile
    ├── event_details.html      # Event details
    ├── checkout.html           # Checkout page
    ├── maintenance.html        # Admin panel
    └── [other templates]
```

## 🔐 Default Admin Credentials

If you use the pre-hashed password in setup:
- Username: `admin`
- Password: `admin123`

**⚠️ Change immediately after first login!**

## 🎯 Key Features Implemented

✅ User registration and authentication  
✅ Secure login with password hashing  
✅ Forgot password functionality  
✅ User profile management  
✅ Database-driven event listing  
✅ Real-time search (2+ letters)  
✅ Functional ticket selector  
✅ Payment and checkout flow  
✅ Event details page  
✅ Genre filtering  
✅ Admin-only maintenance page  
✅ Full CRUD operations  
✅ SQL injection protection  
✅ Responsive design  

## 📝 License

This is a student project for educational purposes.

## 🙏 Credits

Built with Flask, MariaDB, and modern web technologies.

---

For detailed setup instructions, see [SETUP.md](SETUP.md)
