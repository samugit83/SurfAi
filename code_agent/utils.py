import re

def sanitize_gpt_response(response_str: str) -> str:
    # Remove markdown indicators if present
    response_str = re.sub(r'^```json\s*', '', response_str, flags=re.MULTILINE)
    response_str = re.sub(r'```$', '', response_str, flags=re.MULTILINE)
    response_str = response_str.replace(": False", ": false")
    response_str = response_str.replace(": True", ": true")
    
    return response_str.strip()