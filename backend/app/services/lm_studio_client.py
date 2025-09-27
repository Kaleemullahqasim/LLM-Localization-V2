import requests
import httpx
import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class LMStudioClient:
    def __init__(self):
        self.chat_base_url = os.getenv("CHAT_BASE_URL", "http://localhost:1234/v1")
        self.embed_base_url = os.getenv("EMBED_BASE_URL", "http://127.0.0.1:1234/v1")
        self.chat_model = os.getenv("CHAT_MODEL", "qwen/qwen3-1.7b")
        self.embed_model = os.getenv("EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
        
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: int = 200,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a chat completion request to LM Studio"""
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        try:
            # Use requests instead of httpx for better compatibility
            response = requests.post(
                f"{self.chat_base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"LM Studio chat API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Handle reasoning_content if present (specific to some models)
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                if 'message' in choice and 'reasoning_content' in choice['message']:
                    # If there's reasoning_content but no content, use reasoning_content
                    if not choice['message'].get('content'):
                        choice['message']['content'] = choice['message']['reasoning_content']
            
            return result
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Cannot connect to LM Studio at {self.chat_base_url}. Is LM Studio running?")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Request to LM Studio timed out")
        except Exception as e:
            raise Exception(f"LM Studio chat request failed: {str(e)}")
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": self.embed_model,
                "input": texts
            }
            
            try:
                response = await client.post(
                    f"{self.embed_base_url}/embeddings",
                    headers={"Content-Type": "application/json"},
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"LM Studio embedding API error: {response.status_code} - {response.text}")
                
                result = response.json()
                return [item["embedding"] for item in result["data"]]
                
            except httpx.ConnectError as e:
                raise Exception(f"Cannot connect to LM Studio embeddings at {self.embed_base_url}. Is LM Studio running?")
            except httpx.TimeoutException as e:
                raise Exception(f"Embeddings request to LM Studio timed out")
            except Exception as e:
                raise Exception(f"LM Studio embeddings request failed: {str(e)}")
    
    async def extract_rules_from_text(self, document_snippet: str, section_path: List[str]) -> List[Dict[str, Any]]:
        """Use LLM to extract atomic rules from a document snippet"""
        
        # JSON schema for rule extraction
        rule_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "extracted_rules",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "rules": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rule_text": {"type": "string"},
                                    "micro_class": {"type": "string"},
                                    "examples_pos": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "examples_neg": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "severity_cue": {"type": "string"},
                                    "regex_candidate": {"type": "boolean"}
                                },
                                "required": ["rule_text", "micro_class", "examples_pos", "examples_neg", "severity_cue", "regex_candidate"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["rules"],
                    "additionalProperties": False
                }
            }
        }
        
        system_prompt = """You are a localization expert extracting translation quality rules from style guide documents.

Your task: Extract atomic, actionable rules from the given text snippet.

Guidelines:
1. Each rule should be ONE specific, testable requirement
2. Focus on rules with clear cues like "must", "never", "should", "avoid", "use", "don't"
3. Extract positive and negative examples when available
4. Identify if the rule could be checked with regex (punctuation, formatting, simple patterns)
5. Classify the severity cue (must/never = "Major", should/avoid = "Minor", prefer = "Minor")

Output format: JSON with extracted rules array."""

        user_prompt = f"""Document section path: {' > '.join(section_path)}

Text snippet:
{document_snippet}

Extract all actionable translation rules from this text. Focus on specific, testable requirements."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format=rule_schema
        )
        
        content = response["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
            return parsed.get("rules", [])
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            print(f"Raw content: {content}")
            return []
    
    async def evaluate_translation(
        self, 
        source_text: str, 
        target_text: str, 
        candidate_rules: List[Dict[str, Any]], 
        locale: str
    ) -> List[Dict[str, Any]]:
        """Use LLM to evaluate translation against candidate rules"""
        
        # JSON schema for evaluation findings
        findings_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "evaluation_findings",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "findings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rule_id": {"type": "string"},
                                    "severity": {"type": "string", "enum": ["Minor", "Major", "Critical"]},
                                    "justification": {"type": "string"},
                                    "highlighted_text": {"type": "string"},
                                    "span_start": {"type": "integer"},
                                    "span_end": {"type": "integer"}
                                },
                                "required": ["rule_id", "severity", "justification", "highlighted_text", "span_start", "span_end"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["findings"],
                    "additionalProperties": False
                }
            }
        }
        
        # Prepare candidate rules for the prompt
        rules_text = ""
        for rule in candidate_rules:
            rules_text += f"Rule ID: {rule['rule_id']}\n"
            rules_text += f"Rule: {rule['rule_text']}\n"
            rules_text += f"Examples: {rule.get('examples_pos', [])} | {rule.get('examples_neg', [])}\n\n"
        
        system_prompt = f"""You are a professional translation quality evaluator for {locale} locale.

Your task: Evaluate the target translation against the provided rules and identify violations.

Rules:
1. Only flag CLEAR violations of the provided rules
2. Be conservative - when in doubt, don't flag it
3. Provide specific justification for each finding
4. Use exact rule_id from the provided list
5. Identify the exact text span that violates the rule
6. Choose appropriate severity based on the rule's impact

Available Rules:
{rules_text}"""

        user_prompt = f"""Source: {source_text}
Target: {target_text}

Evaluate the target translation against the provided rules. Identify any clear violations."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.1,
            response_format=findings_schema
        )
        
        content = response["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
            return parsed.get("findings", [])
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM evaluation response: {e}")
            print(f"Raw content: {content}")
            return []