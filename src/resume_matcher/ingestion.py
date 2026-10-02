from langchain_core.documents import Document
from pypdf import PdfReader

from .embeddings import vectorstore
from .utils import (
    create_resume_id,
    get_filename
)


def load_resume(
    file_path: str
):
    """
    Load one PDF and combine all pages
    into one resume Document.
    """

    reader = PdfReader(file_path)

    full_text = "\n\n".join(
        (page.extract_text(extraction_mode="plain") or "").strip()
        for page in reader.pages
    )

    if not full_text.strip():
        raise ValueError(
            "The PDF contains no readable text."
        )

    file_name = get_filename(
        file_path
    )

    return Document(
        page_content=full_text,
        metadata={
            "resume": file_name,
            "source": file_name
        }
    )


def add_resume_to_database(
    file_path: str
) -> str:
    """
    Process and store one resume
    in Chroma.
    """

    if not file_path.lower().endswith(
        ".pdf"
    ):
        raise ValueError(
            "Only PDF resumes are supported."
        )

    document = load_resume(
        file_path
    )

    resume_id = create_resume_id(
        file_path
    )

    # Delete an existing version
    # with the same ID.
    try:
        vectorstore.delete(
            ids=[resume_id]
        )
    except Exception:
        pass

    vectorstore.add_documents(
        documents=[document],
        ids=[resume_id]
    )

    return document.metadata[
        "resume"
    ]


def add_resumes_to_database(
    files
):

    if not files:
        return (
            "Please upload at least "
            "one PDF resume."
        )

    added = []
    skipped = []

    for file_path in files:

        try:

            filename = add_resume_to_database(
                str(file_path)
            )

            added.append(filename)

        except Exception as exc:

            skipped.append(
                f"{file_path}: {exc}"
            )

    result = (
        "## Resume Database Updated\n\n"
    )

    result += (
        f"Added: **{len(added)}** resume(s)\n\n"
    )

    for filename in added:
        result += f"- {filename}\n"

    if skipped:

        result += (
            f"\nSkipped: **{len(skipped)}**\n\n"
        )

        for error in skipped:
            result += f"- {error}\n"

    return result