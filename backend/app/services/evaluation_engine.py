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
from ..config import config
from .lm_studio_client import LMStudioClient
from .embedding_service import EmbeddingService
from .deterministic_validators import DeterministicValidators

class EvaluationEngine:
    """Main evaluation engine that orchestrates the scoring process"""
    
    def __init__(self):
        self.lm_client = LMStudioClient()
        self.embedding_service = EmbeddingService()
        self.validators = DeterministicValidators()
        
        # Scoring configuration from centralized config
        self.severity_multipliers = {
            Severity.MINOR: config.SEVERITY_MULTIPLIER_MINOR,
            Severity.MAJOR: config.SEVERITY_MULTIPLIER_MAJOR,
            Severity.CRITICAL: config.SEVERITY_MULTIPLIER_CRITICAL
        }
        
        self.style_punctuation_cap = config.STYLE_PUNCTUATION_CAP
        
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
        
        # Step 2: General translation quality evaluation (NEW!)
        print("Running translation quality assessment...")
        quality_findings = await self.lm_client.evaluate_translation_quality(
            source_text=source_text,
            target_text=target_text,
            locale=locale
        )
        
        # Convert quality findings to Finding objects
        for quality_finding in quality_findings:
            # Create synthetic rule_id based on issue type
            issue_type = quality_finding['issue_type']
            synthetic_rule_id = f"QUALITY_{issue_type.upper()}"
            
            # Map issue types to macro classes
            macro_class_map = {
                'script_mixing': 'Accuracy',
                'accuracy_error': 'Accuracy',
                'completeness_error': 'Accuracy',
                'grammar_error': 'Accuracy',
                'terminology_error': 'Terminology',
                'professionalism_error': 'Style'
            }
            
            # Create a synthetic citation for quality issues
            synthetic_citation = Citation(
                section_path=["General Translation Quality", f"{issue_type.replace('_', ' ').title()}"],
                document_name="Professional Translation Standards"
            )
            
            # Quality issues have higher default weights since they're fundamental errors
            severity = Severity(quality_finding['severity'])
            base_weight = 15  # Higher than style guide rules (which are typically 3-8)
            penalty = base_weight * self.severity_multipliers[severity]
            
            finding = Finding(
                segment_id=f"seg_{job_id}",
                rule_id=synthetic_rule_id,
                severity=severity,
                penalty=penalty,
                justification=quality_finding['justification'],
                citation=synthetic_citation,
                deterministic=False,
                span_start=quality_finding.get('span_start'),
                span_end=quality_finding.get('span_end'),
                highlighted_text=quality_finding.get('highlighted_text')
            )
            all_findings.append(finding)
        
        print(f"Found {len(quality_findings)} quality issues")
        
        # Step 3: Hybrid retrieval for style guide evaluation
        print("Running hybrid retrieval...")
        query_text = f"Source: {source_text}\nTarget: {target_text}"
        candidate_rules = await self.embedding_service.hybrid_search(
            query_text=query_text,
            top_k=20,
            locale=locale,
            kb_version=kb['kb_version']
        )
        print(f"Retrieved {len(candidate_rules)} candidate rules")
        
        # Step 4: Style guide rule evaluation
        if candidate_rules:
            print("Running style guide compliance check...")
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
            
            print(f"Found {len(llm_findings)} style guide violations")
        
        # Step 5: Calculate score
        score_report = await self._calculate_score(
            job_id=job_id,
            findings=all_findings,
            kb=kb,
            source_text=source_text,
            target_text=target_text,
            locale=locale
        )
        
        # Step 6: Save evaluation
        await self._save_evaluation(score_report)
        
        print(f"Evaluation complete. Final score: {score_report.final_score}")
        return score_report
    
    async def _load_knowledge_base(self, locale: str, kb_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load knowledge base from disk"""
        kb_dir = os.path.join(config.DATA_DIR, "knowledge_bases")
        
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
                
                # Convert string enums back to enum objects
                if isinstance(rule_dict.get('macro_class'), str):
                    rule_dict['macro_class'] = MacroClass(rule_dict['macro_class'])
                
                if isinstance(rule_dict.get('default_severity'), str):
                    rule_dict['default_severity'] = Severity(rule_dict['default_severity'])
                
                # Convert citation dict back to Citation object
                if isinstance(rule_dict.get('citation'), dict):
                    rule_dict['citation'] = Citation(**rule_dict['citation'])
                
                rule = Rule(**rule_dict)
                rules.append(rule)
            
            kb_data['rules'] = rules
            return kb_data
            
        except Exception as e:
            print(f"Error loading KB {kb_file}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _calculate_score(
        self,
        job_id: str,
        findings: List[Finding],
        kb: Dict[str, Any],
        source_text: str,
        target_text: str,
        locale: str
    ) -> ScoreReport:
        """Calculate final score based on findings"""
        
        base_score = 100
        total_penalty = 0
        by_macro = {}
        
        # Build rule lookup for macro class mapping
        rule_lookup = {rule.rule_id: rule for rule in kb['rules']}
        
        # Group findings by macro class
        for finding in findings:
            # Get macro class from the actual rule object
            rule = rule_lookup.get(finding.rule_id)
            if rule:
                macro_class = rule.macro_class.value
            else:
                # Fallback to heuristic if rule not found
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
            kb_version=kb['kb_version'],
            rubric_version=kb['rubric_version'],
            model_prompt_version=config.MODEL_PROMPT_VERSION,
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
        
        # Handle quality-based findings
        if rule_id.startswith('QUALITY_'):
            if 'SCRIPT_MIXING' in rule_id or 'ACCURACY_ERROR' in rule_id or 'COMPLETENESS_ERROR' in rule_id or 'GRAMMAR_ERROR' in rule_id:
                return 'Accuracy'
            elif 'TERMINOLOGY_ERROR' in rule_id:
                return 'Terminology'
            elif 'PROFESSIONALISM_ERROR' in rule_id:
                return 'Style'
            else:
                return 'Accuracy'  # Default for quality issues
        
        # Handle style guide rule findings
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
        eval_dir = os.path.join(config.DATA_DIR, "evaluations")
        os.makedirs(eval_dir, exist_ok=True)
        
        eval_file = os.path.join(eval_dir, f"eval_{score_report.job_id}.json")
        
        with open(eval_file, 'w', encoding='utf-8') as f:
            json.dump(score_report.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Evaluation saved: {eval_file}")