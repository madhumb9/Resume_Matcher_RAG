from langchain_core.documents import Document

from .embeddings import vectorstore


RETRIEVAL_K = 5


def retrieve_resumes(
    job_description: str,
    k: int = RETRIEVAL_K
):
    """
    Retrieve the most relevant resumes
    using semantic similarity search.
    """

    if not job_description.strip():
        return []

    results = (
        vectorstore
        .similarity_search_with_score(
            job_description,
            k=k
        )
    )

    return results


def build_context(
    results
):
    """
    Convert retrieved resumes into
    context for the LLM.
    """

    context_parts = []

    for index, (
        document,
        score
    ) in enumerate(
        results,
        start=1
    ):

        resume_name = (
            document.metadata.get(
                "resume",
                "Unknown resume"
            )
        )

        context_parts.append(
            f"""
RESUME {index}

File:
{resume_name}

Resume Content:
{document.page_content}

Retrieval Distance:
{score:.4f}
"""
        )

    return "\n\n".join(
        context_parts
    )