#diarization.py

from diarizer_lite import Diarizer


class DiarizationEngine:
    def __init__(self):
        self.diarizer = Diarizer()

    def diarize(self, audio_path, segments):
        return self.diarizer.diarize_segments(
            audio_file=audio_path,
            segments=segments
        )
