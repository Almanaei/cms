# CMS Development Guide

This guide explains how to set up and maintain both local development and production environments for the CMS.

## Database Architecture

### Development vs Production Database
Our application uses different database systems for development and production:

#### Production Environment (cPanel)
- Database: MySQL
- Driver: PyMySQL
- Connection string format:
  ```
  SQLALCHEMY_DATABASE_URI=mysql+pymysql://username:password@localhost/database
  ```

#### Development Environment (Local)
- Database: PostgreSQL
- Driver: psycopg2-binary
- Connection string format:
  ```
  SQLALCHEMY_DATABASE_URI=postgresql://postgres:your_password@localhost/cms_local
  ```

### Why Different Databases?
1. **Environment Separation**
   - Keeps development work isolated from production data
   - Allows for safe testing of database changes
   - Prevents accidental modification of production data

2. **SQLAlchemy Abstraction**
   - Our ORM (SQLAlchemy) handles database differences
   - Same Python code works with both databases
   - No need to modify application code between environments

3. **Development Benefits**
   - PostgreSQL offers better development tools
   - Stronger data integrity checks during development
   - Easier local setup and maintenance

### Best Practices
1. **Testing Database Changes**
   - Test all database migrations on both PostgreSQL and MySQL
   - Be aware of syntax differences between databases
   - Document any database-specific behaviors

2. **Schema Changes**
   - Always test schema changes in development first
   - Verify migrations work on both database systems
   - Keep track of any database-specific SQL commands

## Local Development Setup

### 1. Environment Setup
1. Install Python 3.11 and PostgreSQL locally
2. Create a local database named 'cms_local'
3. Configure `.env.development` with your local settings:
   - Update database credentials
   - Modify secret key and other settings as needed

### 2. Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize local database
python setup_local.py

# Run the application
python run_local.py
```

The application will be available at `http://localhost:5000`

### 3. Development Workflow
1. Make code changes locally
2. Test changes at `http://localhost:5000`
3. If tests pass:
   ```bash
   # Commit changes
   git add .
   git commit -m "Description of changes"
   
   # Push to repository
   git push
   ```
4. Deploy to production:
   - Go to cPanel's Git Version Control
   - Click "Update from Remote"
   - Restart the Python application

### 4. Branch Management
```bash
# Create new feature branch
git checkout -b feature-name

# Switch between branches
git checkout main
git checkout feature-name

# Merge feature into main
git checkout main
git merge feature-name
```

## Production Environment (cPanel)

### 1. Deployment Files
- `passenger_wsgi.py`: Entry point for production
- `.env.production`: Production environment variables
- `requirements.cpanel.txt`: Production dependencies

### 2. Deployment Process
1. Push changes to Git repository
2. In cPanel:
   - Go to Git Version Control
   - Click "Update from Remote"
   - Go to Python App interface
   - Click "Restart" if needed

### 3. Database Management
- Always backup production database before major changes
- Use init_db.py for database initialization
- Keep production database credentials secure

## Important Notes

### Security
- Never commit `.env` files to Git
- Change default admin passwords immediately
- Keep production credentials secure
- Regularly update dependencies

### Best Practices
- Always test changes locally first
- Use meaningful commit messages
- Keep separate branches for features
- Document significant changes
- Monitor application logs

### File Structure
```
cms/
├── .env.development     # Local environment variables
├── .env.production      # Production environment variables
├── requirements.txt     # Local development dependencies
├── requirements.cpanel.txt  # Production dependencies
├── setup_local.py      # Local database setup
├── run_local.py        # Local development server
├── init_db.py          # Database initialization
└── passenger_wsgi.py   # Production entry point
```

## Troubleshooting

### Common Issues
1. Database Connection:
   - Verify credentials in .env files
   - Check database service is running
   - Ensure database exists

2. Dependencies:
   - Update requirements.txt for local changes
   - Update requirements.cpanel.txt for production
   - Use compatible package versions

3. File Permissions:
   - Check upload directory permissions
   - Verify file ownership in cPanel

### Getting Help
- Check application logs in cPanel
- Review Git commit history
- Consult Flask documentation
- Check database logs for issues
