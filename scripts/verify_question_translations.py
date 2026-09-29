"""Check coverage and protected English terminology in draft question translations."""
import json
import re
from pathlib import Path

from build_question_translations import GLOSSARY, LANGUAGES, source_questions, term_pattern


def main():
    catalog = json.loads((Path(__file__).resolve().parents[1] / "static" / "question-translations.json").read_text(encoding="utf-8"))
    questions = source_questions()
    errors = []
    for code in LANGUAGES:
        entries = catalog.get(code, {})
        missing = [question for question in questions if not entries.get(question)]
        unchanged = [question for question in questions if entries.get(question) == question]
        for question, translation in entries.items():
            if question not in questions:
                errors.append(f"{code}: obsolete source text: {question}")
            for term in GLOSSARY:
                for match in re.finditer(term_pattern(term), question):
                    if match.group().lower() not in translation.lower():
                        errors.append(f"{code}: missing English term {match.group()}: {question}")
        print(f"{code}: {len(entries)}/{len(questions)} translated; {len(missing)} missing; {len(unchanged)} unchanged")
        errors.extend(f"{code}: missing: {question}" for question in missing)
    if errors:
        print("\n".join(errors[:50]))
        raise SystemExit(f"Translation verification failed: {len(errors)} issues")
    print("All question and section strings have draft translations; protected terms retained.")


if __name__ == "__main__":
    main()
