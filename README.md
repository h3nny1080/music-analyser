# Music Analyser

A multi-agent system that analyses audio from YouTube, Spotify, SoundCloud, Apple Music, or uploaded files. It identifies instruments using AI, then lets you export individual stems as isolated audio files or generate sheet music PDFs.

---

## What it does

1. **Input** — paste a YouTube, Spotify, SoundCloud, or Apple Music link, or upload an audio file (MP3, WAV, FLAC, AIFF, OGG, M4A)
2. **Confirm** — for streaming links, the system finds the track on YouTube and asks you to confirm before processing
3. **Separate** — splits the audio into up to 6 stems (vocals, drums, bass, guitar, piano, other) using Meta's Demucs
4. **Identify** — classifies each stem using Microsoft's CLAP model
5. **Export** — choose any instrument to export as an isolated audio file (WAV/FLAC/AIFF) or as a PDF sheet music score

---

## Requirements

- Python 3.11
- Node.js 20 LTS or higher
- ffmpeg
- LilyPond (only required for sheet music export)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/music-analyser.git
cd music-analyser
```

---

### 2. Install system dependencies

#### ffmpeg

**Windows**

1. Download the latest Windows build from https://ffmpeg.org/download.html (click Windows → "Windows builds by BtbN") and download `ffmpeg-master-latest-win64-gpl.zip`
2. Create `C:\ffmpeg` and extract the zip contents so the structure is:
   ```
   C:\ffmpeg\bin\ffmpeg.exe
   C:\ffmpeg\bin\ffprobe.exe
   ```
3. Add `C:\ffmpeg\bin` to your system PATH:
   - Open Start → search "Edit the system environment variables"
   - Click Environment Variables → under System variables find `Path` → Edit → New
   - Add `C:\ffmpeg\bin` and click OK on all windows
4. Open a new terminal and verify:
   ```powershell
   ffmpeg -version
   ```

**macOS**

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**

```bash
sudo apt update && sudo apt install ffmpeg
```

---

#### LilyPond (sheet music export only)

**Windows**

1. Download the Windows installer from https://lilypond.org/download.html
2. Run the installer — it installs to `C:\Program Files (x86)\lilypond-2.26.0-mingw-x86_64\lilypond-2.26.0\bin\` by default
3. Add the `bin` folder to your system PATH the same way as ffmpeg above
4. Open a new terminal and verify:
   ```powershell
   lilypond --version
   ```

**macOS**

```bash
brew install lilypond
```

**Linux (Ubuntu/Debian)**

```bash
sudo apt install lilypond
```

---

### 3. Create a Python 3.11 virtual environment

**Windows**

First install Python 3.11 from https://www.python.org/downloads/release/python-3119/ if not already installed. During installation tick "Add to PATH".

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt. You will need to reactivate the venv every time you open a new terminal.

---

### 4. Install Python dependencies

With your venv active:

```bash
pip install --upgrade pip setuptools wheel
pip install basic-pitch tensorflow
pip install demucs torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn python-multipart pydantic-settings
pip install yt-dlp librosa soundfile numpy requests mutagen
pip install transformers music21
pip install pytest pytest-asyncio
```

> **GPU users (optional but much faster):** Replace the Demucs/torch install line with:
> ```bash
> pip install demucs torch torchaudio --index-url https://download.pytorch.org/whl/cu118
> ```
> This reduces separation time from ~5 minutes to ~30 seconds per track.

---

### 5. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

### 6. Configure environment variables

Copy the example env file:

**Windows**
```powershell
copy .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
MAX_UPLOAD_MB=100
LILYPOND_PATH=C:\Program Files (x86)\lilypond-2.26.0-mingw-x86_64\lilypond-2.26.0\bin\lilypond.EXE
```

> **Spotify credentials** are only needed if you want Spotify link support. Register a free app at https://developer.spotify.com/dashboard to get your client ID and secret.

> **macOS / Linux:** Update `LILYPOND_PATH` to the output of `which lilypond`, e.g. `/usr/local/bin/lilypond`

Create the temp directory:

**Windows**
```powershell
mkdir C:\tmp\music-analyser
```

**macOS / Linux**
```bash
mkdir -p /tmp/music-analyser
```

---

### 7. Run the tests

From the project root with your venv active:

```bash
pytest tests/ -v
```

To run only the fast unit tests and skip the slow model tests:

```bash
pytest tests/ -v -k "not separation and not classification and not Pipeline"
```

All tests should pass before running the application.

---

### 8. Start the backend

With your venv active, from the project root:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000. Visit http://localhost:8000/docs for the interactive API explorer.

---

### 9. Start the frontend

Open a second terminal (leave the backend running in the first). No need to activate the venv for this terminal.

```bash
cd frontend
npm run dev
```

The app will be available at http://localhost:5173.

---

## First run

The first time you run the pipeline, two AI models will download automatically:

| Model | Size | Location |
|---|---|---|
| Demucs `htdemucs_6s` | ~80MB | `~/.cache/torch/hub/` |
| CLAP `laion/clap-htsat-unfused` | ~600MB | `~/.cache/huggingface/` |

This makes the first analysis take longer than usual. Every run after that uses the cached models. It is recommended to test with a short track (30–60 seconds) on first run.

---

## Supported input formats

| Type | Supported |
|---|---|
| YouTube links | ✅ Full track |
| Spotify links | ✅ via YouTube match |
| Apple Music links | ✅ via YouTube match |
| SoundCloud links | ✅ Full track |
| MP3 upload | ✅ |
| WAV upload | ✅ |
| FLAC upload | ✅ |
| AIFF upload | ✅ |
| OGG upload | ✅ |
| M4A upload | ✅ |

> **Note:** Spotify and Apple Music use DRM-protected streams. When you paste one of these links, the system fetches the track metadata and finds the same song on YouTube, then asks you to confirm the match before processing.

---

## Supported output formats

| Type | Format | Best for |
|---|---|---|
| Isolated audio | WAV | Best quality, universal |
| Isolated audio | FLAC | Lossless, smaller than WAV |
| Isolated audio | AIFF | Logic Pro / GarageBand |
| Sheet music | PDF | Printing, reading, sharing |

---

## Project structure

```
music-analyser/
├── ingestion/          # Input routing, YouTube matching, audio normalisation
├── separation/         # Demucs 6-stem separation
├── classification/     # CLAP instrument identification
├── interaction/        # User selection and session management
├── output/             # Sheet music and audio export
├── orchestrator/       # Pipeline wiring, session store, progress tracking
├── api/                # FastAPI routes
│   └── routes/
├── config/             # Settings and environment config
├── tests/              # Unit and end-to-end tests
└── frontend/           # React + Vite UI
```

---

## Troubleshooting

**`ffmpeg` or `lilypond` not recognised after installation**
Close your terminal completely and open a new one — PATH changes don't apply to already-open terminals.

**`ModuleNotFoundError` when running pytest**
Make sure you are running pytest from the project root (`music-analyser/`) with the venv active, not from inside the `tests/` folder.

**Progress bar stuck at 0%**
The first run downloads the Demucs and CLAP models (~680MB total). Give it a few minutes on first use.

**Sheet music test skipped**
LilyPond is not on your PATH. Verify with `lilypond --version` in a fresh terminal. If that fails, re-check the PATH step in section 2.

**Spotify link returns no preview**
Not all Spotify tracks have 30-second previews available via the API. The system will fall back to a YouTube search using the track metadata.

**`[Errno 22] Invalid argument` on Windows**
This is caused by special characters in file paths. Make sure your project is not inside a folder with brackets, ampersands, or other special characters in the path.

---

## Tech stack

| Layer | Technology |
|---|---|
| Audio download | yt-dlp |
| Audio normalisation | ffmpeg, librosa |
| Stem separation | Demucs htdemucs_6s |
| Instrument classification | CLAP (laion/clap-htsat-unfused) |
| Audio to MIDI | Basic Pitch (Spotify) |
| MIDI to sheet music | music21 + LilyPond |
| Backend | Python 3.11, FastAPI |
| Frontend | React, Vite |

---

## Licence

MIT
