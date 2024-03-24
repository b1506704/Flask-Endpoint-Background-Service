from queue import Queue
import wave
import os
import threading
import tempfile
from datetime import timedelta
import pyaudiowpatch as pyaudio

PHRASE_TIMEOUT = 3.05
MAX_PHRASES = 10


class AudioTranscriber:
    def __init__(self, speaker_source, model):
        self.transcript_data = {"Speaker": []}
        self.transcript_changed_event = threading.Event()
        self.audio_model = model

        self.audio_sources = {
            "Speaker": {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data
            }
        }

    def transcribe_audio_queue(self, audio_queue, transcript_queue):
        while True:
            who_spoke, data, time_spoken = audio_queue.get()
            self.update_last_sample_and_phrase_status(
                who_spoke, data, time_spoken)
            source_info = self.audio_sources[who_spoke]

            text = ''

            try:
                fd, path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                source_info["process_data_func"](
                    source_info["last_sample"], path)
                text = self.audio_model.get_transcription(path)
            except Exception as e:
                print(e)
            finally:
                os.unlink(path)

            if text != '' and text.lower() != 'you':
                self.update_transcript(
                    who_spoke, text, time_spoken, transcript_queue)
                self.transcript_changed_event.set()

    def update_last_sample_and_phrase_status(self, who_spoke, data, time_spoken):
        source_info = self.audio_sources[who_spoke]
        if source_info["last_spoken"] and time_spoken - source_info["last_spoken"] > timedelta(seconds=PHRASE_TIMEOUT):
            source_info["last_sample"] = bytes()
            source_info["new_phrase"] = True
        else:
            source_info["new_phrase"] = False

        source_info["last_sample"] += data
        source_info["last_spoken"] = time_spoken

    def process_speaker_data(self, data, temp_file_name):
        with wave.open(temp_file_name, 'wb') as wf:
            wf.setnchannels(self.audio_sources["Speaker"]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_sources["Speaker"]["sample_rate"])
            wf.writeframes(data)

    def update_transcript(self, who_spoke, text, time_spoken, transcript_queue: Queue):
        source_info = self.audio_sources[who_spoke]
        transcript = self.transcript_data[who_spoke]

        if source_info["new_phrase"] or len(transcript) == 0:
            if len(transcript) > MAX_PHRASES:
                transcript.pop(-1)

            transcript.insert(0, (f"{text}", time_spoken))

        else:
            transcript[0] = (f"{text}", time_spoken)

        transcript_queue.put_nowait(text)

    def get_transcript(self):
        combined_transcript = list(self.transcript_data["Speaker"])
        combined_transcript = combined_transcript[:MAX_PHRASES]
        return "".join([t[0] for t in combined_transcript])

    def clear_transcript_data(self):
        self.transcript_data["Speaker"].clear()
        self.audio_sources["Speaker"]["last_sample"] = bytes()
        self.audio_sources["Speaker"]["new_phrase"] = True
