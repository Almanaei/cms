import sys, os
import logging

# Configure logging
logging.basicConfig(
    filename='/home/gdcdksdd/cms/error.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

try:
    # Add your application directory to Python path
    INTERP = os.path.expanduser("/home/gdcdksdd/virtualenv/cms/3.11/bin/python")
    if sys.executable != INTERP:
        os.execl(INTERP, INTERP, *sys.argv)

    # Set up paths
    sys.path.insert(0, '/home/gdcdksdd/cms')

    # Import your Flask app and config
    from app import create_app
    from config import Config

    # Create the application instance
    application = create_app(Config)

except Exception as e:
    logging.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
