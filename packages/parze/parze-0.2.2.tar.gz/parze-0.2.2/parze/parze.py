"""
Parze Python SDK
A simple client for interacting with the Parze API.
"""

import requests
import json
from typing import Union, BinaryIO

class ParzeClient:
    def __init__(self, api_key: str, base_url: str = "https://api.parze.ai"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def parse(self, file: Union[str, BinaryIO], 
              output_format: str = "structured",
              preserve_tables: bool = True,
              preserve_layout: bool = True,
              extraction_mode: str = "auto") -> dict:
        """Parse document into structured text."""
        url = f"{self.base_url}/api/parse"
        
        if isinstance(file, str):
            with open(file, 'rb') as f:
                files = {'file': f}
                data = {
                    'output_format': output_format,
                    'preserve_tables': str(preserve_tables).lower(),
                    'preserve_layout': str(preserve_layout).lower(),
                    'extraction_mode': extraction_mode
                }
                response = requests.post(url, files=files, data=data, headers=self.headers)
        else:
            files = {'file': file}
            data = {
                'output_format': output_format,
                'preserve_tables': str(preserve_tables).lower(),
                'preserve_layout': str(preserve_layout).lower(),
                'extraction_mode': extraction_mode
            }
            response = requests.post(url, files=files, data=data, headers=self.headers)
        
        response.raise_for_status()
        return response.json()

    def extract(self, text: str = None, extraction_schema: dict = None, job_id: str = None, file: Union[str, BinaryIO] = None) -> dict:
        """Extract structured data from a file or parsed text using schema."""
        url = f"{self.base_url}/api/extract"
        
        if file is not None:
            if not extraction_schema:
                raise ValueError("extraction_schema is required")
            if isinstance(file, str):
                with open(file, 'rb') as f:
                    files = {'file': f}
                    data = {'extraction_schema': json.dumps(extraction_schema)}
                    response = requests.post(url, files=files, data=data, headers=self.headers)
            else:
                files = {'file': file}
                data = {'extraction_schema': json.dumps(extraction_schema)}
                response = requests.post(url, files=files, data=data, headers=self.headers)
        else:
            if not text or not extraction_schema or not job_id:
                raise ValueError("text, extraction_schema, and job_id are required when file is not provided")
            headers = {**self.headers, "Content-Type": "application/json"}
            payload = {"text": text, "extraction_schema": extraction_schema, "job_id": job_id}
            response = requests.post(url, json=payload, headers=headers)
        
        response.raise_for_status()
        return response.json()

    def suggest_schema(self, text: str) -> dict:
        """Get AI-suggested schema based on text."""
        url = f"{self.base_url}/api/suggest-schema"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, json={"text": text}, headers=headers)
        response.raise_for_status()
        return response.json()

    def text_to_schema(self, description: str) -> dict:
        """Convert natural language to extraction schema."""
        url = f"{self.base_url}/api/text-to-schema"
        headers = {**self.headers, "Content-Type": "application/json"}
        response = requests.post(url, json={"text": description}, headers=headers)
        response.raise_for_status()
        return response.json()
