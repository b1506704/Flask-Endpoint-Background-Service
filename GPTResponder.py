import datetime
from queue import Queue
import openai
import time

openai.api_key = 'lm-studio'
openai.api_base = 'http://localhost:1234/v1'


def generate_response_from_transcript(transcript, suggestion_queue: Queue):

    try:
        stream = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[
                {"role": "system", "content": transcript}],
            temperature=0.0,
            stream=True
        )

        collected_chunks = []
        collected_messages = []

        for chunk in stream:
            if chunk.choices[0].finish_reason != 'stop' and (chunk.choices[0].delta.content is not None and chunk.choices[0].delta.content != ''):
                collected_chunks.append(chunk)
                chunk_message = chunk.choices[0].delta.content
                suggestion_queue.put_nowait(chunk_message)
                collected_messages.append(chunk_message)

    except KeyError as e:
        print(e)
        return ''

    collected_messages = [m for m in collected_messages if m is not None]
    full_reply_content = ''.join([m for m in collected_messages])

    return full_reply_content


class GPTResponder:
    def __init__(self):
        self.response = ''
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber, transcript_queue: Queue, suggestion_queue: Queue):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()
                transcriber.transcript_changed_event.clear()
                transcript_string = transcriber.get_transcript()

                transcript_queue.put_nowait(
                    '\n' + f'[{datetime.datetime.utcnow()}] - END OF MESSAGE' + '\n')

                response = generate_response_from_transcript(
                    transcript_string, suggestion_queue)
                
                suggestion_queue.put('\n' +
                                     f'[{datetime.datetime.utcnow()}] - END OF MESSAGE' + '\n')

                end_time = time.time()
                execution_time = end_time - start_time

                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time

                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval
