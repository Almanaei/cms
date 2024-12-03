# CMS Application Version Reference

## Application Overview
A Flask-based Content Management System with comprehensive features for content creation, user management, and media handling.

## Current Version Information
- Commit: `f96ea28046b4fe54a09c0c881b5b124f64bf03e9`
- Description: Enhanced analytics dashboard and fixed settings management
- Author: Almanaei (almannaei90@gmail.com)

## Core Features in This Version

### Analytics Dashboard
- Enhanced dashboard functionality
- Improved data visualization
- Real-time user activity tracking

### Settings Management
- Updated context processor for Settings.get
- Streamlined configuration handling
- Improved settings interface

### Navigation
- Fixed sidebar navigation
- Enhanced template inheritance
- Improved UI/UX

### Backup System
- Automated backup functionality
- User activity tracking integration
- Robust data preservation

## Core Components

### Authentication & Authorization
- User authentication via Flask-Login
- Role-based access control system
- Support for OAuth authentication
- Session management and security features

### Content Management
- Post management with categories and tags
- Media management with S3 integration
- Comment system with moderation
- SEO optimization features
- Content versioning

### Database Schema
- Users and Roles
- Posts, Categories, and Tags
- Comments and Likes
- Media Items
- Page Views and Analytics
- System Settings and Backups

### Key Features
- Automated backup system
- User activity tracking
- Media management with S3
- Multi-language support
- Rate limiting
- Caching system
- Background task processing with Celery
- Email notifications
- Social media integration

## Technical Stack

### Core Dependencies
```
Flask==2.3.3
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.2
Flask-WTF==1.1.1
Werkzeug==2.3.7
```

### Database & Migration
```
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
```

### Caching & Task Queue
```
Flask-Caching==2.0.2
redis==5.0.0
celery==5.3.1
```

### Security
```
Flask-WTF==1.1.1
Flask-SeaSurf==1.1.1
Flask-Talisman==1.0.0
PyJWT==2.8.0
```

### Media & File Handling
```
Pillow==10.0.0
python-magic==0.4.27
python-magic-bin==0.4.14
boto3==1.28.25
```

### Additional Features
```
Flask-Babel==3.1.0
Flask-Mail==0.9.1
Flask-Limiter==3.3.1
elasticsearch==7.17.9
```

## Directory Structure
```
cms/
├── app/
│   ├── admin/
│   ├── api/
│   ├── auth/
│   ├── main/
│   ├── models/
│   ├── static/
│   ├── templates/
│   └── utils/
├── migrations/
├── backups/
├── config.py
├── requirements.txt
└── run.py
```

## Key Models
- User
- Role
- Post
- Category
- Tag
- Comment
- Media
- PageView
- Settings
- BackupSchedule

## Configuration
- Environment-based configuration
- Support for .env files
- Configurable backup schedules
- Email settings
- AWS S3 integration
- Redis configuration
- Security settings

## Security Features
- CSRF protection
  - Global CSRF token via meta tag
  - Automatic CSRF token injection in forms
  - AJAX request header integration
- Rate limiting
- Secure session handling
- Password hashing
- Role-based access control
- API authentication

### CSRF Protection Implementation
```html
<!-- Meta tag in base template -->
<meta name="csrf-token" content="{{ csrf_token() }}">

<!-- Automatic CSRF token injection -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // Add CSRF token to forms
        document.querySelectorAll('form').forEach(form => {
            if (!form.querySelector('input[name="csrf_token"]')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrf_token';
                input.value = csrfToken;
                form.appendChild(input);
            }
        });

        // Add CSRF token to AJAX requests
        const originalFetch = window.fetch;
        window.fetch = function() {
            let [resource, config] = arguments;
            config = config || {};
            config.headers = config.headers || {};
            if (!(config.headers instanceof Headers)) {
                config.headers = new Headers(config.headers);
            }
            config.headers.set('X-CSRFToken', csrfToken);
            return originalFetch(resource, config);
        };
    });
</script>
```

This implementation ensures:
1. Automatic CSRF token inclusion in all forms
2. CSRF token headers in all AJAX requests
3. Consistent token availability across the application
4. Protection against cross-site request forgery attacks

## Current Status
This version represents a fully functional CMS with comprehensive features for content management, user handling, and system administration. It includes robust security measures, performance optimizations, and extensive customization options through the settings system.

---
*This reference document was automatically generated to capture the current state of the CMS application.*
