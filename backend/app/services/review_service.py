import os
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

from ..models import (
    ReviewOverrideRequest, FeedbackEvent, FeedbackAction, 
    ScoreReport, Finding, Severity
)

class ReviewService:
    """Service for handling reviewer overrides and feedback"""
    
    def __init__(self):
        self.feedback_dir = "data/feedback"
        os.makedirs(self.feedback_dir, exist_ok=True)
    
    async def process_override(self, request: ReviewOverrideRequest) -> FeedbackEvent:
        """Process a reviewer override and update the evaluation"""
        
        # Load the evaluation containing this finding
        evaluation = await self._find_evaluation_by_finding(request.finding_id)
        if not evaluation:
            raise Exception(f"Evaluation not found for finding {request.finding_id}")
        
        # Find the specific finding
        finding = None
        for f in evaluation['findings']:
            if f.get('segment_id') == request.finding_id or f.get('rule_id') == request.finding_id:
                finding = f
                break
        
        if not finding:
            raise Exception(f"Finding {request.finding_id} not found in evaluation")
        
        # Create feedback event
        event_id = str(uuid.uuid4())
        
        old_value = finding.get('severity', 'Unknown')
        new_value = old_value
        
        if request.action == FeedbackAction.CHANGE_SEVERITY and request.new_severity:
            new_value = request.new_severity.value
            # Update the finding
            finding['severity'] = request.new_severity.value
            # Recalculate penalty
            severity_multipliers = {
                'Minor': 1,
                'Major': 2, 
                'Critical': 3
            }
            # Assume default weight is stored or can be derived
            base_weight = finding.get('penalty', 2) // severity_multipliers.get(old_value, 2)
            finding['penalty'] = base_weight * severity_multipliers.get(new_value, 2)
        
        elif request.action == FeedbackAction.DISMISS:
            finding['dismissed'] = True
            finding['penalty'] = 0
            new_value = 'Dismissed'
        
        elif request.action == FeedbackAction.ACCEPT:
            finding['accepted'] = True
            new_value = 'Accepted'
        
        feedback_event = FeedbackEvent(
            event_id=event_id,
            segment_id=finding.get('segment_id', request.finding_id),
            rule_id=finding.get('rule_id', 'unknown'),
            action=request.action,
            old_value=old_value,
            new_value=new_value,
            reason=request.reason,
            actor=request.reviewer
        )
        
        # Recalculate score
        await self._recalculate_score(evaluation)
        
        # Save updated evaluation
        await self._save_evaluation(evaluation)
        
        # Save feedback event
        await self._save_feedback_event(feedback_event)
        
        return feedback_event
    
    async def _find_evaluation_by_finding(self, finding_id: str) -> Dict[str, Any]:
        """Find evaluation that contains the specified finding"""
        
        eval_dir = "data/evaluations"
        if not os.path.exists(eval_dir):
            return None
        
        eval_files = [f for f in os.listdir(eval_dir) if f.endswith('.json')]
        
        for eval_file in eval_files:
            try:
                with open(os.path.join(eval_dir, eval_file), 'r', encoding='utf-8') as f:
                    evaluation = json.load(f)
                
                # Check if this evaluation contains the finding
                for finding in evaluation.get('findings', []):
                    if (finding.get('segment_id') == finding_id or 
                        finding.get('rule_id') == finding_id):
                        evaluation['_file_path'] = os.path.join(eval_dir, eval_file)
                        return evaluation
                        
            except Exception as e:
                print(f"Error reading evaluation file {eval_file}: {e}")
                continue
        
        return None
    
    async def _recalculate_score(self, evaluation: Dict[str, Any]):
        """Recalculate the score after overrides"""
        
        findings = evaluation.get('findings', [])
        base_score = 100
        total_penalty = 0
        by_macro = {}
        
        # Recalculate based on current finding states
        for finding in findings:
            # Skip dismissed findings
            if finding.get('dismissed', False):
                continue
            
            penalty = finding.get('penalty', 0)
            total_penalty += penalty
            
            # Update macro breakdown
            macro_class = self._determine_macro_class(finding.get('rule_id', ''))
            
            if macro_class not in by_macro:
                by_macro[macro_class] = {'penalty': 0, 'count': 0, 'rules_triggered': []}
            
            by_macro[macro_class]['penalty'] += penalty
            by_macro[macro_class]['count'] += 1
            by_macro[macro_class]['rules_triggered'].append(finding.get('rule_id', ''))
        
        # Apply style/punctuation cap (30 points max)
        style_penalty = by_macro.get('Style', {}).get('penalty', 0)
        punctuation_penalty = by_macro.get('Punctuation', {}).get('penalty', 0)
        
        if style_penalty + punctuation_penalty > 30:
            excess = (style_penalty + punctuation_penalty) - 30
            total_penalty -= excess
            
            # Adjust breakdown
            if 'Style' in by_macro:
                by_macro['Style']['penalty'] = min(by_macro['Style']['penalty'], 15)
            if 'Punctuation' in by_macro:
                by_macro['Punctuation']['penalty'] = min(by_macro['Punctuation']['penalty'], 15)
        
        final_score = max(0, base_score - total_penalty)
        
        # Update evaluation
        evaluation['final_score'] = final_score
        evaluation['by_macro'] = by_macro
        evaluation['last_updated'] = datetime.utcnow().isoformat()
    
    def _determine_macro_class(self, rule_id: str) -> str:
        """Determine macro class from rule ID"""
        rule_id = rule_id.upper()
        
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
    
    async def _save_evaluation(self, evaluation: Dict[str, Any]):
        """Save updated evaluation back to disk"""
        
        file_path = evaluation.get('_file_path')
        if not file_path:
            # Create new file
            eval_dir = "data/evaluations"
            job_id = evaluation.get('job_id', str(uuid.uuid4()))
            file_path = os.path.join(eval_dir, f"eval_{job_id}.json")
        
        # Remove internal fields
        eval_copy = evaluation.copy()
        eval_copy.pop('_file_path', None)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(eval_copy, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving evaluation: {e}")
            raise
    
    async def _save_feedback_event(self, feedback_event: FeedbackEvent):
        """Save feedback event to disk"""
        
        feedback_file = os.path.join(
            self.feedback_dir, 
            f"feedback_{feedback_event.event_id}.json"
        )
        
        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_event.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving feedback event: {e}")
            raise
    
    async def get_feedback_history(self, segment_id: str = None, rule_id: str = None) -> List[FeedbackEvent]:
        """Get feedback history for a segment or rule"""
        
        if not os.path.exists(self.feedback_dir):
            return []
        
        feedback_files = [f for f in os.listdir(self.feedback_dir) if f.endswith('.json')]
        feedback_events = []
        
        for feedback_file in feedback_files:
            try:
                with open(os.path.join(self.feedback_dir, feedback_file), 'r', encoding='utf-8') as f:
                    event_data = json.load(f)
                
                # Filter by segment_id or rule_id if provided
                if segment_id and event_data.get('segment_id') != segment_id:
                    continue
                if rule_id and event_data.get('rule_id') != rule_id:
                    continue
                
                # Convert back to FeedbackEvent object
                if isinstance(event_data.get('created_at'), str):
                    event_data['created_at'] = datetime.fromisoformat(event_data['created_at'].replace('Z', '+00:00'))
                
                feedback_event = FeedbackEvent(**event_data)
                feedback_events.append(feedback_event)
                
            except Exception as e:
                print(f"Error reading feedback file {feedback_file}: {e}")
                continue
        
        # Sort by creation time
        feedback_events.sort(key=lambda x: x.created_at, reverse=True)
        return feedback_events