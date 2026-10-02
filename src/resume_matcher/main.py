import os
from pathlib import Path
from tempfile import TemporaryDirectory

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from markdown_it import MarkdownIt
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

if os.getenv("VERCEL") == "1":
    APP_ENV = "vercel"

from .ingestion import add_resumes_to_database
from .llm import analyze_resumes
from .retrieval import build_context, retrieve_resumes

markdown = MarkdownIt("commonmark", {"html": False})

VERCEL_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resume Matcher</title>
  <style>
    :root { font-family: "Segoe UI", sans-serif; color: #202b2a; background: #f3f6f2; }
    * { box-sizing: border-box; }
    body { margin: 0; }
    header { padding: 22px max(20px, calc((100vw - 940px) / 2)); border-bottom: 1px solid #d8e0da; background: #fff; font-weight: 650; }
    main { width: min(940px, calc(100% - 32px)); margin: 32px auto; }
    h1 { margin: 0 0 8px; font-size: 28px; }
    .intro { margin: 0 0 24px; color: #53615e; }
    section { margin-top: 16px; padding: 20px; border: 1px solid #d8e0da; background: #fff; }
    h2 { margin: 0 0 14px; font-size: 18px; }
    label { display: block; margin-bottom: 8px; font-weight: 600; }
    input[type="file"], textarea { width: 100%; border: 1px solid #b9c7c0; background: #fff; color: inherit; font: inherit; }
    input[type="file"] { padding: 10px; }
    textarea { min-height: 170px; padding: 12px; resize: vertical; }
    button { margin-top: 12px; padding: 10px 15px; border: 0; background: #176b5e; color: #fff; font: inherit; font-weight: 600; cursor: pointer; }
    button:disabled { opacity: .6; cursor: wait; }
    [role="status"] { margin-top: 12px; color: #53615e; }
    .markdown { line-height: 1.6; overflow-wrap: anywhere; }
    .markdown h2 { margin-top: 18px; }
    .markdown pre { overflow-x: auto; padding: 12px; background: #f3f6f2; }
    .markdown code { font-family: Consolas, monospace; }
    @media (max-width: 600px) { main { width: calc(100% - 24px); margin: 24px auto; } section { padding: 16px; } }
  </style>
</head>
<body>
  <header>Resume Matcher</header>
  <main>
    <h1>Resume matching</h1>
    <p class="intro">Add PDF resumes, then compare them with a job description.</p>
    <section>
      <h2>Upload resumes</h2>
      <form id="upload-form">
        <label for="resume-files">Resume PDFs</label>
        <input id="resume-files" type="file" accept=".pdf,application/pdf" multiple>
        <button type="submit">Add resumes</button>
      </form>
      <div id="upload-status" role="status" aria-live="polite"></div>
    </section>
    <section>
      <h2>Find matching resumes</h2>
      <form id="match-form">
        <label for="job-description">Job description</label>
        <textarea id="job-description" required></textarea>
        <button type="submit">Find matches</button>
      </form>
    </section>
    <section id="results-section" hidden>
      <h2>Results</h2>
      <article id="results" class="markdown"></article>
    </section>
  </main>
  <script>
    const uploadForm = document.querySelector("#upload-form");
    const uploadInput = document.querySelector("#resume-files");
    const uploadStatus = document.querySelector("#upload-status");
    const matchForm = document.querySelector("#match-form");
    const resultsSection = document.querySelector("#results-section");
    const results = document.querySelector("#results");
    async function sendRequest(url, options, button, onSuccess) {
      button.disabled = true;
      try {
        const response = await fetch(url, options);
        const responseText = await response.text();
        let payload;
        try {
          payload = JSON.parse(responseText);
        } catch {
          throw new Error(responseText.trim().slice(0, 240) || `Request failed (${response.status}).`);
        }
        if (!response.ok) throw new Error(payload.detail || "Request failed.");
        onSuccess(payload);
        return true;
      } catch (error) {
        uploadStatus.textContent = error.message;
        return false;
      } finally {
        button.disabled = false;
      }
    }
    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!uploadInput.files.length) {
        uploadStatus.textContent = "Please upload at least one PDF resume.";
        return;
      }
      const maxBatchBytes = 4 * 1024 * 1024;
      const batches = [];
      let currentBatch = [];
      let currentBatchBytes = 0;

      for (const file of uploadInput.files) {
        if (file.size > maxBatchBytes) {
          uploadStatus.textContent = `${file.name} is larger than 4 MB. Upload a smaller PDF.`;
          return;
        }
        if (currentBatchBytes + file.size > maxBatchBytes && currentBatch.length) {
          batches.push(currentBatch);
          currentBatch = [];
          currentBatchBytes = 0;
        }
        currentBatch.push(file);
        currentBatchBytes += file.size;
      }
      if (currentBatch.length) batches.push(currentBatch);

      for (let index = 0; index < batches.length; index++) {
        const formData = new FormData();
        for (const file of batches[index]) formData.append("files", file);
        uploadStatus.textContent = `Uploading batch ${index + 1} of ${batches.length}...`;
        const succeeded = await sendRequest(
          "/upload",
          { method: "POST", body: formData },
          uploadForm.querySelector("button"),
          (payload) => { uploadStatus.innerHTML = payload.html; }
        );
        if (!succeeded) return;
      }
    });
    matchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const jobDescription = document.querySelector("#job-description").value;
      sendRequest("/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: jobDescription })
      }, matchForm.querySelector("button"), (payload) => {
        results.innerHTML = payload.html;
        resultsSection.hidden = false;
      });
    });
  </script>
</body>
</html>
"""


def render_markdown(content: str) -> str:
    return markdown.render(content)


def match_resumes(job_description: str) -> str:
    if not job_description.strip():
        return "Please enter a job description."

    results = retrieve_resumes(job_description)
    if not results:
        return "No resumes found in the database."

    context = build_context(results)
    analysis = analyze_resumes(job_description, context)
    retrieved_section = "## Retrieved Resumes\n\n"

    for rank, (document, score) in enumerate(results, start=1):
        resume_name = document.metadata.get("resume", "Unknown")
        retrieved_section += (
            f"**{rank}. {resume_name}**  \n"
            f"Retrieval distance: `{score:.4f}`\n\n"
        )

    return retrieved_section + "\n## Resume Analysis\n\n" + analysis


class MatchRequest(BaseModel):
    job_description: str


app = FastAPI()


if APP_ENV == "vercel":

    @app.get("/", response_class=HTMLResponse)
    def home_page():
        return VERCEL_PAGE


@app.post("/upload")
async def upload_resumes(
    files: list[UploadFile] | None = File(default=None)
):
    if not files:
        status = "Please upload at least one PDF resume."
        return {"html": render_markdown(status)}

    try:
        with TemporaryDirectory(prefix="resume-matcher-") as temporary_directory:
            saved_paths = []

            for index, uploaded_file in enumerate(files):
                original_name = (uploaded_file.filename or "resume.pdf").replace(
                    "\\",
                    "/"
                )
                safe_name = Path(original_name).name or "resume.pdf"
                upload_directory = Path(temporary_directory) / str(index)
                upload_directory.mkdir()
                file_path = upload_directory / safe_name

                with file_path.open("wb") as saved_file:
                    while chunk := await uploaded_file.read(1024 * 1024):
                        saved_file.write(chunk)

                saved_paths.append(str(file_path))

            status = await run_in_threadpool(
                add_resumes_to_database,
                saved_paths
            )
    finally:
        for uploaded_file in files:
            await uploaded_file.close()

    return {"html": render_markdown(status)}


@app.post("/match")
def match_endpoint(request: MatchRequest):
    result = match_resumes(request.job_description)
    return {"html": render_markdown(result)}


if APP_ENV != "vercel":

    import gradio as gr

    with gr.Blocks() as demo:
        gr.Markdown(
            """
            # Resume Matcher RAG

            Upload resumes and compare them
            with a job description using
            semantic retrieval and LLM analysis.
            """
        )
        gr.Markdown("## 1. Upload Resumes")
        resume_files = gr.File(
            label="Upload Resume PDFs",
            file_count="multiple",
            file_types=[".pdf"],
            type="filepath"
        )
        add_button = gr.Button("Add Resumes to Database")
        upload_status = gr.Markdown()
        add_button.click(
            fn=add_resumes_to_database,
            inputs=resume_files,
            outputs=upload_status
        )
        gr.Markdown("## 2. Enter Job Description")
        job_description = gr.Textbox(
            label="Job Description",
            placeholder="Paste the job description here...",
            lines=12
        )
        match_button = gr.Button("Find Matching Resumes")
        result_output = gr.Markdown()
        match_button.click(
            fn=match_resumes,
            inputs=job_description,
            outputs=result_output
        )

    app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "resume_matcher.main:app",
        host="127.0.0.1",
        port=7860,
        reload=True
    )