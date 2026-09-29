"""Draft questionnaire translations using the local Ollama model; review before release."""
import ast
import json
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen3:4b-instruct"
LANGUAGES = {"fr": "French", "ar": "Arabic", "pt": "Portuguese", "es": "Spanish", "sw": "Kiswahili"}
LOCAL_LANGUAGES = {code: name for code, name in LANGUAGES.items() if code != "sw"}
GLOSSARY = [
    "case-based surveillance", "event-based surveillance", "indicator-based surveillance",
    "community-based surveillance", "surveillance", "case notification", "case investigation",
    "contact tracing", "IDSR", "DHIS2 Tracker", "DHIS2",
    "REDCap", "PHEOC", "IES&PHE", "EMR", "CRVS", "MoH", "NPHI", "WHO", "Africa CDC", "OpenAI", "Ollama", "HIS",
    "One Health", "Rapid Response Team", "API", "HL7/FHIR", "GIS", "SOP", "CSV", "LIS", "EOC", "CHWs",
]
ACRONYMS = {"WHO", "API", "CSV", "LIS", "EOC", "CHWs", "IDSR", "PHEOC", "IES&PHE", "EMR", "CRVS", "MoH", "NPHI", "GIS", "SOP", "HL7/FHIR", "HIS"}


def term_pattern(term):
    escaped = re.escape(term)
    return rf"(?<![A-Za-z]){escaped}(?![A-Za-z])" if term in ACRONYMS else rf"(?i:{escaped})"


def source_questions():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    segment = source[source.index("const p1Fields="):source.index("function multiValueKey")]
    js = "const vm=require('vm');let s=process.argv[1];let x=vm.runInNewContext(s+';({p1Fields,p2Sections})');process.stdout.write(JSON.stringify(x));"
    fields = json.loads(subprocess.check_output(["node", "-e", js, segment], text=True))
    strings = [field[1] for field in fields["p1Fields"]]
    for title, group in fields["p2Sections"]:
        strings.append(title)
        strings.extend(field[1] for field in group)
    tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
    domains = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "DOMAINS" for target in node.targets))
    for domain in domains:
        strings.append(domain["name"])
        strings.extend(question["text"] for question in domain["questions"])
    return list(dict.fromkeys(strings))


def source_choices():
    source = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    segment = source[source.index("const p1Fields="):source.index("function multiValueKey")]
    js = "const vm=require('vm');let s=process.argv[1];let x=vm.runInNewContext(s+';({p1Fields,p2Sections})');process.stdout.write(JSON.stringify(x));"
    fields = json.loads(subprocess.check_output(["node", "-e", js, segment], text=True))
    strings = [option for field in fields["p1Fields"] for option in (field[3] if len(field) > 3 else [])]
    strings.extend(option for _, group in fields["p2Sections"] for field in group for option in (field[3] if len(field) > 3 else []))
    tree = ast.parse((ROOT / "server.py").read_text(encoding="utf-8"))
    domains = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "DOMAINS" for target in node.targets))
    strings.extend(option for domain in domains for question in domain["questions"] for option in question.get("options", []))
    return list(dict.fromkeys(option for option in strings if option))


def protect(text):
    matches = []
    pattern = re.compile("|".join(term_pattern(term) for term in sorted(GLOSSARY, key=len, reverse=True)))
    def replace(match):
        matches.append(match.group())
        return f"ZXTERM{len(matches)-1}ZX"
    return pattern.sub(replace, text), matches


def restore(text, matches):
    for index, term in enumerate(matches):
        marker = f"ZXTERM{index}ZX"
        if marker not in text:
            raise ValueError(f"Missing protected term {marker}: {text}")
        text = text.replace(marker, term)
    return text


def translate_batch(language, batch):
    protected = [protect(item) for item in batch]
    prompt = (
        f"Translate these public health assessment questions and headings from English to {language}. "
        "Return ONLY a JSON object with a translations array containing exactly one translated string per input, in the same order. "
        "Keep ZXTERM markers exactly as written; they represent technical terms that must stay in English. "
        "Keep the meaning, question form, and all punctuation. Do not add explanations.\n"
        + json.dumps([item for item, _ in protected], ensure_ascii=False)
    )
    payload = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0, "num_predict": 1600}, "messages": [{"role": "user", "content": prompt}]}).encode()
    request = Request("http://127.0.0.1:11434/api/chat", data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=240) as response:
        content = json.load(response)["message"]["content"]
    result = json.loads(content)
    if isinstance(result, dict):
        result = result.get("translations") or next((value for value in result.values() if isinstance(value, list)), result)
    if not isinstance(result, list) or len(result) != len(batch):
        raise ValueError(f"Expected {len(batch)} strings, got {str(result)[:500]}")
    return [restore(value, terms) for value, (_, terms) in zip(result, protected)]


def main():
    questions = source_questions()
    output = ROOT / "static" / "question-translations.json"
    data = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {language: {} for language in LANGUAGES}
    print(f"Question and section strings: {len(questions)}", flush=True)
    for code, name in LOCAL_LANGUAGES.items():
        translations = data.setdefault(code, {})
        missing = [question for question in questions if question not in translations or translations[question] == question]
        print(f"{name}: {len(missing)} remaining", flush=True)
        for offset in range(0, len(missing), 4):
            batch = missing[offset:offset + 4]
            try:
                translated = translate_batch(name, batch)
            except Exception as error:
                print(f"Retrying batch one question at a time: {ascii(str(error))}", flush=True)
                translated = []
                for question in batch:
                    try:
                        translated.append(translate_batch(name, [question])[0])
                    except Exception as single_error:
                        print(f"Untranslated question: {ascii(question)}; {ascii(str(single_error))}", flush=True)
                        translated.append(question)
            translations.update(zip(batch, translated))
            output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{name}: {len(translations)}/{len(questions)}", flush=True)
    print("Draft translation file:", output, flush=True)


if __name__ == "__main__":
    main()
