from openai import OpenAI
from commitgen.config import ensure_api_key


def generate_commit_message(diff_text, context):
    """
    Function that generates a commit message based on the provided diff text and context.
    If no context is provided, it generates a commit message based solely off the diff.
    """
    if not diff_text.strip():
        return "chore: no changes detected"

    prompt = _build_prompt(diff_text, context)


    api_key = ensure_api_key()
    client = OpenAI(api_key=api_key)

    response = client.responses.create( model="gpt-5-nano", input=prompt, store=True, )

    return response.output_text


def _build_prompt(diff_text: str, context: str) -> str:
    prompt = (
        "You are an expert software engineer.\n"
        "Generate a Conventional Commit message based on the following git diff.\n\n"
        f"GIT DIFF:\n{diff_text}\n\n"
    )

    if context:
        prompt += f"ADDITIONAL CONTEXT:\n{context}\n\n"

    prompt += (
        "Rules:\n"
        "- Use Conventional Commits format\n"
        "- for each change type, use appropriate prefix ([FEAT], [FIX], [DOCS], [STYLE], [REFACTOR], [PERF], [TEST], [CI], [CHORE])\n"
        "- Be concise\n"
        "- If multiple change types are present, include both in the message\n"
        "- Use present tense\n"
        "- Do not include explanations\n"
        "- If no changes detected, respond with '[CHORE]: no changes detected'\n"
        "- Adding lines or stylistic changes or whitespace changes is considered a [CHORE]\n"
        "- If presented additional context use it to generate a more specific message\n"
        "- Cap message at 100 characters per change or feat\n"
        "- Use imperative present tense (e.g. \"add\", \"fix\", \"update\", not \"added\" or \"fixed\")\n"
        "- MOST IMPORTANT DO NOT SKIP THIS STEP Make sure to output using this template if more than one change type detected example -> '[FEAT]: add user login feature',\n '[FIX]: resolve crash on startup',\n '[DOCS]: update README with setup instructions'\n"
    )

    return prompt

def refine_commit_message(existing_message: str, context: str) -> str:
    api_key = ensure_api_key()
    client = OpenAI(api_key=api_key)

    prompt = (
        "You are refining an existing Conventional Commit message.\n\n"
        f"EXISTING MESSAGE:\n{existing_message}\n\n"
        f"USER CONTEXT:\n{context}\n\n"
        "Rules:\n"
        "- Do NOT re-analyze git diff\n"
        "- Preserve existing structure\n"
        "- Only refine wording or add clarity\n"
        "- Use Conventional Commit prefixes\n"
        "- Keep output concise\n"
    )

    response = client.responses.create(
        model="gpt-5-nano",
        input=prompt,
        store=True,
    )

    return response.output_text

def _fallback_commit_message(diff_text: str, context: str) -> str:
    if not diff_text.strip():
        return "chore: no changes detected"

    base = "[FEAT]: update to codebase"

    if context:
        return f"{base}\n\nContext: {context}"

    return base
