"""Create a traceable Russian audio-lesson script from an official guide range."""
import argparse
import json
import os
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "imports" / "colombia_nuestra_casa_pages.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--from-page", type=int, required=True)
    parser.add_argument("--to-page", type=int, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pages = json.loads(SOURCE.read_text(encoding="utf-8"))["pages"]
    source = "\n\n".join(
        f"[Страница {page['page']}]\n{page['text']}"
        for page in pages
        if args.from_page <= page["page"] <= args.to_page
    )
    prompt = f"""Ты методист для подготовки к экзамену на гражданство Колумбии.
Подготовь на русском сценарий аудиоурока «{args.title}» объёмом 1500–1800 слов.
Используй только факты из приведённых ниже страниц официальной методички. Не добавляй
непроверяемые сведения. Объясняй простым языком, в конце сделай краткое повторение.
Не упоминай, что ты ИИ, и не добавляй вопросы: тест будет отдельным этапом.

{source}"""
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("DEEPSEEK_API_KEY is not configured")
    payload = json.dumps({
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.15,
        "max_tokens": 3500,
    }).encode("utf-8")
    req = request.Request(
        "https://api.deepseek.com/chat/completions", data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST",
    )
    with request.urlopen(req, timeout=180) as response:
        result = json.load(response)
    text = result["choices"][0]["message"]["content"].strip()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"Wrote {len(text.split())} words to {output}")


if __name__ == "__main__":
    main()
