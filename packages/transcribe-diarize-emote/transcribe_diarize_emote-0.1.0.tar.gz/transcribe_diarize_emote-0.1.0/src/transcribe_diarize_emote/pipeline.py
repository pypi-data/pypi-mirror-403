#pipeline.py

import os
from .transcription import Transcriber
from .diarization import DiarizationEngine
from .emotion import EmotionEngine
from .models import TranscriptSegment
from .formatting.json_formatter import to_json
from .formatting.text_formatter import to_text
from .formatting.vtt_formatter import to_vtt
from .intermediate_vtt import generate_temp_vtt
from .emotion_alignment import attach_emotion_metrics

class Pipeline:
    def __init__(self, emotion=False, whisper_model="small", device="cpu", compute_type="int8"):
        self.emotion_enabled = emotion
        self.transcriber = Transcriber(model_size=whisper_model, device=device, compute_type=compute_type)
        self.diarizer = DiarizationEngine()
        self.emotion_engine = EmotionEngine() if emotion else None

    def process(self, audio_path):

        raw_emotion_text = None

        # Step 1 — Transcription
        segments = self.transcriber.transcribe(audio_path)

        # Step 2 — Diarization
        diarized = self.diarizer.diarize(audio_path, segments)

        # Convert to objects
        structured = [
            TranscriptSegment(
                start=d["start"],
                end=d["end"],
                speaker=d["speaker"],
                text=d["text"]
            )
            for d in diarized
        ]

        # Step 3 — Emotion (Optional)
        if self.emotion_enabled:
            # 3A — Convert diarized segments → temporary VTT
            temp_vtt_path = generate_temp_vtt(structured)

            try:
                # 3B — Run emotion engine
                emotion_output = self.emotion_engine.analyze(audio_path,temp_vtt_path)
                raw_emotion_text = emotion_output
                # 3C — Attach metrics back to segments
                structured = attach_emotion_metrics(structured,emotion_output)
            
            finally:
                # Always cleanup temp file
                if os.path.exists(temp_vtt_path):
                    os.remove(temp_vtt_path)

        return PipelineResult(structured, raw_emotion_text)


class PipelineResult:
    def __init__(self, segments, raw_emotion_text=None):
        self._segments = segments
        self._raw_emotion_text = raw_emotion_text

    @property
    def json(self):
        return to_json(self._segments)

    @property
    def text(self):
        return to_text(self._segments)

    @property
    def vtt(self):
        if self._raw_emotion_text:
            return self._raw_emotion_text
        return to_vtt(self._segments)