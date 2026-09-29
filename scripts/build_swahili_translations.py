"""Draft Kiswahili questions through MyMemory; review before release."""
import html
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from build_question_translations import protect, restore, source_questions

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "static" / "question-translations.json"


def translate(question):
    source, terms = protect(question)
    url = "https://api.mymemory.translated.net/get?" + urlencode({"q": source, "langpair": "en|sw"})
    with urlopen(url, timeout=20) as response:
        result = json.load(response)
    if result.get("responseStatus") != 200:
        raise ValueError(result.get("responseDetails") or result)
    translation = html.unescape(result["responseData"]["translatedText"])
    if "MYMEMORY WARNING" in translation.upper() or "EXCEEDED" in translation.upper():
        raise ValueError(translation)
    return restore(translation, terms)


def main():
    catalog = json.loads(OUTPUT.read_text(encoding="utf-8"))
    # Replace the low-quality local draft, retaining successful service translations on resume.
    if catalog.get("sw", {}).get("Tool / System Name") == "Jinsi ya Mstari / Mwisho":
        catalog["sw"] = {}
        OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    entries = catalog.setdefault("sw", {})
    questions = source_questions()
    for index, question in enumerate(questions, 1):
        if question in entries:
            continue
        try:
            entries[question] = translate(question)
        except Exception as error:
            print(f"Stopped at {index}/{len(questions)}: {ascii(str(error))}", flush=True)
            break
        OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if index % 10 == 0:
            print(f"Kiswahili: {index}/{len(questions)}", flush=True)
        time.sleep(0.3)
    print(f"Kiswahili catalog: {len(entries)}/{len(questions)}", flush=True)


if __name__ == "__main__":
    main()
