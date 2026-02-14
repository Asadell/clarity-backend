QUICK_REPLY_PROMPT = """
Context:
{history}

You are a relationship counselor. Based on the last few messages, suggest 3 quick replies for the user.
1. CALM: Tenang, tidak defensif.
2. FIRM: Tegas, menjaga boundaries.
3. EMPATHETIC: Pengertian, validasi perasaan.

Output VALID JSON only:
{{
  "calm": {{"text": "...", "reason": "..."}},
  "firm": {{"text": "...", "reason": "..."}},
  "empathetic": {{"text": "...", "reason": "..."}}
}}
"""

CONFLICT_PROMPT = """
Context:
{history}

Analyze the conflict in this conversation.
Output VALID JSON only:
{{
  "score": 0-100,
  "perspectives": {{
    "user": "...",
    "partner": "..."
  }},
  "root_cause": ["..."],
  "suggestion": "..."
}}
"""

PATTERN_PROMPT = """
Context:
{history}

Identify communication patterns.
Output VALID JSON only:
{{
  "main_pattern": "...",
  "triggers": ["..."],
  "cycle": "...",
  "recommendation": "..."
}}
"""

QUESTION_PROMPT = """
Context:
{context}

User Question: {question}

Answer the question based on the context. Be insightful.
"""
