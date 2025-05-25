import json
from app.groq import setup_qa_system
from app.pdf_loader import load_pdf_from_url, split_documents

CV_PROMPT_TEMPLATE = """
You are an AI assistant that reviews resumes (CVs) and evaluates their suitability for a job.

Your task is to:
- Extract structured candidate information from the provided CV.
- Compare this data against the provided job description.
- Return both the structured candidate data and a final recommendation on whether to move forward.

Job Description:
{job_description}

Return the following JSON structure:

{{
    "full_name": "",
    "contact": {{
        "email": "",
        "phone": "",
        "linkedin": "",
        "location": ""
    }},
    "summary": "",
    "skills": [],
    "languages": [],
    "education": [
        {{
            "degree": "",
            "field": "",
            "institution": "",
            "start_year": "",
            "end_year": ""
        }}
    ],
    "experience": [
        {{
            "job_title": "",
            "company": "",
            "location": "",
            "start_date": "",
            "end_date": "",
            "description": ""
        }}
    ],
    "certifications": [],
    "projects": [
        {{
            "title": "",
            "description": ""
        }}
    ],
    "priority": "recommended" | "highly-recommended" | "not-recommended",
    "priority_description": "Explain in 2-4 sentences why this candidate is classified as such. This text will be sent directly to the candidate as feedback."
}}

If any section is missing in the CV, use empty strings or empty lists.
Normalize inconsistent date formats and job titles. Use your best judgment.

Respond with a valid JSON object only.
"""

def proces_cv(file_url: str, job_description: str):
    docs = load_pdf_from_url(file_url)
    print(f"Number of documents loaded: {len(docs)}")
    chunks = split_documents(docs, chunk_size=800)
    qa_system = setup_qa_system(chunks)

    filled_prompt = CV_PROMPT_TEMPLATE.format(job_description=job_description)

    result = qa_system.invoke({"query": filled_prompt})
    parsed_result = json.loads(result['result'])

    return parsed_result
