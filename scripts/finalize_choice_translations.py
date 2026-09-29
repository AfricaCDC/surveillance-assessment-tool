"""Apply reviewed corrections to machine-drafted response choices."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "static" / "choice-translations.json"
CORRECTIONS = {
    "fr": {
        "Ministry of Health": "Ministère de la Santé",
        "National": "National",
    },
}


def main():
    catalog = json.loads(PATH.read_text(encoding="utf-8"))
    for code, entries in CORRECTIONS.items():
        catalog[code].update(entries)
    PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Applied choice corrections")


if __name__ == "__main__":
    main()
