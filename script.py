from flask import Flask, request, render_template_string, jsonify
import threading
import os
import requests
import time
import http.server
import socketserver

app = Flask(__name__)

# Global flag to control message sending
stop_flag = False

# HTML Form
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Sender</title>
    <style>
        body {
            background-color: #222;
            color: white;
            font-family: Arial, sans-serif;
            text-align: center;
        }
        .container {
            margin: 50px auto;
            max-width: 500px;
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            border-radius: 10px;
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
        }
        button {
            background-color: green;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: red;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Start Messaging</h2>
        <form id="messageForm">
            <input type="text" id="convoId" name="convoId" placeholder="Conversation ID" required><br>
            <input type="text" id="hatersName" name="hatersName" placeholder="Custom Name" required><br>
            <input type="number" id="speed" name="speed" placeholder="Delay (seconds)" value="1" required><br>
            <button type="submit">Start Sending</button>
        </form>
        <button onclick="stopMessaging()">Stop Messaging</button>
    </div>

    <script>
        document.getElementById('messageForm').addEventListener('submit', function(event) {
            event.preventDefault();
            fetch('/start', {
                method: 'POST',
                body: new FormData(this)
            }).then(response => response.json())
              .then(result => alert(result.message))
              .catch(error => console.error('Error:', error));
        });

        function stopMessaging() {
            fetch('/stop', { method: 'POST' })
                .then(response => response.json())
                .then(result => alert(result.message))
                .catch(error => console.error('Error:', error));
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start_messaging():
    global stop_flag
    stop_flag = False  # Reset stop flag when starting

    convo_id = request.form.get('convoId')
    haters_name = request.form.get('hatersName')
    speed = int(request.form.get('speed'))

    tokens = ["YOUR_ACCESS_TOKEN_HERE"]  # Replace with valid tokens
    messages = ["Hello!", "This is an automated message.", "Have a nice day!"]  # Example messages

    def send_messages():
        global stop_flag
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        while not stop_flag:
            try:
                for message in messages:
                    if stop_flag:
                        print("[!] Stopping message sending...")
                        return

                    access_token = tokens[0]  # Use a single token for simplicity
                    url = f"https://graph.facebook.com/v17.0/t_{convo_id}"
                    full_message = f"{haters_name}: {message}"
                    parameters = {"access_token": access_token, "message": full_message}
                    response = requests.post(url, json=parameters, headers=headers)

                    print(f"Sent: {full_message} | Response: {response.text}")
                    time.sleep(speed)
            except Exception as e:
                print(f"[!] Error: {e}")

    # Start messaging in a separate thread
    threading.Thread(target=send_messages).start()

    return jsonify({"message": "Messaging started successfully!"})

@app.route('/stop', methods=['POST'])
def stop_messaging():
    global stop_flag
    stop_flag = True
    return jsonify({"message": "Message sending has been stopped."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
