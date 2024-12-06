import logging
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    # Load local environment variables
    logger.info("Loading environment variables...")
    load_dotenv('.env.development')
    
    logger.info("Importing create_app...")
    from app import create_app
    
    logger.info("Creating app instance...")
    app = create_app()
    
    if __name__ == '__main__':
        logger.info("Starting development server...")
        app.run(host='0.0.0.0', port=5000, debug=True)

except Exception as e:
    logger.error(f"Error occurred: {str(e)}", exc_info=True)
    sys.exit(1)
