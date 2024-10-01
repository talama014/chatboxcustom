from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import threading
import signal
import sys


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

edge_options = Options()
edge_options.add_argument("--headless")  # Run in headless mode
edge_options.add_argument("--disable-gpu")  # Disable GPU usage
edge_options.add_argument("--no-sandbox")  # Bypass OS security model (useful for headless)
edge_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems in containerized environments
driver_path = 'E:/Download/Nhac/msedgedriver.exe'

driver_youtube = webdriver.Edge(service=Service(driver_path), options=edge_options)
driver_youtube.get('https://studio.youtube.com/live_chat?is_popout=1&v=RBzScJ5ibVU')  # Replace with your URL

driver_nimo = webdriver.Edge(service=Service(driver_path), options=edge_options)
driver_nimo.get('https://www.nimo.tv/vidwalla/overlay?_roomId=67016536&_lang=1066&_type=chatbox')

# Flag to control the running state of the message fetching thread
fetching = True

# Function to fetch messages
def fetch_messages():
    global fetching
    previous_count_youtube = 0  # Initialize previous count
    previous_count_nimo = 0  # Initialize previous count

    while fetching:
        try:
            # Get the list of all messages
            messagesYoutube = WebDriverWait(driver_youtube, 1).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.style-scope yt-live-chat-text-message-renderer'))
            )

            messages_text_youtube = [message.text for message in messagesYoutube]
            current_count_youtube = len(messages_text_youtube)  # Count the current messages

            # If new messages are detected
            if current_count_youtube > previous_count_youtube:
                # Get the new messages
                new_messages_youtube = messages_text_youtube[previous_count_youtube:current_count_youtube]

                matches_youtube = [string for string in new_messages_youtube if "plaeri" in string]

                # Send new messages to the frontend via SocketIO
                if matches_youtube:
                    matches_youtube = [match.replace('\n', '(youtube):') for match in matches_youtube]
                    socketio.emit('update_messages', matches_youtube)

                # Update the previous count to the current count
                previous_count_youtube = current_count_youtube

            # Get the list of all messages
            messagesNimo = WebDriverWait(driver_nimo, 1).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.nimo-room__chatroom__message-item'))
            )

            messages_text_nimo = [message.text for message in messagesNimo]

            current_count_nimo = len(messages_text_nimo)  # Count the current messages

            # If new messages are detected
            if current_count_nimo > previous_count_nimo:
                # Get the new messages
                new_messages_nimo = messages_text_nimo[previous_count_nimo:current_count_nimo]

                matches_nimo = [string for string in new_messages_nimo if "plaeri" in string]

                # Send new messages to the frontend via SocketIO
                if matches_nimo:
                    matches_nimo = [match.replace(':', '(nimo):') for match in matches_nimo]
                    socketio.emit('update_messages', matches_nimo)

                # Update the previous count to the current count
                previous_count_nimo = current_count_nimo
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(5)  # Check for new messages every second

# Graceful shutdown on Ctrl + C
def signal_handler(sig, frame):
    global fetching
    print('Shutting down...')
    
    # Stop the message fetching thread
    fetching = False

    # Close the WebDriver
    driver_youtube.quit()

    # Exit the application
    sys.exit(0)

# Define route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Start fetching messages in a separate thread
def start_fetching():
    thread = threading.Thread(target=fetch_messages)
    thread.start()

if __name__ == '__main__':
    # Catch Ctrl + C signal
    signal.signal(signal.SIGINT, signal_handler)

    # Start message fetching
    start_fetching()

    # Run Flask-SocketIO app
    socketio.run(app, port=5000, debug=True)
