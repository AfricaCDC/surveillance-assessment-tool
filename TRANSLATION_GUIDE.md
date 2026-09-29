# Translation workflow

English remains the master wording for the assessment and the language used for stored field IDs and response values. The language selector in the application previews French, Arabic, Portuguese, Spanish, and Kiswahili. All questionnaire prompts, response choices, and primary assessment instructions have draft display translations. Untranslated text stays in English. Do not treat these previews as reviewed questionnaires.

The draft display translations are in `static/i18n.js`; questionnaire drafts are in `static/question-translations.json`, response choices in `static/choice-translations.json`, and primary assessment instructions in `static/interface-translations.json`. The `keys` array contains exact English display strings, and each `packs` array contains translations in the same order. Add a new key to every pack together. The script changes displayed text nodes only; it must never translate form values, REDCap field IDs, country identifiers, or previously entered answers. French, Arabic, Portuguese, and Spanish question and interface drafts were generated with a local Ollama model. Kiswahili questions, all response choices, and Kiswahili interface strings were drafted through the MyMemory service, which received public questionnaire wording only, not responses or secrets. Run `python scripts/finalize_question_translations.py` for recorded question corrections, then `python scripts/verify_question_translations.py` to check question coverage and protected terms. Run `python scripts/export_translation_review.py` to rebuild the review CSV.

Before removing a language's preview label:

1. Review every Inventory, Profiling, and Gap Analysis draft question, response choice, and primary instruction against the English source. Use `translation_review.csv` as the review list. Some secondary navigation, validation, accessibility, administrative, and report text remains English.
2. Keep surveillance terms and acronyms in English using one approved glossary. The initial list is in `scripts/build_question_translations.py` and should be expanded by the assessment owners.
3. Have a surveillance specialist and a native-language reviewer compare each translation against the English master. Check right-to-left layout and reading order for Arabic.
4. Verify that changing the language does not change serialized assessment data, REDCap saves, Excel imports or exports, or report content.

Reports and login pages are currently English. A language choice is saved in browser local storage, so it applies to that browser rather than to an account across devices.
