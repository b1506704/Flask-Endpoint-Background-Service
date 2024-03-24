import torch
import os
import whisper

# # Create an instance of the Whisper model with the appropriate dimensions
# model = whisper.model.Whisper(whisper.model.ModelDimensions(
#     n_mels=80,
#     n_vocab=51864,
#     n_audio_ctx=1500,
#     n_audio_state=1024,
#     n_audio_head=16,
#     n_audio_layer=24,
#     n_text_ctx=448,
#     n_text_state=1024,
#     n_text_head=16,
#     n_text_layer=24
# ))

# # Load the model from the safetensors file
# safetensors.torch.load_model(model, os.path.join(os.getcwd(), 'whisper-medium.en.safetensors'))

# # Set the alignment heads for the model
# model.set_alignment_heads(b"ABzY8usPae0{>%R7<zz_OvQ{)4kMa0BMw6u5rT}kRKX;$NfYBv00*Hl@qhsU00")

def get_model():
    return WhisperTranscriber()

class WhisperTranscriber:
    def __init__(self):
        self.audio_model = whisper.load_model(
            os.path.join(os.getcwd(), 'tiny.en.pt'))      

        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    def get_transcription(self, wav_file_path):
        try:
            result = self.audio_model.transcribe(
                wav_file_path, fp16=torch.cuda.is_available())
        except Exception as e:
            print(e)
            return ''
        return result['text'].strip()
