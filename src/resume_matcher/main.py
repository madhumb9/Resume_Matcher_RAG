import gradio as gr

from fastapi import FastAPI

from .ingestion import (
    add_resumes_to_database
)

from .retrieval import (
    retrieve_resumes,
    build_context
)

from .llm import (
    analyze_resumes
)



# MAIN RAG FUNCTION


def match_resumes(
    job_description: str
) -> str:

    if not job_description.strip():

        return (
            "Please enter a job description."
        )

    # 1. Retrieve
    results = retrieve_resumes(
        job_description
    )

    if not results:

        return (
            "No resumes found in the database."
        )

    # 2. Build context
    context = build_context(
        results
    )

    # 3. LLM analysis
    analysis = analyze_resumes(
        job_description,
        context
    )

    # 4. Display retrieved resumes
    retrieved_section = (
        "## Retrieved Resumes\n\n"
    )

    for rank, (
        document,
        score
    ) in enumerate(
        results,
        start=1
    ):

        resume_name = (
            document.metadata.get(
                "resume",
                "Unknown"
            )
        )

        retrieved_section += (
            f"**{rank}. {resume_name}**  \n"
            f"Retrieval distance: "
            f"`{score:.4f}`\n\n"
        )

    return (
        retrieved_section
        + "\n"
        + "## Resume Analysis\n\n"
        + analysis
    )



# GRADIO UI


with gr.Blocks() as demo:

    gr.Markdown(
        """
        # Resume Matcher RAG

        Upload resumes and compare them
        with a job description using
        semantic retrieval and LLM analysis.
        """
    )

    # Upload Resumes
   

    gr.Markdown(
        "## 1. Upload Resumes"
    )

    resume_files = gr.File(
        label="Upload Resume PDFs",
        file_count="multiple",
        file_types=[".pdf"],
        type="filepath"
    )

    add_button = gr.Button(
        "Add Resumes to Database"
    )

    upload_status = gr.Markdown()

    add_button.click(
        fn=add_resumes_to_database,
        inputs=resume_files,
        outputs=upload_status
    )

   
    # Job Description
   

    gr.Markdown(
        "## 2. Enter Job Description"
    )

    job_description = gr.Textbox(
        label="Job Description",
        placeholder=(
            "Paste the job description here..."
        ),
        lines=12
    )

    match_button = gr.Button(
        "Find Matching Resumes"
    )

    result_output = gr.Markdown()

    match_button.click(
        fn=match_resumes,
        inputs=job_description,
        outputs=result_output
    )



# FASTAPI APP


app = FastAPI()

app = gr.mount_gradio_app(
    app,
    demo,
    path="/"
)



# LOCAL RUN


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "resume_matcher.main:app",
        host="127.0.0.1",
        port=7860,
        reload=True
    )