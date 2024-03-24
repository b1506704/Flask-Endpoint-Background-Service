import queue
import subprocess
import time
from flask import Flask
from flask_socketio import SocketIO, emit
import uuid
from assistant import start_transcribing

app = Flask(__name__)
socketio = SocketIO(app)

try:
    subprocess.run(["ffmpeg", "-version"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")

user_sessions = {}
transcript_queue = queue.Queue()
suggestion_queue = queue.Queue()


@socketio.on('ping')
def handle_ping():
    emit('pong', True)


@socketio.on('join-session')
def handle_join_session(user_id):
    if user_id in user_sessions:
        message = f'User ID {user_id} already in a session'
        emit('join-session-response', message)
        app.logger.info(message)

    else:
        session_id = str(uuid.uuid4())
        user_sessions[user_id] = False
        message = f'User ID {user_id} joined session {session_id} successfully'
        emit('join-session-response', message)
        app.logger.info(message)
        start_transcribing(transcript_queue, suggestion_queue)


@socketio.on('start-assistant')
def handle_start_assistant(user_id):
    if user_id not in user_sessions:
        message = f'User ID {user_id} not found'
        emit('start-assistant-response', message)
        app.logger.info(message)
    else:
        user_sessions[user_id] = True
        lastTranscriptionMessage = None
        lastSuggestionMessage = None

        while True:
            if transcript_queue.qsize() > 0:
                transcription_message = transcript_queue.get_nowait()

                if lastTranscriptionMessage != transcription_message:
                    emit('start-assistant-transcription-response',
                         transcription_message)
                    app.logger.info(transcription_message)
                    lastTranscriptionMessage = transcription_message

            if suggestion_queue.qsize() > 0:
                suggestion_message = suggestion_queue.get_nowait()

                if lastSuggestionMessage != suggestion_message:
                    emit('start-assistant-suggestion-response', suggestion_message)
                    app.logger.info(suggestion_message)
                    lastSuggestionMessage = suggestion_message

            time.sleep(0.05)


@socketio.on('stop-assistant')
def handle_stop_assistant(user_id):
    if user_id not in user_sessions:
        message = f'User ID {user_id} not found'
        emit('stop-assistant-response', message)
        app.logger.info(message)
    else:
        message = f'Stop assistant for {user_id} of session successfully'
        user_sessions[user_id] = False
        emit('stop-assistant-response', message)
        app.logger.info(message)
        suggestion_queue.queue.clear()
        transcript_queue.queue.clear()


@socketio.on('leave-session')
def handle_leave_session(user_id):
    if user_id not in user_sessions:
        message = f'User ID {user_id} not found'
        emit('leave-session-response', message)
        app.logger.info(message)
    else:
        message = f'Remove {user_id} of session successfully'
        del user_sessions[user_id]
        emit('leave-session-response', message)
        app.logger.info(message)
        suggestion_queue.queue.clear()
        transcript_queue.queue.clear()


if __name__ == '__main__':
    socketio.run(app, debug=True)
