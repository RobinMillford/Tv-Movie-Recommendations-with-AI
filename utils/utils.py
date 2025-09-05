import re
import hashlib
from datetime import datetime

def format_runtime(minutes):
    if not minutes:
        return "N/A"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m" if hours > 0 else f"{remaining_minutes}m"

def format_currency(amount):
    if not amount:
        return "N/A"
    return f"{amount:,}"

def clean_json_response(content):
    """Clean JSON content from markdown code blocks and other formatting"""
    # Check for ``` tags and extract any JSON found within
    if "```" in content and "```" in content:
        # Try to find JSON within the think tags
        think_content = content.split("```")[-1].strip()
        if think_content.startswith("```json") or think_content.startswith("```"):
            content = think_content
        elif "{" in think_content and "}" in think_content:
            # Extract just the JSON part
            json_start = think_content.find("{")
            json_end = think_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                content = think_content[json_start:json_end]
    
    # Remove markdown code block syntax if present
    if content.startswith("```") and content.endswith("```"):
        # Remove the first and last line (code block markers)
        content = "\n".join(content.split("\n")[1:-1])
    elif content.startswith("```json") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1])
    
    # For cases where just the pattern ```json or ``` is present without proper formatting
    content = content.strip().replace("```json", "").replace("```", "").strip()
    
    return content