#emotion.py

from whisper_speaker_emotion import analyze_speaker_emotion


class EmotionEngine:
    def analyze(self, audio_path, vtt_path):
        return analyze_speaker_emotion(
            audio_path=audio_path,
            vtt_path=vtt_path
        )
