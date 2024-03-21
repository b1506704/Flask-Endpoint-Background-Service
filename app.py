from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

user_sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('ping')
def handle_ping():
    emit('pong', True)

@socketio.on('join-session')
def handle_join_session(user_id):
    if user_id in user_sessions:
        emit('join-session-response', f'User ID {user_id} already in a session')
    else:
        session_id = str(uuid.uuid4())
        user_sessions[user_id] = False
        emit('join-session-response', f'User ID {user_id} joined session {session_id} successfully')

@socketio.on('start-assistant')
def handle_start_assistant(user_id):
    if user_id not in user_sessions:
        emit('start-assistant-response', f'User ID {user_id} not found')
    else:
        user_sessions[user_id] = True
        emit('start-assistant-response', f'Start assistant for {user_id} of session successfully')

@socketio.on('stop-assistant')
def handle_stop_assistant(user_id):
    if user_id not in user_sessions:
        emit('stop-assistant-response', f'User ID {user_id} not found')
    else:
        user_sessions[user_id] = False
        emit('stop-assistant-response', f'Stop assistant for {user_id} of session successfully')

@socketio.on('leave-session')
def handle_leave_session(user_id):
    if user_id not in user_sessions:
        emit('leave-session-response', f'User ID {user_id} not found')
    else:
        del user_sessions[user_id]
        emit('leave-session-response', f'Remove {user_id} of session successfully')

if __name__ == '__main__':
    import uuid
    socketio.run(app, debug=True)