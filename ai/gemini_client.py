from google import genai
from google.genai import types, errors
from config import GEMINI_MODEL, MAX_CHAT_HISTORY
from utils.settings import get_setting
from ai.safety import SYSTEM_SAFETY
from ai.learning_modes import MODES

def generate_reply(prompt, mode="Tutor", profile=None, history=None):
    api_key = get_setting("GEMINI_API_KEY")
    api_key = str(api_key).strip() if api_key else ""
    if not api_key or api_key.lower() in {"your_gemini_api_key_here", "paste_your_api_key_here", "replace-with-your-key"}:
        return "Gemini is not configured. Add a valid GEMINI_API_KEY to the .env file in the same folder as app.py, then restart Streamlit."
    model = str(get_setting("GEMINI_MODEL", GEMINI_MODEL) or GEMINI_MODEL).strip()
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version="v1"),
        )
    except Exception as exc:
        raise RuntimeError(f"Could not initialize the Gemini client: {exc}") from exc
    profile = profile or {}
    context = (
        f"Student learning context (use only what is relevant): "
        f"interests={profile.get('interests','not supplied')}; "
        f"ambitions={profile.get('ambitions','not supplied')}; "
        f"learning_preferences={profile.get('learning_preferences','not supplied')}; "
        f"baseline_notes={profile.get('baseline_notes','not supplied')}."
    )
    contents = []
    for item in (history or [])[-MAX_CHAT_HISTORY:]:
        contents.append(types.Content(
            role="user" if item["role"] == "user" else "model",
            parts=[types.Part.from_text(text=item["content"])]
        ))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_SAFETY + "\n\n" + MODES.get(mode, MODES["Tutor"]) + "\n\n" + context,
        temperature=0.65,
        max_output_tokens=1200,
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except errors.APIError as exc:
        code = getattr(exc, "code", "unknown")
        message = getattr(exc, "message", None) or str(exc)
        raise RuntimeError(
            f"Gemini API error (HTTP {code}) using model '{model}': {message}. "
            "Check that the API key is valid, Gemini API access is enabled, and the model is available to your key."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Could not reach Gemini using model '{model}': {type(exc).__name__}: {exc}"
        ) from exc
    return response.text or "I couldn't prepare a response just now. Please try asking in a different way."
