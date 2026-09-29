"""Create draft translations for questionnaire response choices through MyMemory."""
import html
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from build_question_translations import LANGUAGES, ROOT, protect, restore, source_choices

OUTPUT = ROOT / "static" / "choice-translations.json"
PRESERVED = {
    "Event-based Surveillance", "Case-based Data", "Case-based Surveillance",
    "Event based surveillance", "IDSR/weekly syndromic surveillance",
    "Event-based", "Indicator-based", "Case-based", "Community-based", "One Health",
    "DHIS2", "Go.Data", "OpenSRP", "CHT", "OpenMRS", "ODK", "CommCare",
    "RapidPro", "OpenELIS", "Odoo", "REDCap", "Kobo system", "HL7/FHIR Messaging",
    "Ebola", "Marburg", "Bundibugyo", "Cholera", "Mpox", "Measles", "COVID-19",
    "Yellow Fever", "Polio", "Influenza", "Anthrax", "MoH", "NPHI", "IES&PHE",
    "PHEOC", "EOC", "CHWs", "N/A",
}
ALREADY_TRANSLATED = {"Yes", "No", "Unknown", "Planned"}


def translate(text, language):
    source, terms = protect(text)
    url = "https://api.mymemory.translated.net/get?" + urlencode({"q": source, "langpair": f"en|{language}"})
    with urlopen(url, timeout=20) as response:
        result = json.load(response)
    if result.get("responseStatus") != 200:
        raise ValueError(result.get("responseDetails") or result)
    draft = html.unescape(result["responseData"]["translatedText"])
    if "MYMEMORY WARNING" in draft.upper() or "EXCEEDED" in draft.upper():
        raise ValueError(draft)
    return restore(draft, terms)


def main():
    catalog = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {code: {} for code in LANGUAGES}
    choices = source_choices()
    for code in LANGUAGES:
        entries = catalog.setdefault(code, {})
        for index, choice in enumerate(choices, 1):
            if choice in entries or choice in ALREADY_TRANSLATED:
                continue
            try:
                entries[choice] = choice if choice in PRESERVED else translate(choice, code)
            except Exception as error:
                print(f"Stopped {code} at {index}/{len(choices)}: {ascii(str(error))}", flush=True)
                return
            OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if index % 10 == 0:
                print(f"{code}: {index}/{len(choices)}", flush=True)
            time.sleep(0.2)
        print(f"{code}: {len(entries)} draft entries", flush=True)


if __name__ == "__main__":
    main()
