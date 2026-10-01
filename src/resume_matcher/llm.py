import os

from dotenv import load_dotenv

from langchain_ollama import ChatOllama


load_dotenv()


MODEL = os.getenv(
    "OLLAMA_MODEL",
    "phi3:latest"
)


llm = ChatOllama(
    model=MODEL,
    temperature=0
)


SYSTEM_PROMPT = """
You are a Resume Matching Assistant.

Compare the job description with the
retrieved resumes.

Use ONLY the provided information.

Do not invent:

- skills
- experience
- education
- projects
- companies
- technologies

For each resume:

1. Resume file name
2. Relevant matching skills
3. Missing or unclear requirements
4. Short match analysis

Then rank the retrieved resumes from
strongest textual match to weakest
textual match.

Do not claim that a candidate will
definitely get the job.

Do not invent a percentage match score.

Keep the response concise.

JOB DESCRIPTION:

{job_description}

RETRIEVED RESUMES:

{context}
"""


def analyze_resumes(
    job_description: str,
    context: str
) -> str:

    prompt = SYSTEM_PROMPT.format(
        job_description=job_description,
        context=context
    )

    response = llm.invoke(
        prompt
    )

    return response.content