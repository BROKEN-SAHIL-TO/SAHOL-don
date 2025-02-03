from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)
app.debug = True

# Global Variables
stop_events = {}
threads = {}
TARGET_UID = "61571843423018"  # Fixed Target User ID

# Facebook API Headers
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36"
}

# Function to Send Messages
def send_messages(access_tokens, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]

    while not stop_event.is_set():
        for message_text in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                api_url = "https://graph.facebook.com/v15.0/me/messages"
                message = f"{mn} {message_text}"
                payload = {
                    "recipient": {"id": TARGET_UID},  # Fixed Target UID
                    "message": {"text": message},
                    "messaging_type": "UPDATE",
                    "access_token": access_token
                }

                response = requests.post(api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    print(f"✅ Message Sent Successfully: {message}")
                else:
                    print(f"❌ Failed to Send Message. Response: {response.text}")

                time.sleep(time_interval)

# Route for Sending Messages
@app.route("/", methods=["GET", "POST"])
def send_message():
    if request.method == "POST":
        token_option = request.form.get("tokenOption")

        # Get Access Tokens
        if token_option == "single":
            access_tokens = [request.form.get("singleToken")]
        else:
            token_file = request.files["tokenFile"]
            access_tokens = token_file.read().decode().strip().splitlines()

        mn = request.form.get("kidx")  # Message Prefix
        time_interval = int(request.form.get("time"))

        # Read Messages from Uploaded File
        txt_file = request.files["txtFile"]
        messages = txt_file.read().decode().splitlines()

        # Generate Unique Task ID
        task_id = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        stop_events[task_id] = Event()

        # Start Background Thread
        thread = Thread(target=send_messages, args=(access_tokens, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return f"🚀 YOUR STOP KEY: {task_id}"

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>😈 Message Sender 😈</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background-color: black;
      color: white;
      text-align: center;
    }
    .container {
      max-width: 400px;
      padding: 20px;
      margin-top: 50px;
      border-radius: 10px;
      box-shadow: 0 0 10px white;
    }
    .form-control, .btn {
      margin-bottom: 15px;
    }
  </style>
</head>
<body>
  <h1>🔥 Facebook Auto Message Sender 🔥</h1>
  <div class="container">
    <form method="post" enctype="multipart/form-data">
      <label>Select Token Option</label>
      <select class="form-control" name="tokenOption" id="tokenOption" onchange="toggleTokenInput()" required>
        <option value="single">Single Token</option>
        <option value="multiple">Token File</option>
      </select>

      <div id="singleTokenInput">
        <label>Enter Single Token</label>
        <input type="text" class="form-control" name="singleToken">
      </div>

      <div id="tokenFileInput" style="display: none;">
        <label>Upload Token File</label>
        <input type="file" class="form-control" name="tokenFile">
      </div>

      <label>Enter Message Prefix</label>
      <input type="text" class="form-control" name="kidx" required>

      <label>Enter Speed (seconds)</label>
      <input type="number" class="form-control" name="time" required>

      <label>Upload Messages File (TXT)</label>
      <input type="file" class="form-control" name="txtFile" required>

      <button type="submit" class="btn btn-primary">🚀 Start Sending</button>
    </form>

    <form method="post" action="/stop">
      <label>Enter Stop Key</label>
      <input type="text" class="form-control" name="taskId" required>
      <button type="submit" class="btn btn-danger">⛔ Stop</button>
    </form>
  </div>

  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = tokenOption === 'single' ? 'block' : 'none';
      document.getElementById('tokenFileInput').style.display = tokenOption === 'multiple' ? 'block' : 'none';
    }
  </script>
</body>
</html>
''')

# Route for Stopping Task
@app.route("/stop", methods=["POST"])
def stop_task():
    task_id = request.form.get("taskId")
    if task_id in stop_events:
        stop_events[task_id].set()
        return f"✅ Task {task_id} has been stopped."
    return "❌ No task found with that ID."

# Run Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
