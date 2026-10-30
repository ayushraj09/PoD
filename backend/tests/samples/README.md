# Speech samples for the STT check and audio tests

`python -m app.pipeline.stt tests/samples/` transcribes every file here; `EXPECTED.tsv` holds the true transcripts.

| File | Source | Licence |
|---|---|---|
| `fleurs_hindi_1.wav`, `fleurs_hindi_2.wav`, `fleurs_english_1.wav`, `fleurs_english_2.wav` | [Google FLEURS](https://huggingface.co/datasets/google/fleurs), validation split (hi_in, en_us), rows 0-1 | CC BY 4.0 |
| `chrome_english_1.webm` | `fleurs_english_1.wav` re-encoded to Opus/WebM (what Chrome records) | CC BY 4.0 |
| `iphone_hindi_1.m4a` | `fleurs_hindi_1.wav` re-encoded to AAC/MP4 (what Safari records); not a real iPhone recording | CC BY 4.0 |
| `smallest_english.wav` | [smallest-inc/cookbook](https://github.com/smallest-inc/cookbook/tree/main/speech-to-text/getting-started/samples) sample | from the Smallest AI cookbook repo |

Still worth adding: a real recording from an iPhone and from an Android phone through the widget.
