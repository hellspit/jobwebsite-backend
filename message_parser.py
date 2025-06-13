import re
from database import db_handler

def parse_job_message(message: str) -> dict:
    """
    Parse a job message and extract relevant information
    Returns a dictionary with structured data if it's for 2026 passouts
    """
    # Check if message is for 2026 passouts
    if "2026" not in message:
        return {"is_relevant": False}

    # Extract company name
    company_match = re.search(r"Company name:\s*(.*?)(?:\n|$)", message)
    company = company_match.group(1).strip() if company_match else ""

    # Extract role
    role_match = re.search(r"Role:\s*(.*?)(?:\n|$)", message)
    role = role_match.group(1).strip() if role_match else ""

    # Extract apply link
    apply_link_match = re.search(r"Apply Link:\s*(.*?)(?:\n|$)", message)
    apply_link = apply_link_match.group(1).strip() if apply_link_match else ""

    if not all([company, role, apply_link]):
        return {"is_relevant": False}

    return {
        "is_relevant": True,
        "structured_data": {
            "company": company,
            "job": role,
            "apply_link": apply_link,
            "salary": "",  # Not provided in the message format
            "location": ""  # Not provided in the message format
        },
        "raw_analysis": message
    }

async def process_job_message(message: str) -> bool:
    """
    Process a job message and store it in the database if relevant
    Returns True if successfully stored, False otherwise
    """
    parsed_data = parse_job_message(message)
    if parsed_data["is_relevant"]:
        return await db_handler.insert_job_posting(parsed_data)
    return False 