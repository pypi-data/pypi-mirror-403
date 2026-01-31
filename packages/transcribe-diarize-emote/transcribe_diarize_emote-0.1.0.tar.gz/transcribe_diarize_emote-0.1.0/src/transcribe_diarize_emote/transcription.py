#transcription.py

from faster_whisper import WhisperModel


class Transcriber:
    def __init__(
        self,
        model_size="small",
        device="cpu",
        compute_type="int8"
    ):
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )

    def transcribe(self, audio_path):
        segments, _ = self.model.transcribe(audio_path, task='translate')
    
        return [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            }
            for seg in segments
        ]