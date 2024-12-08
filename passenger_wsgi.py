import sys, os
import logging
from datetime import datetime

# Configure logging with more detailed information
logging.basicConfig(
    filename='/home/gdcdksdd/cms/error.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s\nPath: %(pathname)s:%(lineno)d\nFunction: %(funcName)s\n'
)

try:
    logging.info('Starting application initialization...')
    
    # Add your application directory to Python path
    INTERP = os.path.expanduser("/home/gdcdksdd/virtualenv/cms/3.11/bin/python")
    if sys.executable != INTERP:
        logging.info(f'Switching Python interpreter to {INTERP}')
        os.execl(INTERP, INTERP, *sys.argv)

    # Set up paths
    cwd = os.path.dirname(os.path.abspath(__file__))
    logging.info(f'Current working directory: {cwd}')
    sys.path.insert(0, cwd)

    # Import your Flask app
    logging.info('Importing create_app...')
    from app import create_app
    
    # Create the application instance
    logging.info('Creating application instance...')
    application = create_app()
    
    # Add error handlers
    @application.errorhandler(500)
    def internal_error(error):
        logging.error(f'500 error occurred: {error}', exc_info=True)
        return 'Internal Server Error', 500

    @application.errorhandler(Exception)
    def unhandled_exception(e):
        logging.error(f'Unhandled exception: {str(e)}', exc_info=True)
        return 'Internal Server Error', 500
        
    logging.info('Application initialization completed successfully')

except Exception as e:
    logging.error(f'Error during initialization: {str(e)}', exc_info=True)
    raise

# For debugging
application.debug = True
