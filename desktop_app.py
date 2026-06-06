import os
import sys
import threading
import time
import webview
import logging

from dotenv import load_dotenv

# We need to set the environment paths BEFORE importing the app
if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
    
    # Load .env from the bundled PyInstaller temp folder
    env_path = os.path.join(base_path, '.env')
    load_dotenv(env_path)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    load_dotenv()

# Now we can import the app
from app import app

# Disable Flask logging to console to keep it clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def start_server():
    # Run the Flask app on localhost
    app.run(host='127.0.0.1', port=5000, threaded=True, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start the Flask server in a daemon thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server a moment to start
    time.sleep(1)
    
    # Create the PyWebView Window (Full Screen as requested)
    webview.create_window(
        title='T&S PowerTech - ERP System', 
        url='http://127.0.0.1:5000',
        fullscreen=True
    )
    
    # Start the webview application
    webview.start()
