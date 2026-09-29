"""Apply reviewed fixes and remove obsolete draft entries from question catalogs."""
import json
from pathlib import Path

from build_question_translations import LANGUAGES, source_questions

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "static" / "question-translations.json"
FIXES = {
    "fr": {
        "Surveillance Functions": "Fonctions de surveillance",
        "Sustainability": "Pérennité",
        "Which surveillance approaches does the system support?": "Quelles approches de surveillance le système prend-il en charge ?",
        "Who currently provides the main technical support for the system?": "Qui fournit actuellement le principal soutien technique au système ?",
        "Who are the main institutions and actors involved in surveillance and emergency response in the country?": "Quelles sont les principales institutions et les principaux acteurs impliqués dans surveillance et dans la réponse aux urgences dans le pays ?",
        "How well do the variables and indicators in national surveillance tools align with the Gap Analysis Toolkit data dictionary and current national, WHO and Africa CDC guidance?": "Dans quelle mesure les variables et indicateurs des outils nationaux de surveillance sont-ils alignés sur le dictionnaire de données du Gap Analysis Toolkit et sur les recommandations nationales, de WHO et de Africa CDC actuellement en vigueur ?",
    },
    "ar": {
        "Surveillance Functions": "وظائف Surveillance",
        "Who currently provides the main technical support for the system?": "من يقدم حاليًا الدعم التقني الرئيسي للنظام؟",
        "Who are the main institutions and actors involved in surveillance and emergency response in the country?": "من هي المؤسسات والجهات الفاعلة الرئيسية المشاركة في surveillance والاستجابة للطوارئ في البلد؟",
    },
    "pt": {
        "Who currently provides the main technical support for the system?": "Quem presta atualmente o principal apoio técnico ao sistema?",
        "Who are the main institutions and actors involved in surveillance and emergency response in the country?": "Quais são as principais instituições e os atores envolvidos em surveillance e na resposta a emergências no país?",
    },
    "es": {
        "Surveillance Functions": "Funciones de surveillance",
        "Who currently provides the main technical support for the system?": "¿Quién proporciona actualmente el principal soporte técnico al sistema?",
        "Who are the main institutions and actors involved in surveillance and emergency response in the country?": "¿Cuáles son las principales instituciones y actores involucrados en surveillance y en la respuesta a emergencias en el país?",
    },
    "sw": {
        "Who currently provides the main technical support for the system?": "Ni nani anayetoa msaada mkuu wa kiufundi kwa mfumo kwa sasa?",
        "Who are the main institutions and actors involved in surveillance and emergency response in the country?": "Ni taasisi na wadau gani wakuu wanaohusika katika surveillance na mwitikio wa dharura nchini?",
    },
}


def main():
    catalog = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = source_questions()
    for code in LANGUAGES:
        entries = {question: catalog.get(code, {}).get(question, "") for question in source}
        entries.update(FIXES.get(code, {}))
        catalog[code] = entries
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
