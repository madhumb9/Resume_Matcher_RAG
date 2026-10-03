import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "local")

if os.getenv("VERCEL") == "1":
    APP_ENV = "vercel"


if APP_ENV == "vercel":

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0
    )

else:

    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=os.getenv(
            "OLLAMA_MODEL",
            "phi3:latest"
        ),
        temperature=0
    )


SYSTEM_PROMPT = """
You are a Resume Matching Assistant.

Compare the job description with
the retrieved resumes.

Use ONLY the provided information.

Do not invent skills, experience,
education, projects, companies,
or technologies.

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

JOB DESCRIPTION:

{job_description}

RETRIEVED RESUMES:

{context}
"""


def analyze_resumes(
    job_description: str,
    context: str
) :

    prompt = SYSTEM_PROMPT.format(
        job_description=job_description,
        context=context
    )

    response = llm.invoke(
        prompt
    )

    content = response.content
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif (
                isinstance(block, dict)
                and isinstance(block.get("text"), str)
                and not (
                    isinstance(block.get("extras"), dict)
                    and block["extras"].get("thought")
                )
            ):
                text_parts.append(block["text"])

        text = "\n".join(part for part in text_parts if part.strip())
        if text:
            return text

    raise ValueError("The language model returned no text content.")