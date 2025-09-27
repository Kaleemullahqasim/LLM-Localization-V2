PRD — MVP: Rule-Anchored Localization QA System

0. One-liner

A system that ingests official style guides to automatically create a rule knowledge base (KB) with error classes, severities, and weights.
It then uses this KB to evaluate translations with explainable scoring, and lets reviewers audit, override, and record feedback.

⸻

1. Users & Roles
	•	Admin (Uploader): Uploads style guides; system builds KB; approves KB versions.
	•	Test Taker (Translator): Submits translation; system auto-scores against KB.
	•	Reviewer (QA/LS): Reviews system’s scoring, sees justifications with citations; can override and log feedback.

⸻

2. Problem
	•	Current QA is slow, subjective, and inconsistent.
	•	Style guides are underused because reviewers can’t keep all rules in mind.

MVP Goal:
	•	Every deduction tied to a documented rule.
	•	Auto scoring that is reproducible, explainable, and improvable.
	•	Reviewers save time while maintaining control.

⸻

3. MVP Workflow

3.1 Ingestion (Admin → KB)
	•	Admin uploads DOCX/PDF/HTML/MD style guide.
	•	Pipeline:
	1.	Convert → Markdown with section paths.
	2.	Detect rule cues (must/never/should/avoid, etc.) + Do/Don’t examples (can use same LLM if needed)
	3.	LLM normalizes snippets into atomic rules (JSON schema enforced).
	4.	Auto-classify into macro classes (Terminology, Punctuation, Mechanics, Standards, Style, Accuracy, Legal).
	5.	Assign default severity + weight (cue-based + macro defaults).
	6.	Generate regex checks for easy rules (punctuation width, placeholders, date format).
	•	Output: Rule KB JSON + Points Table CSV, stamped with kb_version + rubric_version.

⸻

3.2 Evaluation (Test Taker → Score)
	•	Test taker submits source + target.
	•	Pipeline:
	1.	Deterministic checks run (regex-ready rules: placeholders, punctuation width, date format, glossary).
	2.	Hybrid retrieval: embeddings + keyword search fetch candidate rules.
	3.	LLM (local): picks relevant rule_ids only; returns structured JSON (findings).
	4.	Scoring engine:
	•	Start at 100.
	•	Deduct weight × severity_multiplier (Minor=1, Major=2, Critical=3).
	•	Apply simple global cap to prevent style nitpicks dominating (e.g., max −30).
	5.	Output: ScoreReport JSON with citations, per-rule penalties, and final score.

⸻

3.3 Review (Reviewer → Override)
	•	Reviewer sees:
	•	Findings highlighted in translation.
	•	Rule text, severity, justification, citation.
	•	Reviewer actions:
	•	Accept / Change severity / Reclassify / Dismiss.
	•	System recomputes score live.
	•	Overrides logged as FeedbackEvents (audit trail).

⸻

4. Functional Requirements

4.1 Ingestion
	•	Normalize docs into Markdown.
	•	Detect cues + examples.
	•	LLM → atomic rules (JSON).
	•	Auto assign severity/weight.
	•	Generate regex for key mechanical rules.
	•	Store as Rule KB (JSON) + Points Table (CSV).

4.2 Evaluation
	•	Deterministic validators:
	•	Glossary/DNT terms.
	•	Placeholders {}, [], <>.
	•	Line breaks.
	•	Punctuation width (！“”《》（）：).
	•	Date format YYYY年M月D日.
	•	LLM evaluation with retrieval: must return existing rule_ids (JSON schema).
	•	Scoring engine with severity multipliers + weight ranges.
	•	Produce ScoreReport JSON with citations.

4.3 Review
	•	Display findings with highlights + rule details.
	•	Accept/override/dismiss → recompute score.
	•	Store overrides as FeedbackEvents.

4.4 Governance
	•	Pin {kb_version, rubric_version, model_prompt_version} to every job.
	•	FeedbackEvents logged, but no global rubric updates in MVP.

⸻

5. Non-Functional Requirements
	•	Local-only: All LLM + embeddings run on LM Studio endpoints.
	•	Latency: Deterministic ≤2s/1k chars; LLM ≤6s/segment.
	•	Precision: Deterministic validators ≥98%.
	•	Acceptance: ≥70% reviewer agreement on LLM findings.
	•	Explainability: 100% findings tied to rule_id + citation.
	•	Reproducibility: Same versions → same score.

⸻

6. LLM & Embeddings

6.1 Embeddings
	•	Endpoint: POST http://127.0.0.1:1234/v1/embeddings
	•	Model: .env EMBED_MODEL=text-embedding-nomic-embed-text-v1.5
	•	Use: store rules as vectors; hybrid search = embeddings + keyword.

6.2 Local LLM
	•	Endpoint: POST http://localhost:1234/v1/chat/completions
	•	Model: .env CHAT_MODEL=qwen/qwen3-1.7b
	•	Features: tool calls + JSON schema output.

6.3 Tools
	•	deterministic_checks(source,target,locale) → rule-bound findings.
	•	retrieve_rules(query_text, top_k) → top rule candidates.

6.4 Structured Output
	•	Ingestion schema: atomic rules (rule_text, examples, citation).
	•	Evaluation schema: findings (rule_id, severity, justification, span, citation).
	•	Any non-matching rule = dropped.

⸻

7. Data Structures

7.1 Rule KB Example

{
  "rule_id": "SHOPIFY-ZHCN-5.5-EXCL-DB",
  "macro_class": "Punctuation",
  "micro_class": "Exclamation width",
  "rule_text": "Use double-byte exclamation marks （！） in Simplified Chinese.",
  "examples_pos": ["示例！"],
  "examples_neg": ["示例!"],
  "default_severity": "Major",
  "default_weight": 2,
  "citation": {"section_path":["5","5.5"]},
  "regex_ready": true
}

7.2 Evaluation Finding

{
  "segment_id": "s_0192",
  "rule_id": "SHOPIFY-ZHCN-5.5-EXCL-DB",
  "severity": "Major",
  "penalty": 2,
  "justification": "Half-width '!' found; style guide mandates '！'.",
  "citation": {"section_path":["5","5.5"]},
  "deterministic": true
}

7.3 ScoreReport

{
  "job_id": "job_001",
  "kb_version": "2025.09.26-01",
  "rubric_version": "2025.09.26-01",
  "final_score": 84,
  "by_macro": {
    "Punctuation": {"penalty": 2, "count": 1}
  }
}

7.4 FeedbackEvent

{
  "event_id": "fb_001",
  "segment_id": "s_0192",
  "action": "downgrade_severity",
  "rule_id": "SHOPIFY-ZHCN-5.5-EXCL-DB",
  "old": "Major",
  "new": "Minor",
  "reason": "Allowed in marketing headers.",
  "actor": "reviewer@vendor.com"
}


⸻

8. Scoring Policy
	•	Severity multipliers: Minor=1, Major=2, Critical=3.
	•	Default weights:
	•	Accuracy/Terminology/Mechanics: 3–6
	•	Punctuation/Style: 1–2
	•	Legal: 5–6
	•	Simple cap: style/punctuation deductions ≤30 pts.
	•	Bands: ≥95 Excellent, 90–95 Good, 80–90 Fair, <80 Needs revision.

⸻

9. Acceptance Tests (MVP)
	•	Upload Shopify zh-CN guide → ≥30 rules induced.
	•	Rules include: exclamation width, placeholders, zh-CN date format, at least one DNT.
	•	Deterministic validators correctly flag seeded test strings.
	•	ScoreReport shows findings with citations.
	•	Reviewer can override a severity and see score update.
	•	Same {kb_version, rubric_version} → identical results.

⸻

10. Out of Scope (MVP)
	•	Global rubric updates (admin approval flow).
	•	Advanced category caps.
	•	Multi-lingual evaluation.
	•	Analytics dashboards.
	•	CAT tool integration.

⸻

✅ This PRD:
	•	Is trimmed to what you need to demo to a customer.
	•	Still includes all the critical backbone (document injection → KB → scoring → review).
	•	Leaves advanced features (rubric governance, analytics, drift monitoring) for v2+.

