"""Check draft catalog coverage for every supported display language."""
import json

from build_choice_translations import ALREADY_TRANSLATED
from build_interface_translations import source_strings
from build_question_translations import LANGUAGES, ROOT, source_choices, source_questions

CATALOGS = (
    ("questions", ROOT / "static" / "question-translations.json", source_questions(), set()),
    ("choices", ROOT / "static" / "choice-translations.json", source_choices(), ALREADY_TRANSLATED),
    ("interface", ROOT / "static" / "interface-translations.json", source_strings(), set()),
)


def main():
    failures = []
    for area, path, source, elsewhere in CATALOGS:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        expected = set(source) - elsewhere
        for code in LANGUAGES:
            entries = catalog.get(code, {})
            missing = sorted(key for key in expected if not entries.get(key))
            markers = sorted(key for key in expected if "ZXTERM" in entries.get(key, ""))
            failures.extend((area, code, kind, key) for kind, keys in (("missing", missing), ("marker", markers)) for key in keys)
            print(f"{area} {code}: {len(expected) - len(missing)}/{len(expected)}")
    if failures:
        for failure in failures[:20]:
            print("FAIL", *failure)
        raise SystemExit(f"{len(failures)} translation coverage failures")
    print("All draft catalogs have full coverage.")


if __name__ == "__main__":
    main()
