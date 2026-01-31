#emotion_alignment.py

import re
from .models import EmotionMetrics


# ===============================
# REGEX DEFINITIONS
# ===============================

TIMESTAMP_REGEX = re.compile(
    r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})"
)

SPEAKER_REGEX = re.compile(r"<v (.*?)>")
PITCH_RMS_REGEX = re.compile(r"Pitch:\s*([\d\.]+)\s*Hz\s*\|\s*RMS:\s*([\d\.]+)")
DELTA_PITCH_REGEX = re.compile(r"Pitch Difference.*?:\s*([+\-]?\d+\.?\d*)")
DELTA_RMS_REGEX = re.compile(r"RMS Difference.*?:\s*([+\-]?\d+\.?\d*)")


# ===============================
# HELPER — VTT Timestamp → Seconds
# ===============================

def vtt_to_seconds(ts):
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


# ===============================
# PARSE EMOTION OUTPUT → BLOCKS
# ===============================

def parse_emotion_blocks(text):

    lines = text.splitlines()

    blocks = []
    current = None

    for line in lines:

        ts_match = TIMESTAMP_REGEX.search(line)

        if ts_match:
            if current:
                blocks.append(current)

            current = {
                "start": vtt_to_seconds(ts_match.group(1)),
                "end": vtt_to_seconds(ts_match.group(2)),
                "speaker": None,
                "pitch": None,
                "rms": None,
                "delta_pitch": None,
                "delta_rms": None,
            }
            continue

        if current is None:
            continue

        sp = SPEAKER_REGEX.search(line)
        if sp:
            current["speaker"] = sp.group(1)
            continue

        pr = PITCH_RMS_REGEX.search(line)
        if pr:
            current["pitch"] = float(pr.group(1))
            current["rms"] = float(pr.group(2))
            continue

        dp = DELTA_PITCH_REGEX.search(line)
        if dp:
            current["delta_pitch"] = float(dp.group(1))
            continue

        dr = DELTA_RMS_REGEX.search(line)
        if dr:
            current["delta_rms"] = float(dr.group(1))
            continue

    if current:
        blocks.append(current)

    return blocks


# ===============================
# MAIN PUBLIC FUNCTION
# ===============================

def attach_emotion_metrics(segments, emotion_text):

    parsed_blocks = parse_emotion_blocks(emotion_text)

    for seg in segments:

        match = next(
            (
                b for b in parsed_blocks
                if abs(b["start"] - seg.start) < 0.05
                and abs(b["end"] - seg.end) < 0.05
                and b["speaker"] == seg.speaker
            ),
            None
        )

        if match and match["pitch"] is not None:
            seg.emotion = EmotionMetrics(
                pitch=match["pitch"],
                rms=match["rms"],
                delta_pitch=match["delta_pitch"],
                delta_rms=match["delta_rms"],
            )

    return segments
