# Lost and Found System

A modern, web-based Lost and Found management system built with Python Flask. This application allows users to report lost items, report found items, and connect with others in their community to recover belongings.

## Features

###  Authentication System
- **User Registration**: Create a new account with username, email, and password
- **User Login**: Secure login with password hashing
- **User Logout**: Safe session termination
- **Session Management**: Persistent login sessions using Flask-Login

###  Item Management
- **Report Lost Items**: Users can report items they've lost with detailed information
- **Report Found Items**: Users can report items they've found
- **View All Items**: Browse all lost and found items in the system
- **Item Details**: View comprehensive details for each item
- **My Items**: Manage your own reported items
- **Status Updates**: Update item status (lost/found/closed/claimed)

###  Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Modern Styling**: Clean, professional interface with gradient accents
- **Intuitive Navigation**: Easy-to-use navigation bar and user-friendly forms
- **Flash Messages**: Clear feedback for user actions
- **Card-based Layout**: Organized display of items in an attractive grid

## Technology Stack

- **Backend**: Python 3.x
- **Web Framework**: Flask 3.0.0
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Security**: Werkzeug password hashing
- **Frontend**: HTML5, CSS3, Jinja2 Templates

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step 1: Clone or Download the Project
```bash
# Navigate to the project directory
cd "Lost and Found"
```

### Step 2: Create a Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

The application will start on `http://127.0.0.1:5000` (or `http://localhost:5000`)

## Project Structure

```
Lost and Found/
│
├── app.py                 # Main Flask application file
├── requirements.txt       # Python dependencies
├── README.md             # This documentation file
├── lost_and_found.db     # SQLite database (created automatically)
│
├── templates/            # Jinja2 HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── lost_items.html   # List of lost items
│   ├── found_items.html  # List of found items
│   ├── report_lost.html  # Form to report lost item
│   ├── report_found.html # Form to report found item
│   ├── item_detail.html  # Item detail view
│   └── my_items.html     # User's items management
│
└── static/               # Static files
    └── style.css         # CSS stylesheet
```

## Database Schema

### User Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password
- `created_at`: Account creation timestamp

### LostItem Table
- `id`: Primary key
- `title`: Item title
- `description`: Detailed description
- `location`: Location where item was lost
- `date_lost`: Date when item was lost
- `contact_info`: Contact information
- `status`: Item status (lost/found/closed)
- `created_at`: Report creation timestamp
- `user_id`: Foreign key to User table

### FoundItem Table
- `id`: Primary key
- `title`: Item title
- `description`: Detailed description
- `location`: Location where item was found
- `date_found`: Date when item was found
- `contact_info`: Contact information
- `status`: Item status (found/claimed/closed)
- `created_at`: Report creation timestamp
- `user_id`: Foreign key to User table

## Usage Guide

### For New Users

1. **Register an Account**
   - Click "Register" in the navigation bar
   - Fill in username, email, and password
   - Confirm your password
   - Click "Register"

2. **Login**
   - Click "Login" in the navigation bar
   - Enter your username and password
   - Click "Login"

### Reporting Items

#### Report a Lost Item
1. Login to your account
2. Click "Report Lost" in the navigation bar
3. Fill in the form:
   - **Item Title**: Brief description (e.g., "Lost iPhone 12")
   - **Description**: Detailed information about the item
   - **Location**: Where you lost the item
   - **Date Lost**: When you lost it
   - **Contact Information**: How people can reach you
4. Click "Submit Report"

#### Report a Found Item
1. Login to your account
2. Click "Report Found" in the navigation bar
3. Fill in the form with similar details
4. Click "Submit Report"

### Managing Your Items

1. Click "My Items" in the navigation bar
2. View all your reported lost and found items
3. Update item status:
   - **Lost Items**: Mark as "Found" or "Close"
   - **Found Items**: Mark as "Claimed" or "Close"

### Browsing Items

- **Lost Items**: Click "Lost Items" to see all reported lost items
- **Found Items**: Click "Found Items" to see all reported found items
- **Item Details**: Click "View Details" on any item card to see full information

## Security Features

- **Password Hashing**: All passwords are hashed using Werkzeug's security functions
- **Session Management**: Secure session handling with Flask-Login
- **User Authentication**: Protected routes require login
- **Input Validation**: Form validation on both client and server side

## Configuration

### Changing the Secret Key
For production use, change the secret key in `app.py`:

```python
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
```

Generate a secure secret key:
```python
import secrets
print(secrets.token_hex(32))
```

### Database Configuration
The application uses SQLite by default. To use a different database, modify the `SQLALCHEMY_DATABASE_URI` in `app.py`:

```python
# PostgreSQL example
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/dbname'

# MySQL example
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:password@localhost/dbname'
```

## Development

### Running in Debug Mode
The application runs in debug mode by default. For production, set `debug=False`:

```python
if __name__ == '__main__':
    app.run(debug=False)
```

### Database Initialization
The database is automatically created when you first run the application. To reset the database:

1. Delete `lost_and_found.db`
2. Restart the application

## API Routes

| Route | Method | Description | Auth Required |
|-------|--------|-------------|---------------|
| `/` | GET | Home page | No |
| `/register` | GET, POST | User registration | No |
| `/login` | GET, POST | User login | No |
| `/logout` | GET | User logout | Yes |
| `/lost-items` | GET | List all lost items | No |
| `/found-items` | GET | List all found items | No |
| `/report-lost` | GET, POST | Report lost item | Yes |
| `/report-found` | GET, POST | Report found item | Yes |
| `/lost-item/<id>` | GET | View lost item details | No |
| `/found-item/<id>` | GET | View found item details | No |
| `/my-items` | GET | View user's items | Yes |
| `/update-status/<type>/<id>/<status>` | GET | Update item status | Yes |

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Verify you're using the correct Python environment

2. **Database Errors**
   - Delete `lost_and_found.db` and restart the application
   - Ensure you have write permissions in the project directory

3. **Port Already in Use**
   - Change the port in `app.py`: `app.run(debug=True, port=5001)`

4. **CSS Not Loading**
   - Ensure the `static` folder exists and contains `style.css`
   - Clear browser cache

## Future Enhancements

Potential features for future versions:
- Image uploads for items
- Email notifications
- Search and filter functionality
- Category/tag system
- Admin panel
- Item matching algorithm
- Comments/messaging system
- Map integration for locations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue in the project repository.

## Author

Lost and Found System - Built with Flask

---

**Note**: This is a development version. For production deployment, ensure you:
- Change the secret key
- Use a production-grade database (PostgreSQL, MySQL)
- Set `debug=False`
- Use a production WSGI server (Gunicorn, uWSGI)
- Configure proper security headers
- Set up HTTPS/SSL

