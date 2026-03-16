# YouTube Video Summarizer — Implementation Plan

A beginner-friendly Python app that takes a YouTube URL, extracts its transcript, and uses LangChain + OpenRouter to produce a short summary, bullet-point key takeaways, and a detailed summary — all displayed through a clean Streamlit UI.

---

## Proposed Changes

### Project Structure

```
C:\Users\MukeshKumar\.gemini\antigravity\scratch\yt-summarizer\
│
├── app.py                  # Main Streamlit UI
├── requirements.txt        # Python dependencies
├── .env.example            # Template for required env vars
│
└── utils/
    ├── __init__.py
    ├── transcript.py       # YouTube transcript extraction
    └── summarizer.py       # LangChain + OpenRouter summarization
```

---

### `requirements.txt` [NEW]

```
streamlit
langchain
langchain-openai
youtube-transcript-api
python-dotenv
```

---

### `.env.example` [NEW]

```
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

---

### `utils/transcript.py` [NEW]

Responsibilities:
- Parse and validate the YouTube video ID from the given URL (supports both `youtu.be` and `youtube.com/watch?v=` formats)
- Call `YouTubeTranscriptApi.get_transcript(video_id)` to retrieve the transcript
- Merge transcript chunks into a single string
- Raise clear, user-friendly exceptions for:
  - Invalid URL (no video ID found)
  - Transcript not available (disabled or non-existent)

---

### `utils/summarizer.py` [NEW]

Responsibilities:
- Load `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from environment (via `python-dotenv`)
- Initialize `ChatOpenAI` from `langchain_openai` pointing to OpenRouter's base URL:  
  `https://openrouter.ai/api/v1`
- Define a single `summarize(transcript_text)` function that sends one LLM call using a structured prompt requesting:
  1. **Short Summary** — 2–3 sentences
  2. **Key Takeaways** — 5 bullet points
  3. **Detailed Summary** — full paragraph
- Parse the LLM response into the three sections
- Raise descriptive errors on API failure

---

### `app.py` [NEW]

Responsibilities:
- Streamlit page config (title, icon, layout)
- URL input text box
- "Summarize" button triggers:
  1. `get_transcript(url)` → transcript text
  2. `summarize(transcript)` → structured output
- Display sections using `st.info`, `st.markdown`, `st.expander`
- Show spinner during processing
- Display user-friendly error messages with `st.error`

---

## Verification Plan

### Manual Verification (primary method — no automated tests for this MVP)

Since this project is purely UI + external API driven, manual testing is the most practical approach:

1. **Install dependencies:**
   ```bash
   cd C:\Users\MukeshKumar\.gemini\antigravity\scratch\yt-summarizer
   pip install -r requirements.txt
   ```

2. **Set up `.env`:**
   ```
   Copy .env.example to .env
   Add a valid OPENROUTER_API_KEY
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Test cases to manually verify:**

   | Test | Input | Expected Result |
   |------|-------|-----------------|
   | Happy path | Valid YouTube URL with transcript | Short summary + bullet points + detailed summary displayed |
   | Invalid URL | `https://not-youtube.com` | Error: "Could not extract a valid YouTube video ID" |
   | No transcript | URL of a video with disabled captions | Error: "Transcript is not available for this video" |
   | Empty input | Click Summarize with empty field | Warning: "Please enter a YouTube URL" |
   | Bad API key | Wrong key in `.env` | Error: "OpenRouter API error..." |

> [!NOTE]
> The user will need an active OpenRouter API key to test the happy path. A free-tier account works.
