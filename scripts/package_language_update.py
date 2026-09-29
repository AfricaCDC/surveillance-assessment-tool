"""Build source deployment update containing the language selector and draft catalogs."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "static/index.html",
    "static/styles.css",
    "static/i18n.js",
    "static/question-translations.json",
    "static/choice-translations.json",
    "static/interface-translations.json",
    "translation_review.csv",
    "TRANSLATION_GUIDE.md",
)


def main():
    destination = ROOT / "language_update.zip"
    with ZipFile(destination, "w", ZIP_DEFLATED) as package:
        for name in FILES:
            package.write(ROOT / name, name)
    print(f"Wrote {destination.name} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
