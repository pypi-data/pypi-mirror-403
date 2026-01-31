#vtt formatter

def seconds_to_vtt(ts):
    h = int(ts // 3600)
    m = int((ts % 3600) // 60)
    s = ts % 60
    return f"{h:02}:{m:02}:{s:06.3f}"


def to_vtt(segments):
    lines = ["WEBVTT\n"]

    for s in segments:
        start = seconds_to_vtt(s.start)
        end = seconds_to_vtt(s.end)

        lines.append(f"{start} --> {end}")
        lines.append(f"<v {s.speaker}> {s.text}")

        if s.emotion:
            lines.append(
                f"NOTE pitch={s.emotion.pitch} rms={s.emotion.rms}"
            )

        lines.append("")

    return "\n".join(lines)
