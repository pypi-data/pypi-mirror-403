# transcribe-diarize-emote

**One-stop audio intelligence pipeline** combining:

- Transcription (faster-whisper)
- Speaker Diarization (diarizer-lite)
- Acoustic Emotion Context Enrichment (whisper-speaker-emotion)

Designed to produce **LLM-ready conversational transcripts** in a single pass.

## What This Library Solves

Modern STT systems give you text.  
But real conversation intelligence requires:

- A clean transcription system
- Who spoke → Diarization  
- How was it said → Acoustic emotion context  
- Clean speaker turns → LLM context engineering  

`transcribe-diarize-emote` solves all three **in one pipeline**.

## Why This Matters For LLM Workflows

Output can be directly used for:

- Summarization
- Sentiment Analysis
- Topic Modeling
- Call Quality Monitoring
- Compliance Analytics
- Customer Experience Intelligence
- Conversation Mining
- Agent Coaching
- Risk / Escalation Detection

## Key Features

- Offline capable
- No API keys required
- CPU supported by default
- CUDA GPU acceleration
- Emotion layer optional toggle
- Direct LLM-ready outputs

## Installation

```bash
pip install transcribe-diarize-emote
```

## Core Usage

```python
from transcribe_diarize_emote import Pipeline

pipe = Pipeline(
    emotion=True,
    whisper_model="large-v3",
    device="cpu",
    compute_type="int8"
)

result = pipe.process("call.wav")

print(result.vtt)
```

## Pipeline Configuration Explained

### - Emotion Layer (emotion)

| Setting | Meaning |
|---|---|
| emotion=True | Adds acoustic emotion metrics |
| emotion=False | Faster pipeline, text only |

### - Whisper Model (whisper_model)

**Recommended**

- large-v3

**Other Supported Models**

- tiny  
- base  
- small  
- medium  
- large-v2  
- large-v3 *(recommended for quality)*  

### - Device Support (device)

| Device | Supported |
|---|---|
| CPU | Yes |
| CUDA GPU | Yes |
| Apple MPS | No |

### - Compute Type (compute_type)

| Device | Recommended |
|---|---|
| CPU | int8 |
| CUDA | float16 |

### - Audio Format

The major supported audio formats are:

- .mp3
- .wav

## Output Behavior

### - emotion=False (Default)

**Recommended Outputs**

- `result.text`
- `result.json`
- `result.vtt`

#### Sample Json

```json
[
  {
    "start": 0.0,
    "end": 4.0,
    "speaker": "Speaker0",
    "text": "Hi, I wanted to report an issue with my ride this morning."
  },
  {
    "start": 4.0,
    "end": 7.0,
    "speaker": "Speaker1",
    "text": "Sure, could you tell me what happened?"
  },
  {
    "start": 7.0,
    "end": 13.0,
    "speaker": "Speaker0",
    "text": "Yeah, driver was polite but car wasn't clean and smelled weird."
  },
  {
    "start": 13.0,
    "end": 17.0,
    "speaker": "Speaker1",
    "text": "I'm sorry to hear that. Anything else?"
  },
  {
    "start": 17.0,
    "end": 25.0,
    "speaker": "Speaker0",
    "text": "Also he took a longer route even after I gave the correct address. Got it. We will look into this and report back."
  }
]
```
### - emotion=True

**Recommended Output**

- `result.vtt` *(Better for readability and LLM understanding)*

#### Sample vtt

```vtt
WEBVTT

Average Pitch:
Speaker0: 230.45 Hz
Speaker1: 190.78 Hz

Average RMS:
Speaker0: 0.068
Speaker1: 0.061

00:00:00.000 --> 00:00:04.000
<v Speaker0> Hi, I just wanted to give some feedback about my cab ride this morning.
Pitch: 236.22 Hz | RMS: 0.066
Pitch Difference with Average: +5.77 Hz
RMS Difference with Average: -0.002

00:00:04.000 --> 00:00:07.000
<v Speaker1> Sure, I can help you with that. Could you tell me what happened?
Pitch: 192.45 Hz | RMS: 0.062
Pitch Difference with Average: +1.67 Hz
RMS Difference with Average: +0.001
```

## Output Philosophy

### - emotion=False

Structured conversational transcript optimized for:

- Summarization
- Classification
- Topic modeling
- Search indexing

### - emotion=True

Emotion-enriched transcript including (Additional context for LLM for sentiment analysis):

- Speaker baseline voice metrics
- Pitch (F0)
- Loudness (RMS)
- Emotional deviation from baseline tone

## Citations

This library builds on the following open-source technologies:

### - faster-whisper
    High-performance Whisper inference powered by **CTranslate2**, enabling fast CPU and GPU transcription without requiring PyTorch runtime.
    Project: https://pypi.org/project/faster-whisper/
### - diarizer-lite
    Lightweight stereo energy-based speaker diarization designed for offline processing and post-STT conversational structuring.
    Project: https://pypi.org/project/diarizer-lite/
### - whisper-speaker-emotion
    Emotion-aware speaker analysis using audio pitch and loudness aligned with Whisper diarized VTT transcripts.
    Project: https://pypi.org/project/whisper-speaker-emotion/

## Designed For LLM Context Engineering

Traditional LLM pipelines rely purely on text transcripts.

However, real-world conversations contain **acoustic emotional signals** that text alone cannot capture.

Instead of forcing LLMs to infer emotion from text,  
`transcribe-diarize-emote` provides **measured acoustic context** directly from audio.

This enables LLM systems to:

- Detect emotional spikes
- Improve sentiment confidence scoring
- Identify escalation or frustration moments
- Improve summarization quality
- Improve explainability of sentiment and classification outputs

This is an example of **context engineering** — improving LLM outputs by improving the quality and richness of input context rather than modifying or tuning the model itself.

## Contributing

Pull requests are welcome.

For major changes, please open an issue first to discuss what you would like to change.

Please ensure tests and documentation are updated where applicable.

## License

MIT License