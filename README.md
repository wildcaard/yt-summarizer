# YouTube Video Summarizer Walkthrough

Welcome to the YouTube Video Summarizer! This small application simplifies the task of gleaning insights from educational, informational, or otherwise long YouTube recordings. Here's a brief walkthrough of how it was built, how it works, and how to verify it.

## 🛠️ Prerequisites & Setup

1. **Environment Setup:** Ensure you have Python installed. The required third-party libraries have been declared in `requirements.txt`:
   - `streamlit`
   - `langchain`
   - `langchain-openai`
   - `youtube-transcript-api`
   - `python-dotenv`

2. **Environment Variables:** The app relies on OpenRouter to execute the LangChain prompts. The template for required keys can be found in `.env.example`:
   - Copy `.env.example` to `.env`.
   - Provide your `OPENROUTER_API_KEY`.
   - Ensure the correct `OPENROUTER_MODEL` is declared.

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Running the application:**
   Launch the app via Streaming by typing:
   ```bash
   streamlit run app.py
   ```

## 🏗️ Architecture & Modules

The project is decoupled into small, coherent pieces.

### 1. `utils/transcript.py`
This module acts as the boundary dealing with YouTube. It exposes two functions:
- `extract_video_id(url)`: Robustly identifies typical YouTube URL formats (`youtu.be/...` and `www.youtube.com/watch?v=...`) and isolates the video ID string using a Regex operation.
- `get_transcript(url)`: Once the real ID is sourced, it negotiates via the `youtube-transcript-api`. Then, it safely formats those chunked captions into a single text slab for consumption.

### 2. `utils/summarizer.py`
This module bridges the LLM processing using LangChain components targeting an OpenRouter interface.
- It heavily leverages **Pydantic Models** alongside Langchain's **JsonOutputParser**.
- Ensures that instead of random LLM prose, we parse clean strict schema data back.
- Returns a JSON dictionary featuring the required `short_summary`, `key_takeaways` array, and a `detailed_summary`.

### 3. `app.py`
Your clean interface. We lean entirely on natively supported Streamlit components without extra frontend friction for MVP sake:
- **`st.title/markdown`**: Headers.
- **`st.button` & `st.spinner`**: Async-looking operations with safety feedback.
- It encapsulates all `utils/` imports inside custom-written exception captures (like `InvalidYouTubeURLError`, `TranscriptNotAvailableError`, `APIError`).

## 🧪 Quick Test Plan

To test, you just need a few valid YouTube links!
- Ensure it successfully parses a standard video (like a dev walkthrough or a news story) and structures the sections natively.
- Feed it a bad "https://google.com" URL and note the expected polite error.
- Use a video known for completely lacking an auto-generated or manual transcript and ensure `TranscriptNotAvailableError` presents appropriately in the Streamlit UI.
