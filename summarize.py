import json
import os

import httpx

LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:8001")
CONTEXT_TOKENS = 262144
MAX_OUTPUT_TOKENS = 2048
SAFETY_MARGIN = 256


def _client():
    return httpx.Client(
        base_url=LLM_URL,
        timeout=httpx.Timeout(600.0, connect=10.0),
    )


def _model_id(client: httpx.Client) -> str:
    data = client.get("/v1/models").json()
    models = data.get("data") or []
    if not models:
        raise RuntimeError("local LLM returned no models")
    return models[0]["id"]


def count_tokens(client: httpx.Client, content: str) -> int:
    """Ask the local LLM how many tokens a string uses."""
    response = client.post(
        "/tokenize",
        json={"content": content, "add_special": False},
    )
    response.raise_for_status()
    return len(response.json()["tokens"])


def _iter_completion(client: httpx.Client, model: str, prompt: str):
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_OUTPUT_TOKENS,
            "temperature": 0.2,
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            data = json.loads(payload)
            delta = ((data.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
            if delta:
                yield delta


def _strip_think(content: str) -> str:
    if "</think>" in content:
        return content.split("</think>", 1)[1].strip()
    return content.strip()


def _split_to_budget(client: httpx.Client, text: str, budget: int) -> list[str]:
    total = count_tokens(client, text)
    if total <= budget:
        return [text]
    n_chunks = max(2, (total + budget - 1) // budget)
    target_chars = max(1000, len(text) // n_chunks)
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + target_chars)
        if end < len(text):
            boundary = text.rfind("\n", start + target_chars // 2, end)
            if boundary > start:
                end = boundary + 1
        piece = text[start:end]
        while count_tokens(client, piece) > budget and len(piece) > 2000:
            piece = piece[: int(len(piece) * 0.85)]
            boundary = piece.rfind("\n")
            if boundary > len(piece) // 2:
                piece = piece[: boundary + 1]
        if not piece:
            break
        chunks.append(piece)
        start += len(piece)
    return chunks


def _stream_prompt(client, model, prompt):
    parts = []
    for delta in _iter_completion(client, model, prompt):
        parts.append(delta)
        yield {"type": "delta", "text": delta}
    yield {"type": "complete", "text": _strip_think("".join(parts))}


def summarize_bill_text_stream(full_text: str, label: str):
    """Yield status/delta/reset/done events while summarizing."""
    with _client() as client:
        model = _model_id(client)
        one_shot = (
            f"Summarize the following congressional legislation ({label}) for a civic reader. "
            "Cover what it does, the major provisions, who is affected, and any notable spending or conditions. "
            "Write 3-6 short paragraphs. Do not invent facts.\n\n"
            f"{full_text}"
        )
        budget = CONTEXT_TOKENS - MAX_OUTPUT_TOKENS - SAFETY_MARGIN
        yield {"type": "status", "message": "Checking bill length…"}
        if count_tokens(client, one_shot) <= budget:
            yield {"type": "status", "message": "Generating summary…"}
            summary = ""
            for event in _stream_prompt(client, model, one_shot):
                if event["type"] == "complete":
                    summary = event["text"]
                else:
                    yield event
            yield {"type": "done", "summary": summary}
            return

        wrapper = (
            f"This is part {{index}} of {{total}} of congressional legislation ({label}). "
            "Summarize only this section's provisions for a civic reader. Be concise. Do not invent facts.\n\n"
        )
        chunk_budget = budget - count_tokens(client, wrapper.format(index=99, total=99))
        chunks = _split_to_budget(client, full_text, max(1000, chunk_budget))
        partials = []
        for index, chunk in enumerate(chunks, start=1):
            yield {"type": "status", "message": f"Summarizing section {index} of {len(chunks)}…"}
            yield {"type": "reset"}
            prompt = wrapper.format(index=index, total=len(chunks)) + chunk
            section = ""
            for event in _stream_prompt(client, model, prompt):
                if event["type"] == "complete":
                    section = event["text"]
                else:
                    yield event
            partials.append(section)
        combine = (
            f"These are consecutive section summaries of congressional legislation ({label}). "
            "Combine them into one coherent summary for a civic reader: what it does, major provisions, "
            "who is affected, and any notable spending or conditions. Write 3-6 short paragraphs. "
            "Do not invent facts.\n\n"
            + "\n\n".join(f"Section {i}:\n{part}" for i, part in enumerate(partials, start=1))
        )
        if count_tokens(client, combine) > budget:
            combine = combine[: int(len(combine) * budget / count_tokens(client, combine))]
        yield {"type": "status", "message": "Combining section summaries…"}
        yield {"type": "reset"}
        summary = ""
        for event in _stream_prompt(client, model, combine):
            if event["type"] == "complete":
                summary = event["text"]
            else:
                yield event
        yield {"type": "done", "summary": summary}
