import requests
import httpx
import json
from typing import List, Dict, Any, Optional
from ..config import config

class LMStudioClient:
    def __init__(self):
        self.chat_base_url = config.CHAT_BASE_URL
        self.embed_base_url = config.EMBED_BASE_URL
        self.chat_model = config.CHAT_MODEL
        self.embed_model = config.EMBED_MODEL
        
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: int = 2000,
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
            # Use requests instead of httpx - httpx has connection issues with LM Studio
            response = requests.post(
                f"{self.chat_base_url}/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=120
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
            raise Exception(f"Request to LM Studio timed out (120s). Try a smaller model or reduce text length.")
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
        
        # JSON schema for LM Studio (no strict mode)
        rule_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "extracted_rules",
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
                                "required": ["rule_text", "micro_class", "examples_pos", "examples_neg", "severity_cue", "regex_candidate"]
                            }
                        }
                    },
                    "required": ["rules"]
                }
            }
        }
        
        system_prompt = """You are extracting TRANSLATION RULES from a style guide written in ENGLISH that tells translators how to translate TO another language.

WHAT TO EXTRACT:
- Rules that tell translators WHAT TO DO or NOT DO (e.g., "Use full-width punctuation", "Do not translate product names", "Be concise")
- Rules about the TARGET LANGUAGE (what the translation should look like)
- Rules with words like: must, should, never, always, do not, avoid, required, recommended

WHAT NOT TO EXTRACT:
- Examples of translations (Chinese, Japanese, etc. text samples)
- Background information about the company
- Process instructions (JIRA, SharePoint, workflow)
- General context without actionable rules

RULE_TEXT MUST BE:
- Written in ENGLISH (the language of the guide)
- A clear instruction or requirement
- About HOW to translate, not WHAT was translated

EXAMPLES format should be:
- examples_pos: Small examples of CORRECT usage (if mentioned)
- examples_neg: Small examples of WRONG usage (if mentioned)
- Keep examples SHORT (under 20 characters each)

Output valid JSON:
{
  "rules": [
    {
      "rule_text": "English instruction from the guide",
      "micro_class": "Category (Punctuation, Terminology, Style, etc.)",
      "examples_pos": ["good"],
      "examples_neg": ["bad"],
      "severity_cue": "must/should/never/avoid",
      "regex_candidate": true if mechanical check possible, false otherwise
    }
  ]
}

If no actionable rules, return: {"rules": []}"""

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
        
        # JSON schema for LM Studio (no strict mode)
        findings_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "evaluation_findings",
                "schema": {
                    "type": "object",
                    "properties": {
                        "findings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rule_id": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "justification": {"type": "string"},
                                    "highlighted_text": {"type": "string"},
                                    "span_start": {"type": "integer"},
                                    "span_end": {"type": "integer"}
                                },
                                "required": ["rule_id", "severity", "justification", "highlighted_text", "span_start", "span_end"]
                            }
                        }
                    },
                    "required": ["findings"]
                }
            }
        }
        
        # Prepare candidate rules for the prompt
        rules_text = ""
        for rule in candidate_rules:
            rules_text += f"Rule ID: {rule['rule_id']}\n"
            rules_text += f"Rule: {rule['rule_text']}\n"
            rules_text += f"Examples: {rule.get('examples_pos', [])} | {rule.get('examples_neg', [])}\n\n"
        
        system_prompt = f"""You are evaluating a {locale} translation against specific rules. Be EXTREMELY precise and conservative.

CRITICAL ACCURACY CHECKS (Check these even without explicit rules):
1. TONE/MEANING: Does the translation convey the same tone and meaning as source? (exclamation vs question vs statement)
2. COMPLETENESS: Is any information missing or added?
3. TERMINOLOGY: Are brand names, product names unchanged where they should be?

EVALUATION PROCESS:
1. Read the rule carefully
2. Check if the TARGET text violates that specific rule
3. ONLY flag if you can PROVE a violation with evidence
4. DO NOT make assumptions or interpretations

COMMON MISTAKES TO AVOID:
- DNT (Do Not Translate) rules: Check if term was CHANGED or KEPT SAME. If it's KEPT (not translated), there's NO violation.
- Punctuation rules: Check EXACT punctuation marks in target
- Terminology rules: Compare actual terms used vs. required terms
- Style rules: Only flag if clearly different from requirement
- Tone changes: Exclamation (!) → Question (?) = CRITICAL accuracy issue

BE CONSERVATIVE:
- When in doubt, do NOT flag
- Only flag OBVIOUS, PROVABLE violations
- Do not add your opinions or interpretations
- Do not flag something if the rule is vague

Available Rules:
{rules_text}

Output valid JSON:
{{
  "findings": [
    {{
      "rule_id": "exact_rule_id_from_list_above",
      "severity": "Minor or Major or Critical",
      "justification": "Explain what the rule says and what you found in the target that violates it",
      "highlighted_text": "exact text from target",
      "span_start": 0,
      "span_end": 10
    }}
  ]
}}

If NO clear violations, return: {{"findings": []}}"""

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