from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

stop_events = {}
threads = {}
TARGET_THREAD_ID = "61571843423018"
PASSWORD = "broken sahil"

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                parameters = {'access_token': access_token, 'message': message}
                
                response = requests.post(api_url, data=parameters, headers=headers)
                
                if response.status_code == 200:
                    print(f"Message Sent Successfully From token {access_token}: {message}")
                else:
                    print(f"Message Sending Failed From token {access_token}: {message}")
                
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        # Password check
        user_password = request.form.get('password')
        if user_password != PASSWORD:
            return "Access Denied: Incorrect Password."

        # Token Selection
        token_option = request.form.get('tokenOption')
        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        # Thread ID Validation
        thread_id = request.form.get('threadId')
        if thread_id != TARGET_THREAD_ID:
            return "Access Denied: Unauthorized Thread ID."

        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        stop_events[task_id] = Event()
        
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return f' YOUR STOP KEY-> {task_id}'

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>😈 𝙎𝘼𝙃𝙄𝙇 𝙄𝙉𝙎𝙄𝘿𝙀 😈</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background-color: black;
                color: white;
                text-align: center;
            }
            .container {
                margin-top: 50px;
                max-width: 400px;
                padding: 20px;
                background-color: #222;
                border-radius: 10px;
                box-shadow: 0 0 10px white;
            }
            .form-control {
                margin-bottom: 10px;
                background: transparent;
                color: white;
            }
            .btn {
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔒 Enter Password</h2>
            <form method="post" enctype="multipart/form-data">
                <input type="password" class="form-control" name="password" placeholder="Enter Password" required>
                
                <label>Select Token Option</label>
                <select class="form-control" name="tokenOption" required>
                    <option value="single">Single Token</option>
                    <option value="multiple">Token File</option>
                </select>
                
                <label>Enter Single Token</label>
                <input type="text" class="form-control" name="singleToken">
                
                <label>Choose Token File</label>
                <input type="file" class="form-control" name="tokenFile">
                
                <label>Thread ID</label>
                <input type="text" class="form-control" name="threadId" required>
                
                <label>Enter Name</label>
                <input type="text" class="form-control" name="kidx" required>
                
                <label>Enter Speed (Seconds)</label>
                <input type="number" class="form-control" name="time" required>
                
                <label>Upload Message File</label>
                <input type="file" class="form-control" name="txtFile" required>
                
                <button type="submit" class="btn btn-primary">Run Server</button>
            </form>
            
            <h3>❌ Stop Task</h3>
            <form method="post" action="/stop">
                <label>Enter Stop Key</label>
                <input type="text" class="form-control" name="taskId" required>
                <button type="submit" class="btn btn-danger">Stop Server</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task with ID {task_id} has been stopped.'
    else:
        return f'No task found with ID {task_id}.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
