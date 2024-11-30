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

## Common Issues and Solutions

### CSS Linter Errors with Jinja2 Template Variables

**Problem**: When using Jinja2 template variables within CSS styles, you might encounter CSS linter errors like:
```
at-rule or selector expectedcss(css-ruleorselectorexpected)
```

**Solution**: Instead of using template variables directly in CSS or inline styles, use a data attribute approach:

1. Store the dynamic value in a data attribute:
```html
<div class="progress-bar" 
     data-width="{{ value }}"
     role="progressbar">
</div>
```

2. Use JavaScript to apply the style after the page loads:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const element = document.querySelector('.progress-bar');
    const width = element.getAttribute('data-width');
    element.style.width = width + '%';
});
```

This approach:
- Avoids CSS syntax errors from template variables
- Maintains clean separation between HTML and CSS
- Works reliably across different browsers
- Keeps the code maintainable and linter-friendly
