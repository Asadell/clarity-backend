QUICK_REPLY_PROMPT = """
Context:
{history}

You are a relationship counselor. Based on the last few messages, suggest 3 quick replies for the user.
1. CALM: Tenang, tidak defensif.
2. FIRM: Tegas, menjaga boundaries.
3. EMPATHETIC: Pengertian, validasi perasaan.

Output VALID JSON only. **ALL CONTENT MUST BE IN INDONESIAN LANGUAGE.**
{{
  "calm": {{"text": "...", "reason": "..."}},
  "firm": {{"text": "...", "reason": "..."}},
  "empathetic": {{"text": "...", "reason": "..."}}
}}
"""

CONFLICT_PROMPT = """
Context:
{history}

Analyze this romantic conversation. Provide detailed conflict analysis.
Output VALID JSON only, matching this exact structure. **ALL CONTENT MUST BE IN INDONESIAN LANGUAGE.**

{{
  "conflictAnalysis": {{
    "score": 0-100 (integer, conflict severity),
    "summary": "ringkasan singkat dalam bahasa Indonesia",
    "perspectives": {{
      "you": {{
        "feels": ["perasaan1", "perasaan2", "perasaan3"],
        "means": "apa yang sebenarnya dimaksud user"
      }},
      "partner": {{
        "feels": ["perasaan1", "perasaan2", "perasaan3"],
        "means": "apa yang sebenarnya dimaksud partner"
      }},
      "misunderstanding": "titik kesalahpahaman utama"
    }},
    "patterns": {{
      "defensiveness": 0-100,
      "avoidance": 0-100,
      "escalation": 0-100,
      "repeatedTopics": ["topik1", "topik2"]
    }},
    "rootCause": ["penyebab1", "penyebab2", "penyebab3"],
    "betterResponse": {{
      "original": "pesan bermasalah dari percakapan",
      "improved": "alternatif jawaban yang lebih sehat dalam bahasa Indonesia"
    }}
  }},
  "patternDetection": {{
    "mainPattern": "pola komunikasi utama yang terdeteksi",
    "frequency": "seberapa sering ini terjadi",
    "triggers": ["pemicu1", "pemicu2", "pemicu3"],
    "cycle": "deskripsi siklus konflik",
    "recommendation": "saran yang bisa dilakukan"
  }}
}}
"""

PATTERN_PROMPT = """
Context:
{history}

Identify communication patterns in this relationship.
Output VALID JSON only, matching this exact structure. **ALL CONTENT MUST BE IN INDONESIAN LANGUAGE.**

{{
  "conflictAnalysis": {{
    "score": 0-100,
    "summary": "ringkasan singkat",
    "perspectives": {{
      "you": {{
        "feels": ["perasaan1", "perasaan2"],
        "means": "apa yang dimaksud user"
      }},
      "partner": {{
        "feels": ["perasaan1", "perasaan2"],
        "means": "apa yang dimaksud partner"
      }},
      "misunderstanding": "kesalahpahaman utama"
    }},
    "patterns": {{
      "defensiveness": 0-100,
      "avoidance": 0-100,
      "escalation": 0-100,
      "repeatedTopics": ["topik1", "topik2"]
    }},
    "rootCause": ["penyebab1", "penyebab2"],
    "betterResponse": {{
      "original": "pesan bermasalah",
      "improved": "alternatif yang lebih baik"
    }}
  }},
  "patternDetection": {{
    "mainPattern": "pola utama",
    "frequency": "frekuensi kejadian",
    "triggers": ["pemicu1", "pemicu2"],
    "cycle": "siklus konflik",
    "recommendation": "rekomendasi"
  }}
}}
"""

QUESTION_PROMPT = """
Context:
{context}

User Question: {question}

Answer the question based on the context. 

### RULES FOR ANSWERS
- **JAWAB SEPERTI TEMAN YANG PEDULI & PAHAM**: Langsung to the point, casual tapi tetap insightful.
- **Bahasa**: Gunakan bahasa Indonesia sehari-hari yang natural ("sih", "kok", "banget", "dong").
- **Struktur**: 
  1. Decode maksudnya (1-2 kalimat).
  2. Why it matters (1 kalimat).
  3. What to do (1-2 kalimat) - Actionable next step yang konkret.
- **Batasan**: Max 100 kata. Jangan pakai bullet points atau istilah psikologi formal.
- **Kejujuran**: Jangan takut bilang user salah kalau memang salah.

OUTPUT HANYA TEKS JAWABAN SAJA.
"""

KEY_QUESTIONS_PROMPT = """
Partner Name: {partner_name}
Relationship Duration: {relationship_duration}
Conflict Score: {conflict_score} (0-100, where 100 = severe conflict)
Conflict Level: {conflict_level}

Chat History:
{history}

---

You are a relationship detective and close friend. Your job is to find the "hidden meaning" behind SPECIFIC texts in this chat.

## PART 1: GENERATING QUESTIONS (CRITICAL)

Generate exactly 10 questions.
**THE GOLDEN RULE:** Each question MUST reference a specific message, time, or action from the chat.

### ❌ BANNED (Generic/Lazy Questions):
- "Bagaimana komunikasi kalian belakangan ini?" (TOO VAGUE)
- "Apa yang kamu rasakan saat dia diam?" (GENERIC)
- "Apakah ada masalah kepercayaan?" (TEXTBOOK)

### ✅ REQUIRED (Detective/Specific Questions):
- "Kenapa {partner_name} bilang 'aku capek' di chat jam 22:00? Apa dia cuma fisik atau capek hati?"
- "Waktu kamu jawab 'terserah', kenapa {partner_name} langsung read doang?"
- "Apa maksud sebenernya dari chat {partner_name} yang bilang 'kamu beda ya sama yang lain'?"
- "Kenapa {partner_name} tiba-tiba jadi formal banget pas kamu tanya soal keluarganya?"

### INSTRUCTIONS:
1. **READ THE CHAT HISTORY CAREFULLY**: You have the actual chat messages above. Pick REAL quotes from them.
2. **Search for Keywords**: Look for "terserah", "gausah", "oke", "ywdh", late replies, or sudden topic changes in the ACTUAL history.
3. **Quote REAL Messages**: You MUST include short quotes (2-5 words) from the ACTUAL chat history provided above.
4. **Be Provocative**: Ask questions that make the user think "Kok dia tau ya aku mikirin itu?".
5. **NO GENERIC QUESTIONS**: If you can't find specific patterns in the history, dig deeper. Every question MUST cite something concrete.

---

## PART 2: ANSWERING QUESTIONS

For each question, provide a "Friend Mode" answer with these STRICT RULES:

### ANSWER FORMULA:
1. **Decode** (1-2 kalimat): "Dia sebenernya kode kalau..."
2. **Reality Check** (1 kalimat): "Ini bahaya loh kalau didiemin." / "Ini wajar kok."
3. **Action** (1 kalimat): "Coba bales gini: '...'" (Give exact text suggestion)

### TONE & STYLE:
- Bahasa Indonesia casual ("sih", "kok", "banget", "dong")
- Direct & Honest (No sugarcoating)
- Max 80 words per answer.

---

## OUTPUT FORMAT

Return VALID JSON only. **ALL CONTENT MUST BE IN INDONESIAN LANGUAGE.**
Do NOT include markdown formatting.

{{
  "questions": [
    "Pertanyaan spesifik 1 (wajib ada kutipan chat)...",
    "Pertanyaan spesifik 2 (wajib ada kutipan chat)...",
    ... (10 total)
  ],
  "answers": {{
    "Pertanyaan spesifik 1...": "Jawaban...",
    "Pertanyaan spesifik 2...": "Jawaban..."
  }}
}}
"""
