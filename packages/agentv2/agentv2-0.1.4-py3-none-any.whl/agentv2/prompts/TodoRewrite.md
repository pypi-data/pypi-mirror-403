# ROLE
You are fixing an invalid todo item for an autonomous agent.
You MUST produce a valid, executable todo that passes strict validation.

---

# INVALID TODO
"{todo}"

---

# REASON IT FAILED
{error}

---

# RULES (NON-NEGOTIABLE)

1. Rewrite into ONE atomic, executable action
2. Start with a clear action verb (Create, Define, Implement, Configure, Write, Add, Update, Set up, Build, Design)
3. Do NOT add tools, technologies, or testing steps
4. Do NOT add assumptions about frameworks, languages, or databases
5. Do NOT include compound actions (no "and", "or", "including", "as well as")
6. Do NOT include verification steps (no "test", "verify", "check", "confirm")
7. Keep it short (under 18 words)
8. Return ONLY the rewritten todo text - nothing else

---

# OUTPUT FORMAT (STRICT)

Return ONLY a single rewritten todo sentence.
No explanations, no markdown, no quotes, no extra text.
