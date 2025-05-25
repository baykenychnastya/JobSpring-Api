import json

from app.groq import setup_qa_system
from app.pdf_loader import load_pdf_from_url, split_documents

docs = load_pdf_from_url("https://...")
print(f"Number of documents loaded: {len(docs)}")
chunks = split_documents(docs, chunk_size=800)
qa_system = setup_qa_system(chunks)

query =  """
    You are an AI assistant that reads resumes/CVs and extracts structured information.
    Based on the context provided, extract all relevant details about the candidate and return them in the following JSON format:

    {
        "full_name": "",
        "contact": {
            "email": "",
            "phone": "",
            "linkedin": "",
            "location": ""
        },
        "summary": "",
        "skills": [],
        "languages": [],
        "education": [
            {
            "degree": "",
            "field": "",
            "institution": "",
            "start_year": "",
            "end_year": ""
            }
        ],
        "experience": [
            {
            "job_title": "",
            "company": "",
            "location": "",
            "start_date": "",
            "end_date": "",
            "description": ""
            }
        ],
        "certifications": [],
        "projects": [
            {
            "title": "",
            "description": ""
            }
        ]
    }
    Respond only with a valid JSON object. If information is missing, return empty strings or empty lists as appropriate. 
    Use your best judgment to normalize inconsistent date formats and job titles.
"""

result = qa_system.invoke({"query": query})
parsed_result = json.loads(result['result'])
answer = parsed_result['answer']
sources = parsed_result['sources']

print(f"Answer: {answer}")
print(f"Sources: {sources}")