#intermediate_vtt

import tempfile
from .formatting.vtt_formatter import seconds_to_vtt


def generate_temp_vtt(segments):
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".vtt"
    )

    temp_file.close()

    with open(temp_file.name, "w") as f:
        f.write("WEBVTT\n\n")

        for s in segments:
            start = seconds_to_vtt(s.start)
            end = seconds_to_vtt(s.end)

            f.write(f"{start} --> {end}\n")
            f.write(f"<v {s.speaker}> {s.text}\n\n")

    return temp_file.name
