import json
import re
import textwrap
from pathlib import Path
from typing import Dict, List, Optional


PHASE2_FIELD_LABELS = {
    "official_name": "Official system name",
    "platforms": "Underlying platform",
    "implementation_status": "Implementation status",
    "year_implemented": "Year first implemented",
    "surveillance_approaches": "Surveillance approaches supported",
    "diseases_supported": "Diseases, hazards or public-health events supported",
    "captures_signals": "Captures signals or rumours",
    "captures_verification": "Captures signal verification status and outcome",
    "alert_risk_assessment": "Captures alert risk assessment, classification and prioritisation",
    "case_notifications": "Captures suspected case notifications and profiles",
    "unique_identifier": "Generates or stores a unique identifier",
    "case_investigation": "Captures case investigation details and outcomes",
    "specimen_requests": "Captures specimen details and laboratory requests",
    "specimen_tracking": "Supports specimen tracking",
    "lab_results": "Captures laboratory test details and results",
    "lab_results_received": "How laboratory results are received",
    "contact_identification": "Supports contact identification and listing",
    "contact_followup": "Supports contact follow-up",
    "dashboards_surveillance": "Provides surveillance and response dashboards",
    "gis_mapping": "Supports GIS mapping",
    "epidemic_curves": "Generates epidemic curves",
    "trend_analysis": "Supports trend analysis",
    "hotspot_analysis": "Supports hotspot or cluster analysis",
    "contact_dashboards": "Provides contact follow-up dashboards",
    "lab_dashboards": "Provides laboratory dashboards",
    "mortality_dashboards": "Provides mortality dashboards",
    "custom_visualisations": "Supports custom analyses and visualisations",
    "automated_alerts": "Generates automated alerts or notifications",
    "threshold_monitoring": "Monitors surveillance thresholds",
    "line_lists": "Generates case, contact, specimen or alert line lists",
    "situation_reports": "Generates situation reports",
    "weekly_reports": "Generates weekly surveillance reports",
    "monthly_reports": "Generates monthly surveillance reports",
    "scheduled_reports": "Supports scheduled report distribution",
    "bulletin_outputs": "Provides surveillance bulletin outputs",
    "excel_export": "Supports spreadsheet export",
    "pdf_export": "Supports PDF export",
    "api_access": "Supports API-based access",
    "primary_users": "Primary user groups",
    "active_users": "Approximate active users",
    "coverage_level": "Geographic or administrative coverage",
    "district_count": "Districts or equivalent areas implemented",
    "facility_count": "Facilities or service-delivery points implemented",
    "web_access": "Accessible through a web browser",
    "mobile_interface": "Mobile application or mobile-optimised interface",
    "offline_access": "Works without internet connectivity",
    "api_available": "Provides an API",
    "open_source": "Distributed under an open-source licence",
    "hosting_model": "Primary hosting model",
    "data_exchange": "Exchanges data with other systems",
    "exchange_comments": "Data-exchange systems and data types",
    "ownership_institution": "Owning and managing institution",
    "hosting_institution": "Hosting institution or provider",
    "sop_available": "Standard operating procedures available",
    "user_manuals": "User manuals or job aids available",
    "data_policy": "Approved data-access, use and sharing policy",
    "security_controls": "Data-security and privacy controls implemented",
    "emergency_support": "Previously supported an emergency response",
    "supported_events": "Outbreaks or emergencies supported",
    "lessons_learned": "Lessons from routine or emergency deployment",
    "technical_support": "Main technical-support provider",
    "expertise_sufficient": "National team has sufficient in-house expertise",
    "funding_source": "Main operation and maintenance funding source",
    "retained_capabilities": "Strengths or capabilities to retain",
    "operational_challenges": "Operational, technical, governance or user challenges",
    "planned_enhancements": "Planned or funded enhancements",
    "implementation_lessons": "Implementation lessons for future deployments",
    "known_limitations": "Known limitations",
    "priority_actions": "Priority roadmap actions or milestones",
    "other_information": "Other relevant information",
}

PHASE2_INTERNAL_FIELDS = {"_tool_id", "field_comments", "imported_comments"}


def _format_report_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def _natural_join(items: List[str]) -> str:
    items = [str(item).strip() for item in items if str(item).strip()]
    if not items:
        return "none recorded"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def _is_api_enabled(value: object) -> bool:
    normalized = _format_report_value(value).strip().lower()
    return normalized in {"yes", "y", "true", "1"}


def _is_affirmative(value: object) -> bool:
    normalized = _format_report_value(value).lower()
    return bool(normalized) and normalized in {
        "yes",
        "y",
        "true",
        "1",
        "supported",
        "available",
        "present",
        "implemented",
        "active",
        "open",
        "operational",
        "ok",
    }


def _is_negative(value: object) -> bool:
    normalized = _format_report_value(value).lower()
    return bool(normalized) and normalized in {
        "no",
        "n",
        "false",
        "0",
        "not supported",
        "not available",
        "absent",
        "missing",
        "unknown",
        "none",
        "not implemented",
        "not operational",
    }


def _classify_yes_no(value: object):
    if _is_affirmative(value):
        return True
    if _is_negative(value):
        return False
    return None


def _normalize_phase2_assessments(phase2):
    def has_name(item):
        name = _format_report_value(item.get("official_name", "")).strip()
        return bool(name) and name.casefold() != "unnamed"

    if isinstance(phase2, dict):
        candidates = [phase2] if has_name(phase2) else []
    elif isinstance(phase2, list):
        candidates = [item for item in phase2 if isinstance(item, dict) and has_name(item)]
    else:
        candidates = []

    # REDCap repeating instruments can contain the same profiled system more than
    # once. Consolidate those rows before calculating scores or writing findings.
    consolidated = {}
    for candidate in candidates:
        key = re.sub(
            r"[^a-z0-9]+",
            " ",
            _format_report_value(candidate.get("official_name", "")).casefold(),
        ).strip()
        if key not in consolidated:
            consolidated[key] = dict(candidate)
            continue
        existing = consolidated[key]
        for field, value in candidate.items():
            if isinstance(value, list):
                combined = existing.get(field, [])
                if not isinstance(combined, list):
                    combined = [combined] if _format_report_value(combined) else []
                seen = {_format_report_value(item).casefold() for item in combined}
                for item in value:
                    normalized = _format_report_value(item).casefold()
                    if normalized and normalized not in seen:
                        combined.append(item)
                        seen.add(normalized)
                existing[field] = combined
            elif not _format_report_value(existing.get(field)) and _format_report_value(value):
                existing[field] = value
    return list(consolidated.values())


def _is_placeholder_entry(value: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", _format_report_value(value).casefold()).strip()
    return normalized in {
        "na",
        "n a",
        "nil",
        "none",
        "not applicable",
        "no recommendation",
        "no recommendations",
    }


def _is_national_coverage(value: object) -> bool:
    """Return true only when the response explicitly denotes national coverage."""
    normalized = re.sub(r"[^a-z0-9]+", " ", _format_report_value(value).casefold()).strip()
    if not normalized:
        return False
    return normalized in {
        "national",
        "national scale",
        "national level",
        "national coverage",
        "countrywide",
        "country wide",
    } or normalized.startswith("national scale ") or normalized.startswith("national level ")


def _dedupe_report_items(items, merge_similar=False):
    unique = []
    exact_keys = set()
    for item in items:
        item = re.sub(r"\s+", " ", _format_report_value(item)).strip()
        exact_key = re.sub(r"[^a-z0-9]+", " ", item.casefold()).strip()
        if not item or exact_key in exact_keys:
            continue

        replacement_index = None
        if merge_similar:
            name, _, detail = item.partition(":")
            candidate_tokens = set(re.findall(r"[a-z0-9]+", detail.casefold())) - {
                "a", "an", "and", "are", "for", "is", "of", "the", "to", "with",
            }
            if len(candidate_tokens) >= 5:
                for index, existing in enumerate(unique):
                    existing_name, _, existing_detail = existing.partition(":")
                    if existing_name.casefold() != name.casefold():
                        continue
                    existing_tokens = set(re.findall(r"[a-z0-9]+", existing_detail.casefold())) - {
                        "a", "an", "and", "are", "for", "is", "of", "the", "to", "with",
                    }
                    union = candidate_tokens | existing_tokens
                    similarity = len(candidate_tokens & existing_tokens) / len(union) if union else 0
                    if similarity >= 0.65:
                        replacement_index = index
                        break
        if replacement_index is not None:
            if len(item) > len(unique[replacement_index]):
                unique[replacement_index] = item
            exact_keys.add(exact_key)
            continue
        unique.append(item)
        exact_keys.add(exact_key)
    return unique


def _flatten_phase2_entries(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        entries = [str(item).strip() for item in value if str(item).strip()]
        return _dedupe_report_items([item for item in entries if not _is_placeholder_entry(item)])
    text_value = _format_report_value(value)
    if not text_value:
        return []
    entries = [part.strip() for part in re.split(r"[,;\n]", text_value) if part.strip()]
    return _dedupe_report_items([item for item in entries if not _is_placeholder_entry(item)])


def _phase2_domain_scores(assessments):
    domain_key_map = {
        "Access and availability": ["web_access", "mobile_interface", "offline_access", "api_available"],
        "Interoperability and data exchange": ["data_exchange", "open_source", "api_available"],
        "Governance and data quality": ["sop_available", "user_manuals", "data_policy", "security_controls"],
        "Operational readiness": ["emergency_support", "expertise_sufficient"],
    }
    rows = []
    for domain, keys in domain_key_map.items():
        total = 0
        positive = 0
        for assessment in assessments:
            for key in keys:
                if key not in assessment:
                    continue
                classification = _classify_yes_no(assessment.get(key))
                if classification is None:
                    continue
                total += 1
                if classification:
                    positive += 1
        if total:
            score = round((positive / total) * 100)
            rows.append([domain, str(total), str(positive), f"{score}%"])
    return rows


def _phase2_assessment_completeness(assessments):
    rows = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        fields = [
            key for key in PHASE2_FIELD_LABELS
            if key != "official_name" and key in assessment
        ]
        total = len(fields)
        filled = sum(1 for key in fields if bool(_format_report_value(assessment.get(key))))
        percent = round((filled / total) * 100) if total else 0
        rows.append([name, str(filled), str(total), f"{percent}%"])
    return rows


def _phase2_short_summary(assessments):
    capability_fields = [
        ("captures_signals", "signal detection"), ("alert_risk_assessment", "alert risk assessment"),
        ("case_notifications", "case notification"), ("case_investigation", "case investigation"),
        ("specimen_tracking", "specimen tracking"), ("lab_results", "laboratory results"),
        ("contact_identification", "contact identification"), ("contact_followup", "contact follow-up"),
        ("dashboards_surveillance", "surveillance dashboards"), ("gis_mapping", "GIS mapping"),
        ("trend_analysis", "trend analysis"), ("automated_alerts", "automated alerts"),
        ("line_lists", "line lists"), ("situation_reports", "situation reports"),
        ("api_available", "API access"), ("data_exchange", "data exchange"),
        ("offline_access", "offline operation"),
    ]
    critical_gap_fields = [
        ("contact_identification", "contact identification"), ("contact_followup", "contact follow-up"),
        ("specimen_tracking", "specimen tracking"), ("lab_results", "laboratory-result capture"),
        ("offline_access", "offline operation"), ("data_exchange", "data exchange"),
        ("sop_available", "standard operating procedures"), ("user_manuals", "user manuals or job aids"),
    ]
    summaries = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        identity = [_format_report_value(assessment.get(key)) for key in
                    ("platforms", "surveillance_approaches", "diseases_supported")]
        identity = [item for item in identity if item]
        context = [_format_report_value(assessment.get(key)) for key in
                   ("implementation_status", "coverage_level")]
        context = [item for item in context if item]
        opening = f"{name} is profiled" + (" as " + ", ".join(identity) if identity else "")
        if context:
            opening += ", with " + " and ".join(context) + " status/coverage"
        sentences = [opening + "."]
        capabilities = [label for key, label in capability_fields if _is_affirmative(assessment.get(key))]
        gaps = [label for key, label in critical_gap_fields if _is_negative(assessment.get(key))]
        if capabilities:
            sentences.append("Key capabilities include " + ", ".join(capabilities[:7]) + ".")
        if gaps:
            sentences.append("Main gaps are " + ", ".join(gaps[:5]) + ".")
        challenge = _format_report_value(assessment.get("operational_challenges"))
        limitation = _format_report_value(assessment.get("known_limitations"))
        if challenge and not _is_placeholder_entry(challenge):
            sentences.append(f"Reported challenges include {challenge.rstrip('. ')}.")
        limitation_key = re.sub(r"[^a-z0-9]+", " ", limitation.casefold()).strip()
        challenge_key = re.sub(r"[^a-z0-9]+", " ", challenge.casefold()).strip()
        if (limitation and not _is_placeholder_entry(limitation)
                and limitation_key != challenge_key):
            sentences.append(f"Known limitations include {limitation.rstrip('. ')}.")
        narrative = []
        comments = assessment.get("field_comments") if isinstance(assessment.get("field_comments"), dict) else {}
        narrative.extend(_format_report_value(value) for value in comments.values()
                         if _format_report_value(value) and
                         not _is_placeholder_entry(_format_report_value(value)))
        narrative = _dedupe_report_items(narrative, merge_similar=True)
        if narrative:
            note = re.sub(r"\s*[\r\n]+\s*", "; ", narrative[0]).rstrip(". ")
            sentences.append(f"Additional respondent comments highlight {note}.")
        actions = _flatten_phase2_entries(assessment.get("priority_actions"))
        if not actions:
            actions = _flatten_phase2_entries(assessment.get("planned_enhancements"))
        actions = [action for action in actions if not _is_placeholder_entry(action)]
        if actions:
            sentences.append(f"Priority action: {actions[0].rstrip('. ')}.")
        summaries.append(" ".join(sentences))
    return summaries


def _phase2_gaps_and_risks(assessments):
    gaps = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        if _is_negative(assessment.get("data_policy")):
            gaps.append(f"{name}: no approved data policy is documented.")
        if _is_negative(assessment.get("security_controls")):
            gaps.append(f"{name}: security and privacy controls are not implemented.")
        if _is_negative(assessment.get("sop_available")):
            gaps.append(f"{name}: standard operating procedures are not available.")
        if _is_negative(assessment.get("user_manuals")):
            gaps.append(f"{name}: user manuals or job aids are not available.")
        if _is_negative(assessment.get("data_exchange")):
            gaps.append(f"{name}: data exchange with other systems is not supported.")
        if _is_negative(assessment.get("api_available")):
            gaps.append(f"{name}: API access is not available.")
        if _format_report_value(assessment.get("known_limitations")):
            gaps.append(f"{name}: {assessment.get('known_limitations')}")
        if _format_report_value(assessment.get("operational_challenges")):
            gaps.append(f"{name}: {assessment.get('operational_challenges')}")
    return _dedupe_report_items(gaps, merge_similar=True)


def _phase2_strengths(assessments):
    strengths = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        capabilities = _flatten_phase2_entries(assessment.get("retained_capabilities"))
        if capabilities:
            strengths.append(f"{name}: {', '.join(capabilities)}")
        if _is_affirmative(assessment.get("open_source")):
            strengths.append(f"{name}: open source or open standards are available.")
        if _is_affirmative(assessment.get("api_available")):
            strengths.append(f"{name}: API access is available.")
        if _is_affirmative(assessment.get("security_controls")):
            strengths.append(f"{name}: security and privacy controls are in place.")
        if _is_affirmative(assessment.get("sop_available")):
            strengths.append(f"{name}: standard operating procedures are available.")
        if _is_affirmative(assessment.get("user_manuals")):
            strengths.append(f"{name}: user manuals or job aids are available.")
    return _dedupe_report_items(strengths)


def _phase2_prioritised_recommendations(assessments):
    recommendations = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        actions = _flatten_phase2_entries(assessment.get("priority_actions"))
        for action in actions:
            recommendations.append(f"{name}: {action}")
    return _dedupe_report_items(recommendations)


def _phase2_action_plan(assessments):
    actions = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        enhancements = _flatten_phase2_entries(assessment.get("planned_enhancements"))
        for enhancement in enhancements:
            actions.append(f"{name}: {enhancement}")
    return _dedupe_report_items(actions)


def _phase2_data_quality_flags(assessments):
    flags = []
    for assessment in assessments:
        name = _format_report_value(assessment.get("official_name", "Unnamed")) or "Unnamed"
        # Negative answers belong in the gaps section. This section is reserved
        # for ambiguous or internally inconsistent profiling data.
        for field, label in (
            ("data_policy", "data access/use policy"),
            ("security_controls", "security and privacy controls"),
            ("sop_available", "standard operating procedures"),
            ("user_manuals", "user manuals or job aids"),
            ("api_available", "API availability"),
            ("data_exchange", "data exchange capability"),
        ):
            value = assessment.get(field)
            if _format_report_value(value) and _classify_yes_no(value) is None:
                flags.append(f'{name}: {label} has an unclear response ("{_format_report_value(value)}").')
        if _format_report_value(assessment.get("exchange_comments")) and _is_negative(assessment.get("data_exchange")):
            flags.append(f"{name}: exchange comments exist despite no data exchange support.")
    return _dedupe_report_items(flags)


def _is_dhis2_based(tool: Dict[str, object]) -> bool:
    technology = _format_report_value(tool.get("technology", "")).lower()
    if "dhis2" in technology:
        return True
    for system_type in tool.get("system_type", []):
        if "dhis2" in _format_report_value(system_type).lower():
            return True
    return False


def _is_paper_based(tool: Dict[str, object]) -> bool:
    for key in ("technology", "point_of_data_entry", "comments", "data_captured"):
        if "paper" in _format_report_value(tool.get(key, "")).lower():
            return True
    return False


def _is_national_scale(tool: Dict[str, object]) -> bool:
    return _is_national_coverage(tool.get("geographical_coverage", ""))


def _has_linked_systems(tool: Dict[str, object]) -> bool:
    return bool(_format_report_value(tool.get("linked_to_other_systems", "")))


def _generate_phase1_inventory_analysis(
    tools: List[Dict[str, object]],
    function_counts: Dict[str, int],
) -> List[str]:
    total_systems = len(tools)
    api_systems = sum(_is_api_enabled(tool.get("has_api", "")) for tool in tools)
    dhis2_systems = sum(_is_dhis2_based(tool) for tool in tools)
    paper_systems = sum(_is_paper_based(tool) for tool in tools)
    national_systems = sum(_is_national_scale(tool) for tool in tools)
    specialized_systems = total_systems - national_systems
    linked_systems = sum(_has_linked_systems(tool) for tool in tools)
    stand_alone_systems = total_systems - linked_systems

    data_type_counts = {
        "Aggregate": 0,
        "Case-based": 0,
        "Mixed (Aggregate & Case-based)": 0,
        "Event-based only": 0,
    }
    for tool in tools:
        system_types = [
            _format_report_value(entry).lower()
            for entry in tool.get("system_type", [])
            if _format_report_value(entry)
        ]
        has_aggregate = any("aggregate" in item for item in system_types)
        has_case = any("case" in item for item in system_types)
        has_event = any("event" in item for item in system_types)

        if has_aggregate and has_case:
            data_type_counts["Mixed (Aggregate & Case-based)"] += 1
        elif has_aggregate:
            data_type_counts["Aggregate"] += 1
        elif has_case:
            data_type_counts["Case-based"] += 1
        elif has_event:
            data_type_counts["Event-based only"] += 1

    analysis_lines: List[str] = []
    analysis_lines.append("Overview of the HIS Inventory")
    analysis_lines.extend(format_ascii_table(
        ["Indicator", "Value"],
        [
            ["Total systems identified", str(total_systems)],
            ["Systems with APIs", str(api_systems)],
            ["DHIS2-based systems", str(dhis2_systems)],
            ["Stand-alone systems", str(stand_alone_systems)],
            ["Paper-based systems", str(paper_systems)],
            ["National-scale systems", str(national_systems)],
            ["Specialized/program-specific systems", str(specialized_systems)],
        ],
    ))
    analysis_lines.append("")

    analysis_lines.append("System Distribution by Data Type")
    data_type_rows = []
    for data_type in ["Aggregate", "Case-based", "Mixed (Aggregate & Case-based)", "Event-based only"]:
        count = data_type_counts.get(data_type, 0)
        percent = round((count / total_systems) * 100) if total_systems else 0
        data_type_rows.append([data_type, str(count), f"{percent}%"])
    analysis_lines.extend(format_ascii_table(["Data Type", "Number", "Percentage"], data_type_rows))
    analysis_lines.append("")

    analysis_lines.append("Distribution of Surveillance Functions")
    function_rows = []
    for function_name, count in sorted(
        function_counts.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        percent = round((count / total_systems) * 100) if total_systems else 0
        function_rows.append([function_name, str(count), f"{percent}%"])
    if function_rows:
        analysis_lines.extend(format_ascii_table(["Surveillance Function", "No. of Systems", "Percentage"], function_rows))
    analysis_lines.append("")

    analysis_lines.append("Integration Status")
    integration_rows = [
        ["Systems with API", str(api_systems)],
        ["Systems linked to other systems", str(linked_systems)],
        ["Stand-alone systems", str(stand_alone_systems)],
        ["Paper-based workflows", str(paper_systems)],
    ]
    analysis_lines.extend(format_ascii_table(["Integration Characteristic", "Number"], integration_rows))
    return analysis_lines


def _append_phase2_report(
    line_items: List[str], assessments: List[Dict[str, object]], inventory_total: Optional[int] = None
) -> None:
    if not assessments:
        return

    line_items.append("")
    line_items.append("Profiling")
    line_items.append(
        "Profiling builds on the Inventory and focuses on assessment completeness, capability scores, "
        "identified gaps and risks, strengths to retain, prioritised recommendations, action planning, and data-quality flags."
    )
    line_items.append(
        "Refer to the Inventory for system details, platform and ownership information, inventory totals, function distribution, "
        "geographic coverage, data type distribution, technology distribution, API/integration counts, and primary user groups."
    )
    line_items.append("")

    line_items.append("Surveillance System Profiling: Summary Report")
    system_count = len(assessments)
    national_count = sum(1 for assessment in assessments
                         if _is_national_coverage(assessment.get("coverage_level")))
    api_count = sum(1 for assessment in assessments if _is_affirmative(assessment.get("api_available")))
    exchange_count = sum(1 for assessment in assessments if _is_affirmative(assessment.get("data_exchange")))
    percent = lambda count: round((count / system_count) * 100) if system_count else 0
    national_phrase = f"All {system_count}" if national_count == system_count else str(national_count)
    line_items.append(
        f"Overview: The assessment profiled {system_count} surveillance system{'s' if system_count != 1 else ''}. "
        f"{national_phrase} reported national coverage, {api_count} ({percent(api_count)}%) reported API access, and "
        f"{exchange_count} ({percent(exchange_count)}%) reported exchanging data with other systems."
    )
    capability_fields = [
        ("captures_signals", "signal detection"), ("case_notifications", "case notification"),
        ("case_investigation", "case investigation"), ("lab_results", "laboratory reporting"),
        ("contact_followup", "contact tracing"), ("dashboards_surveillance", "dashboards"),
        ("situation_reports", "situation reporting"),
    ]
    capabilities = [label for key, label in capability_fields if any(_is_affirmative(item.get(key)) for item in assessments)]
    line_items.append(
        "Key capabilities: Reported functions include " + _natural_join(capabilities) + ". Capabilities vary across systems."
    )
    summary_gap_fields = [
        ("contact_identification", "contact identification"),
        ("contact_followup", "contact follow-up"),
        ("specimen_tracking", "specimen tracking"),
        ("lab_results", "laboratory-result capture"),
        ("offline_access", "offline operation"),
        ("data_exchange", "data exchange"),
        ("sop_available", "standard operating procedures"),
        ("user_manuals", "user manuals or job aids"),
    ]
    recurring_gaps = [label for key, label in summary_gap_fields if any(_is_negative(item.get(key)) for item in assessments)][:5]
    challenge_text = " ".join(_format_report_value(item.get("operational_challenges")) for item in assessments).casefold()
    challenge_themes = []
    for pattern, label in [
        (r"fund|budget", "limited funding"), (r"internet|network|connect", "unreliable connectivity"),
        (r"equipment|tool|resource|storage", "insufficient equipment"),
        (r"train|capacity|knowledge", "training needs"), (r"ownership", "data ownership concerns"),
    ]:
        if re.search(pattern, challenge_text): challenge_themes.append(label)
    gap_summary = (
        "Across the profiled surveillance systems, recurring functional gaps were reported in "
        + _natural_join(recurring_gaps) + "."
        if recurring_gaps else "No recurring functional gap was identified across the profiled surveillance systems."
    )
    line_items.append(
        "Main gaps and challenges: " + gap_summary + " "
        + ("Reported implementation challenges include " + _natural_join(challenge_themes) + "." if challenge_themes else "No recurring implementation challenge theme was identified.")
    )
    actions = " ".join(
        entry for assessment in assessments
        for entry in (_flatten_phase2_entries(assessment.get("priority_actions")) or _flatten_phase2_entries(assessment.get("planned_enhancements")))
        if not _is_placeholder_entry(entry)
    ).casefold()
    action_themes = []
    for pattern, label in [
        (r"train|capacity", "user training and technical capacity development"),
        (r"dashboard", "dashboard development"), (r"integrat|testing platform", "integration with testing platforms"),
        (r"roll.?out|point.?of.?entry|\bpoe\b", "expansion of digital screening to designated points of entry"),
        (r"incent", "incentives for call handlers"),
    ]:
        if re.search(pattern, actions): action_themes.append(label)
    phase_out = any(
        "ewars" in _format_report_value(item.get("official_name")).casefold()
        and re.search(r"phas(?:e|ed|ing)\s*out", " ".join(
            _flatten_phase2_entries(item.get("priority_actions")) or _flatten_phase2_entries(item.get("planned_enhancements"))
        ).casefold())
        for item in assessments
    )
    action_sentence = "Reported priority actions: Actions include " + _natural_join(action_themes) + "."
    if phase_out: action_sentence += " EWARS is reported to be undergoing phase-out."
    line_items.append(action_sentence)
    airport_issue = any(
        _is_national_coverage(item.get("coverage_level"))
        and re.search(r"airport|juba international", " ".join(
            _format_report_value(value) for key, value in item.items() if key not in PHASE2_INTERNAL_FIELDS
        ).casefold())
        for item in assessments
    )
    paper_issue = any(
        "paper" in _format_report_value(item.get("platforms")).casefold()
        and any(_is_affirmative(item.get(key)) for key in ("api_available", "automated_alerts", "dashboards_surveillance"))
        for item in assessments
    )
    validation_items = []
    if airport_issue: validation_items.append("national coverage reported for an airport-only deployment")
    if paper_issue: validation_items.append("digital capabilities attributed to a paper-based screening form")
    validation_intro = "Some entries require clarification before finalization"
    if validation_items: validation_intro += ", particularly " + _natural_join(validation_items)
    line_items.append(
        "Data validation: " + validation_intro + ". Missing functions should also be assessed against each system's intended purpose before being classified as gaps."
    )
    line_items.append("")

    completeness_rows = _phase2_assessment_completeness(assessments)
    line_items.append("Assessment completeness")
    if completeness_rows:
        line_items.extend(format_ascii_table(
            ["System", "Fields Completed", "Total Fields", "Completeness"],
            [[name, str(filled), str(total), percent] for name, filled, total, percent in completeness_rows],
        ))
    else:
        line_items.append("- No Profiling assessment completeness data is available.")
    line_items.append("")

    domain_rows = _phase2_domain_scores(assessments)
    line_items.append("Domain capability scores")
    if domain_rows:
        line_items.extend(format_ascii_table(
            ["Domain", "Affirmative response rate", "Affirmative answers", "Scored yes/no answers"],
            [[domain, score, str(positive), str(total)] for domain, total, positive, score in domain_rows],
        ))
        profile_total = len(assessments)
        exchange_count = sum(1 for item in assessments if _is_affirmative(item.get("data_exchange")))
        line_items.append(
            "Interpretation note: Domain rates use affirmative answers divided by scored yes/no answers across "
            f"{profile_total} profiled system{'s' if profile_total != 1 else ''}. The answer counts are not system counts. "
            f"Data exchange specifically was reported by {exchange_count} of {profile_total} profiled "
            f"system{'s' if profile_total != 1 else ''}."
        )
        if inventory_total is not None:
            unprofiled = max(0, inventory_total - profile_total)
            line_items.append(
                f"Inventory context: {inventory_total} system{'s were' if inventory_total != 1 else ' was'} recorded in the Inventory; "
                f"{profile_total} had Profiling responses and {unprofiled} did not. Profiling rates and counts use only the "
                f"{profile_total} profiled system{'s' if profile_total != 1 else ''}."
            )
    else:
        line_items.append("- No applicable yes/no questions were found for domain scoring.")
    line_items.append("")

    gaps = _phase2_gaps_and_risks(assessments)
    line_items.append("Identified gaps and risks")
    if gaps:
        for item in gaps:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No specific gaps or risks were identified from Profiling.")
    line_items.append("")

    strengths = _phase2_strengths(assessments)
    line_items.append("Strengths to retain")
    if strengths:
        for item in strengths:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No strengths were captured in the Profiling data.")
    line_items.append("")

    recommendations_rows = _phase2_prioritised_recommendations(assessments)
    line_items.append("Prioritised recommendations")
    if recommendations_rows:
        for item in recommendations_rows:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No prioritised recommendations were recorded.")
    line_items.append("")

    action_plan_rows = _phase2_action_plan(assessments)
    line_items.append("Action plan")
    if action_plan_rows:
        for item in action_plan_rows:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No action plan items were recorded.")
    line_items.append("")

    flags = _phase2_data_quality_flags(assessments)
    line_items.append("Data-quality and consistency flags")
    if flags:
        for item in flags:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No data-quality or consistency flags were detected from the assessment.")


def generate_report(profile: Dict[str, str], findings: List[str], recommendations: List[str]) -> str:
    line_items: List[str] = []
    line_items.append("Surveillance Profile Report")
    line_items.append(f"Country: {profile.get('country_name', profile.get('facility_name', 'N/A'))}")
    line_items.append(f"Reporting Period: {profile.get('reporting_period', 'N/A')}")
    line_items.append("")

    tools = [
        tool for tool in (profile.get("tools", []) or [])
        if isinstance(tool, dict) and _format_report_value(tool.get("inventory_name", ""))
    ]
    total_tools = len(tools)
    line_items.append("Executive Summary")
    if total_tools:
        line_items.append(
            f"This summary provides an overview of the surveillance digital tool portfolio captured for "
            f"{profile.get('country_name', 'the country')} during {profile.get('reporting_period', 'the reporting period')}.")
    else:
        line_items.append("No systems were captured in the Inventory.")

    tool_fields = [
        "inventory_name",
        "unit_responsible",
        "system_type",
        "surveillance_functions",
        "geographical_coverage",
        "point_of_data_entry",
        "data_captured",
        "information_users",
        "technology",
        "has_api",
        "linked_to_other_systems",
        "comments",
    ]
    completeness_by_tool: List[Dict[str, object]] = []
    system_type_counts: Dict[str, int] = {}
    function_counts: Dict[str, int] = {}
    coverage_counts: Dict[str, int] = {}
    data_capture_details: List[str] = []

    for tool in tools:
        filled = 0
        missing_fields: List[str] = []
        for field in tool_fields:
            value = tool.get(field)
            if isinstance(value, list):
                if value:
                    filled += 1
                else:
                    missing_fields.append(field.replace("_", " "))
            elif value is not None and str(value).strip():
                filled += 1
            else:
                missing_fields.append(field.replace("_", " "))

        completeness_by_tool.append(
            {
                "name": tool.get("inventory_name", "Unnamed") or "Unnamed",
                "filled": filled,
                "total": len(tool_fields),
                "missing": missing_fields,
            }
        )

        for system_type in tool.get("system_type", []):
            system_type_counts[system_type] = system_type_counts.get(system_type, 0) + 1
        for surveillance_function in tool.get("surveillance_functions", []):
            function_counts[surveillance_function] = function_counts.get(surveillance_function, 0) + 1
        coverage_key = tool.get("geographical_coverage", "Unknown") or "Unknown"
        coverage_counts[coverage_key] = coverage_counts.get(coverage_key, 0) + 1
        data_captured = tool.get("data_captured", "").strip()
        if data_captured:
            data_capture_details.append(f"{tool.get('inventory_name', 'Unnamed')}: {data_captured}")

    if function_counts:
        most_common_function, most_common_function_count = max(function_counts.items(), key=lambda item: (item[1], item[0]))
        line_items.append(
            f"The most widely supported surveillance function is {most_common_function}, available in {most_common_function_count} system{'s' if most_common_function_count != 1 else ''}."
        )
    if system_type_counts:
        most_common_type, most_common_type_count = max(system_type_counts.items(), key=lambda item: (item[1], item[0]))
        line_items.append(
            f"The most common digital distribution type is {most_common_type}, used by {most_common_type_count} system{'s' if most_common_type_count != 1 else ''}."
        )
    if total_tools:
        average_functions = sum(len(tool.get("surveillance_functions", [])) for tool in tools) / total_tools
        top_systems = sorted(
            tools,
            key=lambda tool: (-len(tool.get("surveillance_functions", [])), tool.get("inventory_name", ""))
        )[:3]
        line_items.append(
            f"The average number of surveillance functions per system is {average_functions:.1f}."
        )
        if top_systems:
            top_reports = [
                f"{tool.get('inventory_name', 'Unnamed')} ({len(tool.get('surveillance_functions', []))} functions)"
                for tool in top_systems
            ]
            line_items.append(
                f"Top three systems with the highest functionality are: {', '.join(top_reports)}."
            )

        # Coverage values may be recorded as "National", "National geographic",
        # or another National-qualified label. Use the same classification as the
        # summary count so the narrative cannot contradict it.
        national_tools = [tool for tool in tools if _is_national_scale(tool)]
        if national_tools:
            top_national = max(national_tools, key=lambda tool: len(tool.get("surveillance_functions", [])))
            line_items.append(
                f"The national-coverage system supporting the most surveillance functions is {top_national.get('inventory_name', 'Unnamed')}, with {len(top_national.get('surveillance_functions', []))} functions."
            )
        else:
            line_items.append("No systems were recorded with national coverage.")

    if findings:
        line_items.append("")
        line_items.append("Key findings from the Inventory:")
        for item in findings:
            line_items.append(f"- {item}")

    line_items.append("")
    line_items.append("Data completeness by system")
    completeness_rows = []
    for item in completeness_by_tool:
        tool = next((tool for tool in tools if (tool.get("inventory_name", "Unnamed") or "Unnamed") == item["name"]), {})
        percent = round((item["filled"] / item["total"]) * 100) if item["total"] else 0
        missing_text = ", ".join(item["missing"]) if item["missing"] else "none"
        completeness_rows.append([
            item["name"],
            str(item["filled"]),
            str(item["total"]),
            f"{percent}%",
            missing_text,
        ])
    line_items.extend(format_ascii_table([
        "System",
        "Fields Completed",
        "Total Fields",
        "Completeness",
        "Missing Fields",
    ], completeness_rows))

    if function_counts:
        line_items.append("")
        line_items.append("System by function support")
        function_rows = []
        for surveillance_function, count in sorted(function_counts.items(), key=lambda item: (-item[1], item[0])):
            percent = int((count / total_tools) * 100) if total_tools else 0
            names = [tool.get('inventory_name', 'Unnamed') or 'Unnamed' for tool in tools if surveillance_function in tool.get('surveillance_functions', [])]
            function_rows.append([
                surveillance_function,
                str(count),
                f"{percent}%",
                ", ".join(names),
            ])
        line_items.extend(format_ascii_table([
            "Function",
            "Systems",
            "Percent",
            "Systems with Function",
        ], function_rows))

    if tools:
        line_items.append("")
        line_items.extend(_generate_phase1_inventory_analysis(tools, function_counts))

    line_items.append("")
    line_items.append("Recommendations")
    if recommendations:
        for item in recommendations:
            line_items.append(f"- {item}")
    else:
        line_items.append("- No recommendations were recorded.")

    phase2_assessments = _normalize_phase2_assessments(profile.get("phase2") or [])

    if tools and not phase2_assessments:
        line_items.append("")
        line_items.append("Inventory Details")
        line_items.append(f"Total systems in use: {total_tools}")

        data_type_counts = {
            "Aggregate": 0,
            "Case-based": 0,
            "Mixed (Aggregate & Case-based)": 0,
            "Event-based only": 0,
        }
        for tool in tools:
            system_types = [
                _format_report_value(entry).lower()
                for entry in tool.get("system_type", [])
                if _format_report_value(entry)
            ]
            has_aggregate = any("aggregate" in item for item in system_types)
            has_case = any("case" in item for item in system_types)
            has_event = any("event" in item for item in system_types)
            if has_aggregate and has_case:
                data_type_counts["Mixed (Aggregate & Case-based)"] += 1
            elif has_aggregate:
                data_type_counts["Aggregate"] += 1
            elif has_case:
                data_type_counts["Case-based"] += 1
            elif has_event:
                data_type_counts["Event-based only"] += 1

        line_items.append("Digital distribution type counts:")
        for data_type in ["Aggregate", "Case-based", "Mixed (Aggregate & Case-based)", "Event-based only"]:
            line_items.append(f"- {data_type}: {data_type_counts.get(data_type, 0)}")

        if function_counts:
            line_items.append("Surveillance function counts:")
            for surveillance_function, count in sorted(function_counts.items(), key=lambda item: (-item[1], item[0])):
                line_items.append(f"- {surveillance_function}: {count}")

        if coverage_counts:
            line_items.append("Coverage by geography:")
            for coverage, count in sorted(coverage_counts.items(), key=lambda item: (-item[1], item[0])):
                line_items.append(f"- {coverage}: {count}")

        if data_capture_details:
            line_items.append("Data capture by system:")
            for entry in data_capture_details:
                line_items.append(f"- {entry}")

        shared_functions: Dict[str, List[str]] = {}
        for tool in tools:
            tool_name = tool.get("inventory_name", "Unnamed")
            for surveillance_function in tool.get("surveillance_functions", []):
                shared_functions.setdefault(surveillance_function, []).append(tool_name)

        shared_functions = {func: names for func, names in shared_functions.items() if len(names) > 1}
        if shared_functions:
            line_items.append("Systems sharing surveillance functions:")
            for func, names in sorted(shared_functions.items(), key=lambda item: (-len(item[1]), item[0])):
                line_items.append(f"- {func}: {', '.join(names)}")

        line_items.append("")
        line_items.append("Detailed Inventory:")
        for index, tool in enumerate(tools, start=1):
            line_items.append("")
            line_items.append(f"Tool {index}: {tool.get('inventory_name', 'N/A')}")
            for label, key in [
                ("Unit Responsible", "unit_responsible"), ("Type of System", "system_type"),
                ("Surveillance Functions", "surveillance_functions"), ("Geographical Coverage", "geographical_coverage"),
                ("Point of Data Entry", "point_of_data_entry"), ("Data Captured", "data_captured"),
                ("Information Users", "information_users"), ("Technology", "technology"),
                ("Has API", "has_api"), ("Linked to Other Systems", "linked_to_other_systems"),
                ("Comments", "comments"),
            ]:
                value = _format_report_value(tool.get(key, ""))
                if value:
                    line_items.append(f"- {label}: {value}")

    if phase2_assessments:
        _append_phase2_report(line_items, phase2_assessments, total_tools)

    return "\n".join(line_items)


def format_ascii_table(headers: List[str], rows: List[List[str]]) -> List[str]:
    if not rows:
        return []
    # Keep every logical record on one physical line. Presentation layers can
    # wrap text inside the cell without creating false, apparently empty rows.
    clean = lambda value: " ".join(str(value or "").split()).replace("|", "/")
    lines = [
        "| " + " | ".join(clean(value) for value in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(clean(row[index]) if index < len(row) else "" for index in range(len(headers))) + " |"
        for row in rows
        if any(clean(value) for value in row)
    )
    return lines


class ProfileStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or Path(__file__).with_name("profiles.json")

    def load(self) -> List[Dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, profiles: List[Dict[str, str]]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(profiles, handle, indent=2)


def build_profile_payload(form_data: Dict[str, str]) -> Dict[str, str]:
    return {
        "country_name": form_data.get("country_name", ""),
        "reporting_period": form_data.get("reporting_period", ""),
        "lead_team_member_name2": form_data.get("lead_team_member_name2", ""),
        "tools": form_data.get("tools", []),
        "findings": form_data.get("findings", ""),
        "recommendations": form_data.get("recommendations", ""),
        "phase2": form_data.get("phase2", {}),
    }


def parse_multiline(value: str) -> List[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


if __name__ == "__main__":
    print("Surveillance app module ready")
