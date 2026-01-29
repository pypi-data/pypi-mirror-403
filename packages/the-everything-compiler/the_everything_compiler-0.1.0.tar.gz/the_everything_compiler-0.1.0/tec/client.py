#
# The Everything Compiler
# Licensed under the MIT License
# (check LICENSE.TXT for details.)
#
# tec/client.py
#

import os
import sys
from google import genai
from google.genai import types, errors
from openai import OpenAI, OpenAIError

def _get_client(service: str, api_key: str):
    if not api_key:
        raise ValueError(f"API Key is required for {service} service. Please set TEC_API_KEY env var or configure tec.toml")
    
    if service == "google":
        return genai.Client(api_key=api_key)
    elif service == "openai":
        return OpenAI(api_key=api_key)
    else:
        raise ValueError(f"Unknown service: {service}")

def _clean_response(text: str) -> str:
    """Removes markdown code blocks from the response."""
    lines = text.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()

def generate_c_code(context_xml: str, instructions: str, ai_config) -> str:
    """Sends the XML to the LLM and returns specific C code."""
    client = _get_client(ai_config.service, ai_config.api_key)
    
    prompt = f"{instructions}\n\n{context_xml}"
    
    try:
        if ai_config.service == "google":
            response = client.models.generate_content(
                model=ai_config.model,
                contents=prompt
            )
            text = response.text
        elif ai_config.service == "openai":
            response = client.chat.completions.create(
                model=ai_config.model,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": context_xml}
                ]
            )
            text = response.choices[0].message.content
        else:
             raise NotImplementedError(f"Service '{ai_config.service}' not yet implemented.")
        
        if not text:
             return "// Error: No response from AI"

        return _clean_response(text)
    except (errors.ServerError, OpenAIError) as e:
        print(f"[!] AI Service Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
        sys.exit(1)

def fix_c_code(original_code: str, error_message: str, instructions: str, ai_config) -> str:
    """Sends the code and error to the LLM to request a fix."""
    client = _get_client(ai_config.service, ai_config.api_key)

    prompt = f"""
{instructions}

The following C code failed to compile:
```c
{original_code}
```

Error Message:
{error_message}

Please fix the code. Return ONLY the fixed C code.
"""
    try:
        text = ""
        if ai_config.service == "google":
            response = client.models.generate_content(
                model=ai_config.model,
                contents=prompt
            )
            text = response.text
        elif ai_config.service == "openai":
            response = client.chat.completions.create(
                model=ai_config.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            text = response.choices[0].message.content
        else:
             raise NotImplementedError(f"Service '{ai_config.service}' not yet implemented.")

        if not text:
             return original_code # Failed to fix

        return _clean_response(text)
    except (errors.ServerError, OpenAIError) as e:
        print(f"[!] AI Service Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected Error: {e}")
        sys.exit(1)