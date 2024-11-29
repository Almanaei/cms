# Content Management System (CMS)

A modern, Flask-based Content Management System with a clean and responsive user interface.

## Features

- User authentication (login/register)
- Admin dashboard
- Post management (create, edit, delete)
- Category management
- Rich text editor for post content
- Featured images for posts
- Responsive design
- SEO-friendly URLs

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the application:
```bash
python run.py
```

5. Access the application:
- Main site: http://localhost:5000
- Admin login: http://localhost:5000/auth/login
  - Default admin credentials:
    - Username: admin
    - Password: admin

## Project Structure

```
cms/
├── app/
│   ├── static/
│   │   └── css/
│   ├── templates/
│   │   ├── admin/
│   │   ├── auth/
│   │   └── main/
│   ├── admin/
│   ├── auth/
│   ├── main/
│   ├── models.py
│   └── __init__.py
├── config.py
├── requirements.txt
├── run.py
└── init_db.py
```

## Security Notes

1. Change the default admin password after first login
2. Update the SECRET_KEY in config.py for production
3. Configure proper database URL for production
4. Set up proper file upload restrictions and validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
