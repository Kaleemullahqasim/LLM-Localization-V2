Task List (MVP Build — Rule-Anchored Localization QA System)

1. Project Setup
	•	Initialize TypeScript project with clean directory structure (/services, /models, /utils).
	•	Define environment config (.env) for LM Studio endpoints:
	•	CHAT_BASE_URL, CHAT_MODEL (e.g., qwen/qwen3-1.7b).
	•	EMBED_BASE_URL, EMBED_MODEL (e.g., text-embedding-nomic-embed-text-v1.5).
	•	Scoring params (severity multipliers, style cap).

⸻

2. Core Data Models
	•	Rule: rule_id, macro_class, micro_class, rule_text, examples, default_severity, default_weight, citation, regex_ready.
	•	Finding: segment_id, rule_id, severity, justification, penalty, citation, deterministic flag.
	•	ScoreReport: job_id, kb_version, rubric_version, final_score, by_macro breakdown.
	•	FeedbackEvent: event_id, segment_id, action, old→new severity, reason, actor.

⸻

3. Ingestion Pipeline (Document → KB)
	•	Implement document parser (DOCX/PDF/HTML/MD → Markdown with section paths).
	•	Build cue miner (regex: must/never/should/avoid/preferred, Do/Don’t/Correct/Wrong/Example).
	•	Create LLM normalizer:
	•	Send candidate spans to LLM with induced_rules JSON schema.
	•	Ensure output has: rule_text, micro_class, examples, citation.
	•	Implement classification + scoring:
	•	Macro class assignment (Terminology, Punctuation, Mechanics, etc.).
	•	Default severity (cue-based: must/never = Major, should = Minor).
	•	Default weight by macro class.
	•	Add regex generators for: punctuation width, placeholders {}/[]/<>, zh-CN date format.
	•	Save results to:
	•	Rule KB JSON (full details).
	•	Points Table CSV (human-readable).
	•	Version outputs with kb_version + rubric_version.

⸻

4. Embedding & Retrieval
	•	Create embedding client (LM Studio endpoint).
	•	Embed all rules (rule_text + examples).
	•	Build simple vector index (in-memory or file-based).
	•	Implement hybrid search: top-k embeddings + keyword filter.

⸻

5. Deterministic Validators
	•	Glossary/DNT enforcement (lookup).
	•	Placeholder/tag validator ({}, [], <>, balanced & untouched).
	•	Line break preservation validator.
	•	Punctuation width validator (！“”《》（）：).
	•	Date format validator (YYYY年M月D日).

⸻

6. Evaluation Engine
	•	Create evaluation orchestrator:
	•	Run deterministic checks first.
	•	Run retrieval (embedding + keyword).
	•	Call LLM with retrieved rules → must output lqa_findings JSON schema.
	•	Filter out invalid rule_ids.
	•	Implement scoring:
	•	Base = 100.
	•	Deduct weight × severity_multiplier.
	•	Severity multipliers: Minor=1, Major=2, Critical=3.
	•	Global style/punctuation cap = −30 max.
	•	Generate ScoreReport JSON with rule citations + by_macro breakdown.

⸻

7. Reviewer System
	•	Build minimal UI (web page or CLI) to display:
	•	Findings with highlights in target text.
	•	Rule text, severity, justification, citation.
	•	Add reviewer controls: Accept / Change severity / Reclassify / Dismiss.
	•	Recompute score live on overrides.
	•	Log overrides as FeedbackEvents.

⸻

8. Governance (MVP scope)
	•	Stamp every job with {kb_version, rubric_version, model_prompt_version}.
	•	Store all FeedbackEvents (no auto rubric updates in MVP).

⸻

9. Testing & Acceptance
	•	Create a smoke test set with seeded strings:
	•	Half-width ! → flagged by punctuation rule.
	•	Placeholder {name} modified → flagged.
	•	2025-09-01 instead of 2025年9月1日 → flagged.
	•	Known DNT term mistranslated → flagged.
	•	Verify ingestion of Shopify zh-CN guide → at least 30 rules created.
	•	Verify evaluator produces ScoreReport JSON with citations.
	•	Verify reviewer can override severity and see score update.
	•	Verify rescoring with same versions produces identical results.

⸻

Critical Path (must finish to demo)
	1.	Ingestion pipeline (doc → KB).
	2.	Deterministic validators (5 essentials).
	3.	Embedding + retrieval.
	4.	Evaluation orchestrator + scoring.
	5.	Minimal reviewer UI + override.

Everything else (advanced validators, governance UI, analytics) = defer to v2.

⸻

⚡ This task list is tight and executable. It matches the PRD exactly and strips away non-MVP extras. With this, your AI assistant/dev team can build a working demo system to show your customer.

