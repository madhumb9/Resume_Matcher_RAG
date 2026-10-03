# Resume Matcher

Resume Matcher is a retrieval-augmented application for comparing PDF resumes with a job description. It extracts text from uploaded resumes, retrieves the most relevant resumes, and uses a language model to summarize matches and rank candidates. It does not produce percentage match scores.

## Features

- Upload one or more PDF resumes.
- Extract text from readable PDFs and store it in Chroma.
- Retrieve the five most relevant resumes for a job description.
- Generate a grounded comparison of matching skills, missing or unclear requirements, and overall textual relevance.
- Run locally with Gradio, Ollama, and a local Chroma database, or deploy the API and web interface on Vercel.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- For local inference: [Ollama](https://ollama.com/) with the `phi3:latest` and `nomic-embed-text` models
- For Vercel deployment: Gemini API access, a Hugging Face token, and a Chroma Cloud database

## Run Locally

Clone the repository and install the local dependencies:

```powershell
uv sync --extra local
```

Copy the example environment file and adjust it if needed:

```powershell
Copy-Item .env.example .env
```

The default local models are `phi3:latest` for text generation and `nomic-embed-text` for embeddings. Pull them with Ollama if they are not installed:

```powershell
ollama pull phi3:latest
ollama pull nomic-embed-text
```

Make sure Ollama is running, then start the application:

```powershell
uv run python -m resume_matcher.main
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860). Upload PDF resumes, enter a job description, and select **Find Matching Resumes**. Local Chroma data is stored in `vector_db/`.

## Deploy on Vercel

The Vercel entry point is `api/index.py`. Vercel sets the `VERCEL` environment variable, which selects the cloud configuration automatically. Add these values in the Vercel project's **Settings > Environment Variables**:

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Authenticates Gemini text generation. |
| `HF_TOKEN` | Authenticates Hugging Face hosted resume embeddings. |
| `CHROMA_API_KEY` | Authenticates the Chroma Cloud database. |
| `CHROMA_TENANT` | Chroma Cloud tenant name or ID. |
| `CHROMA_DATABASE` | Chroma Cloud database name. |

Set the variables for the environments you use, then redeploy. Uploads are stored in the configured Chroma Cloud collection, so the resumes remain available across function invocations.

## API

### `POST /upload`

Uploads one or more PDF files as multipart form data using the `files` field. The response contains an HTML-rendered upload status.

### `POST /match`

Accepts a JSON request with a job description:

```json
{
	"job_description": "The job description text"
}
```

The response contains an HTML-rendered list of retrieved resumes and the language model's analysis. If matching fails, check the Vercel function logs for the traceback.

## Notes

- The application extracts text directly from PDFs; scanned image-only PDFs require OCR and may not be readable.
- Resume files with no extractable text are skipped during upload.
- In Vercel mode, resume text is sent to Hugging Face for embeddings and retrieved resume text is sent to Gemini for analysis. Use only resumes you are authorized to process.
- Local model and environment settings are loaded from `.env`. `.env` is excluded from version control; do not commit API tokens or secrets.
