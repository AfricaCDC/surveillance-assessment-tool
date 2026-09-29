"""Export draft display translations for human review."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
OUTPUT = ROOT / "translation_review.csv"
LANGUAGES = ("fr", "ar", "pt", "es", "sw")
CATALOGS = (
    ("Question", "question-translations.json"),
    ("Response choice", "choice-translations.json"),
    ("Interface", "interface-translations.json"),
)


def main():
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("Area", "English source", "French", "Arabic", "Portuguese", "Spanish", "Kiswahili", "Review status"))
        for area, filename in CATALOGS:
            catalog = json.loads((STATIC / filename).read_text(encoding="utf-8"))
            sources = dict.fromkeys(source for entries in catalog.values() for source in entries)
            for source in sources:
                writer.writerow((area, source, *(catalog.get(code, {}).get(source, "") for code in LANGUAGES), "Draft — review required"))
    print(f"Wrote {OUTPUT.name}")


if __name__ == "__main__":
    main()
