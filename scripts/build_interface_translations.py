"""Draft static assessment-page text and display attributes through MyMemory."""
import ast
import json
import time
from pathlib import Path

from build_choice_translations import translate
from build_question_translations import LANGUAGES, LOCAL_LANGUAGES, ROOT, source_choices, source_questions, translate_batch
from extract_interface_strings import source_interface_strings

OUTPUT = ROOT / "static" / "interface-translations.json"
PRESERVED = {"AFRICA CENTRES FOR DISEASE CONTROL AND PREVENTION", "Africa CDC Surveillance Systems Assessment", "REDCap primary database"}


def source_strings():
    i18n = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")
    common = set(ast.literal_eval(i18n.split("const keys = ", 1)[1].split(";", 1)[0]))
    covered = common | set(source_choices()) | set(source_questions())
    page = source_interface_strings()
    workflow = page[:page.index("Save domain responses") + 1]
    dynamic = ["Optional clarification for this question", "Add a comment or clarification…", "Select a response", "Explanation or supporting details", "Add relevant details…", "Add another value; separate several with semicolons"]
    return [item for item in dict.fromkeys(workflow + dynamic) if item not in covered and len(item) > 1 and not item.startswith("v1.")]


def main():
    catalog = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {code: {} for code in LANGUAGES}
    source = source_strings()
    print(f"Interface strings: {len(source)}", flush=True)
    for code, name in LOCAL_LANGUAGES.items():
        entries = catalog.setdefault(code, {})
        missing = [item for item in source if item not in entries]
        for offset in range(0, len(missing), 4):
            batch = missing[offset:offset + 4]
            try:
                drafts = translate_batch(name, batch)
            except Exception as error:
                print(f"Retrying {code} individually: {ascii(str(error))}", flush=True)
                drafts = []
                for item in batch:
                    try:
                        drafts.append(translate_batch(name, [item])[0])
                    except Exception:
                        drafts.append(item)
            entries.update(zip(batch, drafts))
            OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{code}: {len(entries)}/{len(source)}", flush=True)
        print(f"{code}: {len(entries)} interface drafts", flush=True)
    code = "sw"
    entries = catalog.setdefault(code, {})
    for index, item in enumerate(source, 1):
        if item in entries:
            continue
        try:
            entries[item] = item if item in PRESERVED else translate(item, code)
        except Exception as error:
            print(f"Stopped {code} at {index}/{len(source)}: {ascii(str(error))}", flush=True)
            return
        OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if index % 10 == 0:
            print(f"{code}: {index}/{len(source)}", flush=True)
        time.sleep(0.2)
    print(f"{code}: {len(entries)} interface drafts", flush=True)


if __name__ == "__main__":
    main()
