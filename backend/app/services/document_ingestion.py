import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
from docx import Document
import PyPDF2
from bs4 import BeautifulSoup
import markdown
import uuid

from ..models import Rule, MacroClass, Severity, Citation, KnowledgeBase
from .lm_studio_client import LMStudioClient
from .embedding_service import EmbeddingService

class DocumentIngestionService:
    """Service for ingesting style guide documents and creating rule knowledge bases"""
    
    def __init__(self):
        self.lm_client = LMStudioClient()
        self.embedding_service = EmbeddingService()
        
        # Rule cue patterns for detecting rule statements
        self.rule_cues = [
            r'\b(must|shall|required?|mandatory)\b',
            r'\b(never|not allowed|prohibited|forbidden)\b', 
            r'\b(should|recommended?|preferred?|better)\b',
            r'\b(avoid|discouraged?|not recommended)\b',
            r'\b(always|ensure|make sure)\b',
            r'\b(do not|don\'t|cannot|can\'t)\b'
        ]
        
        # Example patterns
        self.example_cues = [
            r'\b(example|e\.g\.|for instance|such as)\b',
            r'\b(correct|right|good|proper)\b:?\s*["""]',
            r'\b(incorrect|wrong|bad|improper)\b:?\s*["""]',
            r'\b(do|use)\b:?\s*["""]',
            r'\b(don\'t|avoid)\b:?\s*["""]'
        ]
        
        # Default weights by macro class
        self.default_weights = {
            MacroClass.ACCURACY: 5,
            MacroClass.TERMINOLOGY: 4,
            MacroClass.MECHANICS: 3,
            MacroClass.PUNCTUATION: 2,
            MacroClass.STYLE: 1,
            MacroClass.LEGAL: 6,
            MacroClass.STANDARDS: 3
        }
    
    async def ingest_document(self, file_path: str, locale: str) -> KnowledgeBase:
        """Main ingestion pipeline: document -> knowledge base"""
        print(f"Starting ingestion of {file_path} for locale {locale}")
        
        # Step 1: Convert to markdown with section paths
        markdown_content, section_map = await self._convert_to_markdown(file_path)
        
        # Step 2: Detect rule cues and extract candidate snippets
        candidate_snippets = self._extract_candidate_snippets(markdown_content, section_map)
        print(f"Found {len(candidate_snippets)} candidate snippets")
        
        # Step 3: Use LLM to normalize snippets into atomic rules
        raw_rules = []
        for snippet, section_path in candidate_snippets[:50]:  # Limit for MVP
            try:
                extracted = await self.lm_client.extract_rules_from_text(snippet, section_path)
                for rule_data in extracted:
                    rule_data['section_path'] = section_path
                    raw_rules.append(rule_data)
            except Exception as e:
                print(f"Error extracting rules from snippet: {e}")
                continue
        
        print(f"Extracted {len(raw_rules)} raw rules from LLM")
        
        # Step 4: Process and structure rules
        processed_rules = []
        for i, rule_data in enumerate(raw_rules):
            try:
                rule = await self._process_rule(rule_data, locale, i)
                processed_rules.append(rule)
            except Exception as e:
                print(f"Error processing rule: {e}")
                continue
        
        print(f"Successfully processed {len(processed_rules)} rules")
        
        # Step 5: Create knowledge base
        kb_version = datetime.now().strftime("%Y.%m.%d-%H%M")
        rubric_version = kb_version  # Same for MVP
        
        kb = KnowledgeBase(
            kb_version=kb_version,
            rubric_version=rubric_version,
            rules=processed_rules,
            source_document=os.path.basename(file_path),
            locale=locale,
            rule_count=len(processed_rules)
        )
        
        # Step 6: Save knowledge base and generate embeddings
        await self._save_knowledge_base(kb)
        await self.embedding_service.index_rules(processed_rules)
        
        print(f"Knowledge base created: {kb.kb_version}")
        return kb
    
    async def _convert_to_markdown(self, file_path: str) -> Tuple[str, Dict[str, List[str]]]:
        """Convert document to markdown with section mapping"""
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.docx':
            return await self._convert_docx_to_markdown(file_path)
        elif extension == '.pdf':
            return await self._convert_pdf_to_markdown(file_path)
        elif extension in ['.html', '.htm']:
            return await self._convert_html_to_markdown(file_path)
        elif extension in ['.md', '.markdown']:
            return await self._read_markdown_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    async def _convert_docx_to_markdown(self, file_path: str) -> Tuple[str, Dict[str, List[str]]]:
        """Convert DOCX to markdown with section tracking"""
        doc = Document(file_path)
        markdown_lines = []
        section_map = {}
        current_section = ["1"]
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            
            # Detect headers based on style
            if para.style.name.startswith('Heading'):
                level = int(para.style.name.split()[-1]) if para.style.name.split()[-1].isdigit() else 1
                markdown_lines.append('#' * level + ' ' + text)
                
                # Update section path  
                current_section = current_section[:level-1] + [str(len(current_section))]
                section_map[text] = current_section.copy()
            else:
                markdown_lines.append(text)
        
        return '\n'.join(markdown_lines), section_map
    
    async def _convert_pdf_to_markdown(self, file_path: str) -> Tuple[str, Dict[str, List[str]]]:
        """Convert PDF to markdown (basic text extraction)"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text_lines = []
            
            for page in reader.pages:
                text = page.extract_text()
                text_lines.extend(text.split('\n'))
        
        # Basic section detection (very simple for MVP)
        section_map = {}
        current_section = ["1"]
        
        return '\n'.join(text_lines), section_map
    
    async def _convert_html_to_markdown(self, file_path: str) -> Tuple[str, Dict[str, List[str]]]:
        """Convert HTML to markdown"""
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Simple conversion - extract text with basic structure
        markdown_lines = []
        section_map = {}
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
            if element.name.startswith('h'):
                level = int(element.name[1])
                text = element.get_text().strip()
                markdown_lines.append('#' * level + ' ' + text)
                section_map[text] = [str(level)]
            else:
                text = element.get_text().strip()
                if text:
                    markdown_lines.append(text)
        
        return '\n'.join(markdown_lines), section_map
    
    async def _read_markdown_file(self, file_path: str) -> Tuple[str, Dict[str, List[str]]]:
        """Read markdown file and extract section structure"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract headers for section mapping
        section_map = {}
        lines = content.split('\n')
        
        for line in lines:
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()
                section_map[title] = [str(level)]
        
        return content, section_map
    
    def _extract_candidate_snippets(self, markdown_content: str, section_map: Dict[str, List[str]]) -> List[Tuple[str, List[str]]]:
        """Extract text snippets that likely contain rules"""
        lines = markdown_content.split('\n')
        snippets = []
        
        current_section = ["1"]
        current_snippet = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_snippet:
                    snippets.append(('\n'.join(current_snippet), current_section.copy()))
                    current_snippet = []
                continue
            
            # Update section if this is a header
            if line.startswith('#'):
                if current_snippet:
                    snippets.append(('\n'.join(current_snippet), current_section.copy()))
                    current_snippet = []
                
                title = line.lstrip('#').strip()
                if title in section_map:
                    current_section = section_map[title]
                continue
            
            # Check if line contains rule cues
            has_rule_cue = any(re.search(pattern, line, re.IGNORECASE) for pattern in self.rule_cues)
            has_example_cue = any(re.search(pattern, line, re.IGNORECASE) for pattern in self.example_cues)
            
            if has_rule_cue or has_example_cue:
                current_snippet.append(line)
            elif current_snippet:
                # Continue building snippet if we're already in one
                current_snippet.append(line)
                
                # End snippet if it gets too long
                if len(current_snippet) > 10:
                    snippets.append(('\n'.join(current_snippet), current_section.copy()))
                    current_snippet = []
        
        # Add final snippet if exists
        if current_snippet:
            snippets.append(('\n'.join(current_snippet), current_section.copy()))
        
        return snippets
    
    async def _process_rule(self, rule_data: Dict[str, Any], locale: str, index: int) -> Rule:
        """Process raw rule data into structured Rule object"""
        
        # Generate rule ID
        rule_id = f"{locale.upper()}-{str(index).zfill(3)}-{str(uuid.uuid4())[:8].upper()}"
        
        # Classify macro class based on rule text content
        macro_class = self._classify_macro_class(rule_data['rule_text'])
        
        # Determine severity based on cues
        severity = self._determine_severity(rule_data.get('severity_cue', ''))
        
        # Get default weight for this macro class
        default_weight = self.default_weights.get(macro_class, 2)
        
        # Check if rule is regex-ready and generate pattern
        regex_ready = rule_data.get('regex_candidate', False)
        regex_pattern = None
        if regex_ready:
            regex_pattern = await self._generate_regex_pattern(rule_data['rule_text'], locale)
        
        # Create citation
        citation = Citation(
            section_path=rule_data.get('section_path', ["unknown"]),
            document_name=None  # Will be set by caller
        )
        
        return Rule(
            rule_id=rule_id,
            macro_class=macro_class,
            micro_class=rule_data['micro_class'],
            rule_text=rule_data['rule_text'],
            examples_pos=rule_data.get('examples_pos', []),
            examples_neg=rule_data.get('examples_neg', []),
            default_severity=severity,
            default_weight=default_weight,
            citation=citation,
            regex_ready=regex_ready,
            regex_pattern=regex_pattern
        )
    
    def _classify_macro_class(self, rule_text: str) -> MacroClass:
        """Classify rule into macro class based on content"""
        text_lower = rule_text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ['punctuation', 'comma', 'period', 'exclamation', 'question', '！', '。', '，']):
            return MacroClass.PUNCTUATION
        elif any(word in text_lower for word in ['terminology', 'term', 'glossary', 'translation', 'translate']):
            return MacroClass.TERMINOLOGY
        elif any(word in text_lower for word in ['format', 'date', 'number', 'placeholder', 'tag', '{', '}', '[', ']']):
            return MacroClass.MECHANICS
        elif any(word in text_lower for word in ['legal', 'compliance', 'regulation', 'law', 'rights']):
            return MacroClass.LEGAL
        elif any(word in text_lower for word in ['accuracy', 'correct', 'precise', 'exact', 'meaning']):
            return MacroClass.ACCURACY
        elif any(word in text_lower for word in ['standard', 'iso', 'specification', 'requirement']):
            return MacroClass.STANDARDS
        else:
            return MacroClass.STYLE
    
    def _determine_severity(self, severity_cue: str) -> Severity:
        """Determine severity based on linguistic cues"""
        cue_lower = severity_cue.lower()
        
        if any(word in cue_lower for word in ['must', 'never', 'required', 'mandatory', 'shall', 'critical']):
            return Severity.MAJOR
        elif any(word in cue_lower for word in ['should', 'recommended', 'preferred', 'better', 'avoid']):
            return Severity.MINOR
        else:
            return Severity.MINOR
    
    async def _generate_regex_pattern(self, rule_text: str, locale: str) -> str:
        """Generate regex pattern for mechanical rules"""
        text_lower = rule_text.lower()
        
        # Common regex patterns for localization rules
        if 'exclamation' in text_lower and locale == 'zh-CN':
            return r'[^！]!'  # Half-width exclamation in Chinese
        elif 'date' in text_lower and 'yyyy年' in text_lower:
            return r'\d{4}-\d{1,2}-\d{1,2}'  # ISO date instead of Chinese format
        elif 'placeholder' in text_lower:
            return r'\{[^}]*\}'  # Placeholder patterns
        elif 'comma' in text_lower and locale == 'zh-CN':
            return r'[^，],'  # Half-width comma in Chinese
        
        return None
    
    async def _save_knowledge_base(self, kb: KnowledgeBase):
        """Save knowledge base to disk"""
        kb_dir = os.path.join("data", "knowledge_bases")
        os.makedirs(kb_dir, exist_ok=True)
        
        # Save as JSON
        kb_file = os.path.join(kb_dir, f"kb_{kb.kb_version}_{kb.locale}.json")
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(kb.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        
        # Save points table as CSV
        csv_data = []
        for rule in kb.rules:
            csv_data.append({
                'Rule ID': rule.rule_id,
                'Macro Class': rule.macro_class.value,
                'Micro Class': rule.micro_class,
                'Rule Text': rule.rule_text,
                'Severity': rule.default_severity.value,
                'Weight': rule.default_weight,
                'Section': ' > '.join(rule.citation.section_path)
            })
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join(kb_dir, f"points_table_{kb.kb_version}_{kb.locale}.csv")
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"Knowledge base saved: {kb_file}")
        print(f"Points table saved: {csv_file}")