import os
import json
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import (
    ScoreReport, Finding, ScoreBreakdown, Rule, Severity, Citation,
    MacroClass
)
from .lm_studio_client import LMStudioClient
from .embedding_service import EmbeddingService
from .deterministic_validators import DeterministicValidators

class EvaluationEngine:
    """Main evaluation engine that orchestrates the scoring process"""
    
    def __init__(self):
        self.lm_client = LMStudioClient()
        self.embedding_service = EmbeddingService()
        self.validators = DeterministicValidators()
        
        # Scoring configuration
        self.severity_multipliers = {
            Severity.MINOR: 1,
            Severity.MAJOR: 2,
            Severity.CRITICAL: 3
        }
        
        self.style_punctuation_cap = 30  # Max deduction for style/punctuation
        
    async def evaluate(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str,
        kb_version: Optional[str] = None
    ) -> ScoreReport:
        """Main evaluation pipeline"""
        
        job_id = str(uuid.uuid4())
        print(f"Starting evaluation job {job_id}")
        
        # Load knowledge base
        kb = await self._load_knowledge_base(locale, kb_version)
        if not kb:
            raise Exception(f"No knowledge base found for locale {locale}")
        
        all_findings = []
        
        # Step 1: Run deterministic checks
        print("Running deterministic validators...")
        deterministic_findings = await self.validators.run_all_checks(
            source_text, target_text, locale, kb['rules']
        )
        all_findings.extend(deterministic_findings)
        print(f"Found {len(deterministic_findings)} deterministic violations")
        
        # Step 2: Hybrid retrieval for LLM evaluation
        print("Running hybrid retrieval...")
        query_text = f"Source: {source_text}\nTarget: {target_text}"
        candidate_rules = await self.embedding_service.hybrid_search(
            query_text=query_text,
            top_k=20,
            locale=locale
        )
        print(f"Retrieved {len(candidate_rules)} candidate rules")
        
        # Step 3: LLM evaluation
        if candidate_rules:
            print("Running LLM evaluation...")
            llm_findings = await self.lm_client.evaluate_translation(
                source_text=source_text,
                target_text=target_text,
                candidate_rules=[{
                    'rule_id': r['rule'].rule_id,
                    'rule_text': r['rule'].rule_text,
                    'examples_pos': r['rule'].examples_pos,
                    'examples_neg': r['rule'].examples_neg
                } for r in candidate_rules],
                locale=locale
            )
            
            # Convert LLM findings to Finding objects
            for llm_finding in llm_findings:
                # Find the matching rule
                matching_rule = None
                for candidate in candidate_rules:
                    if candidate['rule'].rule_id == llm_finding['rule_id']:
                        matching_rule = candidate['rule']
                        break
                
                if matching_rule:
                    finding = Finding(
                        segment_id=f"seg_{job_id}",
                        rule_id=llm_finding['rule_id'],
                        severity=Severity(llm_finding['severity']),
                        penalty=matching_rule.default_weight * self.severity_multipliers[Severity(llm_finding['severity'])],
                        justification=llm_finding['justification'],
                        citation=matching_rule.citation,
                        deterministic=False,
                        span_start=llm_finding.get('span_start'),
                        span_end=llm_finding.get('span_end'),
                        highlighted_text=llm_finding.get('highlighted_text')
                    )
                    all_findings.append(finding)
            
            print(f"Found {len(llm_findings)} LLM violations")
        
        # Step 4: Calculate score
        score_report = await self._calculate_score(
            job_id=job_id,
            findings=all_findings,
            kb_version=kb['kb_version'],
            rubric_version=kb['rubric_version'],
            source_text=source_text,
            target_text=target_text,
            locale=locale
        )
        
        # Step 5: Save evaluation
        await self._save_evaluation(score_report)
        
        print(f"Evaluation complete. Final score: {score_report.final_score}")
        return score_report
    
    async def _load_knowledge_base(self, locale: str, kb_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load knowledge base from disk"""
        kb_dir = "data/knowledge_bases"
        
        if not os.path.exists(kb_dir):
            return None
        
        # Find the most recent KB for locale if version not specified
        kb_files = [f for f in os.listdir(kb_dir) if f.endswith(f'_{locale}.json')]
        
        if not kb_files:
            return None
        
        if kb_version:
            target_file = f"kb_{kb_version}_{locale}.json"
            if target_file not in kb_files:
                return None
            kb_file = target_file
        else:
            # Use most recent
            kb_files.sort(reverse=True)
            kb_file = kb_files[0]
        
        try:
            with open(os.path.join(kb_dir, kb_file), 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            # Convert rule dictionaries back to Rule objects
            rules = []
            for rule_dict in kb_data['rules']:
                # Handle datetime fields
                if isinstance(rule_dict.get('created_at'), str):
                    rule_dict['created_at'] = datetime.fromisoformat(rule_dict['created_at'].replace('Z', '+00:00'))
                
                rule = Rule(**rule_dict)
                rules.append(rule)
            
            kb_data['rules'] = rules
            return kb_data
            
        except Exception as e:
            print(f"Error loading KB {kb_file}: {e}")
            return None
    
    async def _calculate_score(
        self,
        job_id: str,
        findings: List[Finding],
        kb_version: str,
        rubric_version: str,
        source_text: str,
        target_text: str,
        locale: str
    ) -> ScoreReport:
        """Calculate final score based on findings"""
        
        base_score = 100
        total_penalty = 0
        by_macro = {}
        
        # Group findings by macro class
        for finding in findings:
            # Determine macro class from rule_id or use default logic
            macro_class = self._get_macro_class_from_finding(finding)
            
            if macro_class not in by_macro:
                by_macro[macro_class] = {
                    'penalty': 0,
                    'count': 0,
                    'rules_triggered': []
                }
            
            by_macro[macro_class]['penalty'] += finding.penalty
            by_macro[macro_class]['count'] += 1
            by_macro[macro_class]['rules_triggered'].append(finding.rule_id)
            
            total_penalty += finding.penalty
        
        # Apply style/punctuation cap
        style_penalty = by_macro.get('Style', {}).get('penalty', 0)
        punctuation_penalty = by_macro.get('Punctuation', {}).get('penalty', 0)
        
        if style_penalty + punctuation_penalty > self.style_punctuation_cap:
            excess = (style_penalty + punctuation_penalty) - self.style_punctuation_cap
            total_penalty -= excess
            
            # Adjust the breakdown
            if 'Style' in by_macro:
                by_macro['Style']['penalty'] = min(by_macro['Style']['penalty'], self.style_punctuation_cap // 2)
            if 'Punctuation' in by_macro:
                by_macro['Punctuation']['penalty'] = min(by_macro['Punctuation']['penalty'], self.style_punctuation_cap // 2)
        
        final_score = max(0, base_score - total_penalty)
        
        # Convert to ScoreBreakdown objects
        score_breakdown = {}
        for macro_class, data in by_macro.items():
            score_breakdown[macro_class] = ScoreBreakdown(
                penalty=data['penalty'],
                count=data['count'],
                rules_triggered=data['rules_triggered']
            )
        
        return ScoreReport(
            job_id=job_id,
            kb_version=kb_version,
            rubric_version=rubric_version,
            model_prompt_version="1.0.0",  # MVP version
            final_score=final_score,
            findings=findings,
            by_macro=score_breakdown,
            source_text=source_text,
            target_text=target_text,
            locale=locale
        )
    
    def _get_macro_class_from_finding(self, finding: Finding) -> str:
        """Determine macro class from finding (simple logic for MVP)"""
        rule_id = finding.rule_id.upper()
        
        if 'PUNCT' in rule_id or 'EXCL' in rule_id or 'COMMA' in rule_id:
            return 'Punctuation'
        elif 'TERM' in rule_id or 'GLOSS' in rule_id:
            return 'Terminology'
        elif 'DATE' in rule_id or 'PLACEHOLDER' in rule_id or 'TAG' in rule_id:
            return 'Mechanics'
        elif 'LEGAL' in rule_id:
            return 'Legal'
        elif 'ACCURACY' in rule_id or 'MEANING' in rule_id:
            return 'Accuracy'
        else:
            return 'Style'
    
    async def _save_evaluation(self, score_report: ScoreReport):
        """Save evaluation results to disk"""
        eval_dir = "data/evaluations"
        os.makedirs(eval_dir, exist_ok=True)
        
        eval_file = os.path.join(eval_dir, f"eval_{score_report.job_id}.json")
        
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(score_report.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Evaluation saved: {eval_file}")