#json formatter

def to_json(segments):
    output = []

    for s in segments:
        obj = {
            "start": s.start,
            "end": s.end,
            "speaker": s.speaker,
            "text": s.text
        }

        if s.emotion:
            obj["emotion"] = {
                "pitch": s.emotion.pitch,
                "rms": s.emotion.rms,
                "delta_pitch": s.emotion.delta_pitch,
                "delta_rms": s.emotion.delta_rms
            }

        output.append(obj)

    return output
