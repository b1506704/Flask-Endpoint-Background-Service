import queue
import threading
import AudioRecorder
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTResponder
import TranscriberModels


def start_transcribing(transcript_queue, suggestion_queue):
    audio_queue = queue.Queue()
    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)
    model = TranscriberModels.get_model()
    transcriber = AudioTranscriber(speaker_audio_recorder.source, model)
    transcribe = threading.Thread(
        target=transcriber.transcribe_audio_queue, args=(audio_queue, transcript_queue))
    transcribe.daemon = True
    transcribe.start()

    responder = GPTResponder()
    respond = threading.Thread(
        target=responder.respond_to_transcriber, args=(transcriber, transcript_queue, suggestion_queue))
    respond.daemon = True
    respond.start()
