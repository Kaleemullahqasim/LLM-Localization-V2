import re
import json
from typing import List, Dict, Any, Set
from ..models import Finding, Rule, Severity, Citation

class DeterministicValidators:
    """Deterministic validators for mechanical translation rules"""
    
    def __init__(self):
        # Chinese punctuation mappings
        self.zh_punctuation_map = {
            '!': '！',    # Exclamation
            ',': '，',    # Comma  
            ':': '：',    # Colon
            ';': '；',    # Semicolon
            '?': '？',    # Question mark
            '"': '"',     # Opening quote
            '"': '"',     # Closing quote
            '(': '（',    # Opening parenthesis
            ')': '）',    # Closing parenthesis
            '<': '《',    # Opening bracket
            '>': '》',    # Closing bracket
        }
        
        # Common placeholder patterns
        self.placeholder_patterns = [
            r'\{[^}]*\}',     # {placeholder}
            r'\[[^\]]*\]',    # [placeholder]
            r'<[^>]*>',       # <placeholder>
            r'%[sd]',         # %s, %d format specifiers
            r'%\(\w+\)[sd]',  # %(name)s format specifiers
        ]
        
        # Chinese date format pattern
        self.zh_date_pattern = r'\d{4}年\d{1,2}月\d{1,2}日'
        self.iso_date_pattern = r'\d{4}-\d{1,2}-\d{1,2}'
    
    async def run_all_checks(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        rules: List[Rule]
    ) -> List[Finding]:
        """Run all deterministic checks and return findings"""
        
        findings = []
        segment_id = "seg_" + str(hash(target_text))[:8]
        
        # Extract regex-ready rules
        regex_rules = [rule for rule in rules if rule.regex_ready and rule.regex_pattern]
        
        # Run checks
        findings.extend(await self._check_punctuation_width(source_text, target_text, locale, segment_id, rules))
        findings.extend(await self._check_placeholders(source_text, target_text, locale, segment_id, rules))
        findings.extend(await self._check_date_format(source_text, target_text, locale, segment_id, rules))
        findings.extend(await self._check_line_breaks(source_text, target_text, locale, segment_id, rules))
        findings.extend(await self._check_regex_rules(source_text, target_text, locale, segment_id, regex_rules))
        
        return findings
    
    async def _check_punctuation_width(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        segment_id: str,
        rules: List[Rule]
    ) -> List[Finding]:
        """Check for correct punctuation width (full-width vs half-width)"""
        
        findings = []
        
        if locale != 'zh-CN':
            return findings
        
        # Find relevant punctuation rules
        punct_rules = [
            rule for rule in rules 
            if rule.macro_class.value == 'Punctuation' and 'width' in rule.rule_text.lower()
        ]
        
        for half_width, full_width in self.zh_punctuation_map.items():
            if half_width in target_text:
                # Find positions of half-width punctuation
                positions = []
                for match in re.finditer(re.escape(half_width), target_text):
                    positions.append((match.start(), match.end()))
                
                if positions:
                    # Find matching rule
                    matching_rule = None
                    for rule in punct_rules:
                        if half_width in rule.rule_text or full_width in rule.rule_text:
                            matching_rule = rule
                            break
                    
                    if not matching_rule and punct_rules:
                        matching_rule = punct_rules[0]  # Use first punctuation rule as fallback
                    
                    if matching_rule:
                        for start_pos, end_pos in positions:
                            finding = Finding(
                                segment_id=segment_id,
                                rule_id=matching_rule.rule_id,
                                severity=matching_rule.default_severity,
                                penalty=matching_rule.default_weight * 2,  # Major severity multiplier
                                justification=f"Half-width '{half_width}' found; should use full-width '{full_width}' in Chinese.",
                                citation=matching_rule.citation,
                                deterministic=True,
                                span_start=start_pos,
                                span_end=end_pos,
                                highlighted_text=half_width
                            )
                            findings.append(finding)
        
        return findings
    
    async def _check_placeholders(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        segment_id: str,
        rules: List[Rule]
    ) -> List[Finding]:
        """Check that placeholders are preserved correctly"""
        
        findings = []
        
        # Find placeholder rules
        placeholder_rules = [
            rule for rule in rules 
            if 'placeholder' in rule.rule_text.lower() or 'tag' in rule.rule_text.lower()
        ]
        
        if not placeholder_rules:
            return findings
        
        # Extract placeholders from source and target
        source_placeholders = set()
        target_placeholders = set()
        
        for pattern in self.placeholder_patterns:
            source_matches = re.findall(pattern, source_text)
            target_matches = re.findall(pattern, target_text)
            
            source_placeholders.update(source_matches)
            target_placeholders.update(target_matches)
        
        # Check for missing or modified placeholders
        missing_placeholders = source_placeholders - target_placeholders
        extra_placeholders = target_placeholders - source_placeholders
        
        rule = placeholder_rules[0]  # Use first placeholder rule
        
        # Report missing placeholders
        for placeholder in missing_placeholders:
            finding = Finding(
                segment_id=segment_id,
                rule_id=rule.rule_id,
                severity=Severity.MAJOR,
                penalty=rule.default_weight * 2,
                justification=f"Placeholder '{placeholder}' from source is missing in target.",
                citation=rule.citation,
                deterministic=True,
                highlighted_text=placeholder
            )
            findings.append(finding)
        
        # Report extra/modified placeholders
        for placeholder in extra_placeholders:
            if placeholder not in source_placeholders:
                finding = Finding(
                    segment_id=segment_id,
                    rule_id=rule.rule_id,
                    severity=Severity.MAJOR,
                    penalty=rule.default_weight * 2,
                    justification=f"Placeholder '{placeholder}' in target does not match source placeholders.",
                    citation=rule.citation,
                    deterministic=True,
                    highlighted_text=placeholder
                )
                findings.append(finding)
        
        return findings
    
    async def _check_date_format(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        segment_id: str,
        rules: List[Rule]
    ) -> List[Finding]:
        """Check for proper date format in Chinese locale"""
        
        findings = []
        
        if locale != 'zh-CN':
            return findings
        
        # Find date format rules
        date_rules = [
            rule for rule in rules 
            if 'date' in rule.rule_text.lower() and ('年' in rule.rule_text or 'format' in rule.rule_text.lower())
        ]
        
        if not date_rules:
            return findings
        
        # Check for ISO dates in Chinese text (should be Chinese format)
        iso_dates = re.findall(self.iso_date_pattern, target_text)
        
        if iso_dates:
            rule = date_rules[0]
            
            for iso_date in iso_dates:
                # Find position in text
                match = re.search(re.escape(iso_date), target_text)
                if match:
                    finding = Finding(
                        segment_id=segment_id,
                        rule_id=rule.rule_id,
                        severity=rule.default_severity,
                        penalty=rule.default_weight * 2,
                        justification=f"ISO date format '{iso_date}' found; should use Chinese format (YYYY年M月D日).",
                        citation=rule.citation,
                        deterministic=True,
                        span_start=match.start(),
                        span_end=match.end(),
                        highlighted_text=iso_date
                    )
                    findings.append(finding)
        
        return findings
    
    async def _check_line_breaks(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        segment_id: str,
        rules: List[Rule]
    ) -> List[Finding]:
        """Check that line breaks are preserved"""
        
        findings = []
        
        # Find line break rules
        linebreak_rules = [
            rule for rule in rules 
            if 'line break' in rule.rule_text.lower() or 'formatting' in rule.rule_text.lower()
        ]
        
        if not linebreak_rules:
            return findings
        
        source_breaks = source_text.count('\n')
        target_breaks = target_text.count('\n')
        
        # Allow some tolerance for formatting differences
        if abs(source_breaks - target_breaks) > 2:
            rule = linebreak_rules[0]
            
            finding = Finding(
                segment_id=segment_id,
                rule_id=rule.rule_id,
                severity=Severity.MINOR,
                penalty=rule.default_weight * 1,  # Minor severity
                justification=f"Line break count mismatch: source has {source_breaks}, target has {target_breaks}.",
                citation=rule.citation,
                deterministic=True
            )
            findings.append(finding)
        
        return findings
    
    async def _check_regex_rules(
        self, 
        source_text: str, 
        target_text: str, 
        locale: str, 
        segment_id: str,
        regex_rules: List[Rule]
    ) -> List[Finding]:
        """Check rules that have regex patterns"""
        
        findings = []
        
        for rule in regex_rules:
            if not rule.regex_pattern:
                continue
            
            try:
                matches = list(re.finditer(rule.regex_pattern, target_text))
                
                if matches:
                    for match in matches:
                        finding = Finding(
                            segment_id=segment_id,
                            rule_id=rule.rule_id,
                            severity=rule.default_severity,
                            penalty=rule.default_weight * 2,  # Default to major
                            justification=f"Regex pattern violation: {rule.rule_text}",
                            citation=rule.citation,
                            deterministic=True,
                            span_start=match.start(),
                            span_end=match.end(),
                            highlighted_text=match.group()
                        )
                        findings.append(finding)
                        
            except re.error as e:
                print(f"Invalid regex pattern in rule {rule.rule_id}: {e}")
                continue
        
        return findings
    
    async def check_glossary_terms(
        self, 
        source_text: str, 
        target_text: str, 
        glossary: Dict[str, str],
        segment_id: str,
        rule: Rule
    ) -> List[Finding]:
        """Check glossary/DNT terms (placeholder for future implementation)"""
        
        findings = []
        
        # This would check against a glossary/DNT list
        # For MVP, we'll implement a simple version
        
        for source_term, expected_translation in glossary.items():
            if source_term.lower() in source_text.lower():
                if expected_translation.lower() not in target_text.lower():
                    finding = Finding(
                        segment_id=segment_id,
                        rule_id=rule.rule_id,
                        severity=Severity.MAJOR,
                        penalty=rule.default_weight * 2,
                        justification=f"Glossary term '{source_term}' should be translated as '{expected_translation}'.",
                        citation=rule.citation,
                        deterministic=True,
                        highlighted_text=source_term
                    )
                    findings.append(finding)
        
        return findings