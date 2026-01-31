#text formatter

def to_text(segments):
    lines = []

    for s in segments:
        base = f"{s.speaker} ({s.start:.2f}-{s.end:.2f}): {s.text}"

        if s.emotion:
            base += (
                f" | pitch={s.emotion.pitch:.2f}"
                f" rms={s.emotion.rms:.4f}"
            )

        lines.append(base)

    return "\n".join(lines)
