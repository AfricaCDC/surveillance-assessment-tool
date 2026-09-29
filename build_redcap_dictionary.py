import csv
from pathlib import Path

SOURCE = Path(r"C:\Users\George\Downloads\AfricaCDCSurveillanceSystemsPr_DataDictionary_2026-08-08.csv")
OUTPUT_DIR = Path("outputs/redcap")
OUTPUT = OUTPUT_DIR / "Africa_CDC_REDCap_Data_Dictionary.csv"

with SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
    headers = next(csv.reader(handle))

if len(headers) != 18 or headers[0] != "Variable / Field Name" or headers[1] != "Form Name":
    raise SystemExit("Unexpected REDCap Data Dictionary header structure")

rows = []

def add(name, form, label, field_type="text", choices="", section="", note="", validation="",
        required="", identifier="", branching="", annotation=""):
    if len(name) > 26:
        raise ValueError(f"REDCap field name exceeds 26 characters: {name}")
    rows.append([
        name, form, section, field_type, label, choices, note, validation, "", "",
        identifier, branching, required, "", "", "", "", annotation,
    ])

# One record represents one country and reporting period.
add("record_id", "country_assessment", "Assessment ID", section="Country assessment",
    note="Stable ID supplied by the application, e.g. GHA-2026.", required="y")
add("country_name", "country_assessment", "Country", required="y")
add("reporting_period", "country_assessment", "Reporting period", required="y")
add("assessment_title", "country_assessment", "Assessment title")
add("assessment_scope", "country_assessment", "Assessment scope or context", "notes")
add("assessment_status", "country_assessment", "Assessment status", "dropdown",
    "draft, Draft | active, Active | complete, Complete | archived, Archived", required="y")
add("created_at", "country_assessment", "Created at", validation="datetime_seconds_ymd")
add("updated_at", "country_assessment", "Last updated at", validation="datetime_seconds_ymd")

# Repeating: one instance for every phase-specific working group.
add("wg_group_id", "working_groups", "Application group ID", section="Working group")
add("wg_phase", "working_groups", "Assessment phase", "dropdown",
    "inventory, Inventory | profiling, Profiling | gap, Gap Analysis", required="y")
add("wg_group_name", "working_groups", "Group name", required="y")
add("wg_username", "working_groups", "Generated application username",
    note="Password is intentionally not stored in REDCap.")
add("wg_active", "working_groups", "Account active", "yesno")
add("wg_created_at", "working_groups", "Group created at", validation="datetime_seconds_ymd")

# Repeating: one instance per inventory tool/system.
add("inv_tool_id", "inventory_tools", "Application tool ID", section="Inventory tool")
add("inv_tool_name", "inventory_tools", "Tool / system name", required="y")
add("inv_unit", "inventory_tools", "Unit responsible")
add("inv_system_type", "inventory_tools", "Type of system", "notes")
add("inv_surv_functions", "inventory_tools", "Surveillance functions", "notes")
add("inv_geo_coverage", "inventory_tools", "Geographical coverage")
add("inv_data_entry", "inventory_tools", "Point of data entry")
add("inv_data_captured", "inventory_tools", "Data captured", "notes")
add("inv_info_users", "inventory_tools", "Information users", "notes")
add("inv_technology", "inventory_tools", "Technology")
add("inv_has_api", "inventory_tools", "Has API", "yesno")
add("inv_linked_systems", "inventory_tools", "Linked to other systems", "notes")
add("inv_comments", "inventory_tools", "Comments", "notes")
add("inv_entered_by", "inventory_tools", "Entered by application username")
add("inv_updated_at", "inventory_tools", "Last updated at", validation="datetime_seconds_ymd")

profile_fields = {
    "official_name":"Official name, local name or acronym", "platforms":"Underlying platform(s)",
    "implementation_status":"Current implementation status", "year_implemented":"Year first implemented",
    "surveillance_approaches":"Surveillance approaches", "diseases_supported":"Diseases or conditions supported",
    "captures_signals":"Captures signals", "captures_verification":"Captures signal verification",
    "alert_risk_assessment":"Supports alert risk assessment", "case_notifications":"Case notifications",
    "unique_identifier":"Unique patient or case identifier", "case_investigation":"Case investigation",
    "specimen_requests":"Specimen requests", "specimen_tracking":"Specimen tracking",
    "lab_results":"Laboratory results", "lab_results_received":"How laboratory results are received",
    "contact_identification":"Contact identification", "contact_followup":"Contact follow-up",
    "dashboards_surveillance":"Surveillance dashboards", "gis_mapping":"GIS mapping",
    "epidemic_curves":"Epidemic curves", "trend_analysis":"Trend analysis",
    "hotspot_analysis":"Hotspot analysis", "contact_dashboards":"Contact dashboards",
    "lab_dashboards":"Laboratory dashboards", "mortality_dashboards":"Mortality dashboards",
    "custom_visualisations":"Custom visualisations", "automated_alerts":"Automated alerts",
    "threshold_monitoring":"Threshold monitoring", "line_lists":"Line lists",
    "situation_reports":"Situation reports", "weekly_reports":"Weekly reports",
    "monthly_reports":"Monthly reports", "scheduled_reports":"Scheduled reports",
    "bulletin_outputs":"Bulletin outputs", "excel_export":"Excel export", "pdf_export":"PDF export",
    "api_access":"API access", "primary_users":"Primary users", "active_users":"Number of active users",
    "coverage_level":"Coverage level", "district_count":"Number of districts covered",
    "facility_count":"Number of facilities covered", "web_access":"Web access",
    "mobile_interface":"Mobile interface", "offline_access":"Offline access",
    "api_available":"API available", "open_source":"Open source", "hosting_model":"Hosting model",
    "data_exchange":"Data exchange and interoperability", "ownership_institution":"Owning institution",
    "hosting_institution":"Hosting institution", "sop_available":"Standard operating procedures available",
    "user_manuals":"User manuals or job aids available", "data_policy":"Data policy available",
    "security_controls":"Security and privacy controls", "emergency_support":"Emergency response support",
    "supported_events":"Events supported", "lessons_learned":"Emergency-response lessons learned",
    "technical_support":"Technical support", "expertise_sufficient":"Sufficient local expertise",
    "funding_source":"Funding source", "retained_capabilities":"Capabilities to retain",
    "operational_challenges":"Operational challenges", "planned_enhancements":"Planned enhancements",
    "implementation_lessons":"Implementation lessons", "known_limitations":"Known limitations",
    "priority_actions":"Priority actions", "other_information":"Other information",
}

add("prof_tool_id", "system_profiling", "Application tool ID", section="System profiling")
for key, label in profile_fields.items():
    field_type = "notes" if key in {
        "platforms", "surveillance_approaches", "diseases_supported", "lab_results_received",
        "primary_users", "coverage_level", "data_exchange", "security_controls", "supported_events",
        "lessons_learned", "technical_support", "funding_source", "retained_capabilities",
        "operational_challenges", "planned_enhancements", "implementation_lessons", "known_limitations",
        "priority_actions", "other_information",
    } else "text"
    add(key, "system_profiling", label, field_type, required="y" if key == "official_name" else "")
add("prof_entered_by", "system_profiling", "Entered by application username")
add("prof_updated_at", "system_profiling", "Last updated at", validation="datetime_seconds_ymd")

# Repeating: assignments for inventory tools, profiling tools and gap domains.
add("assign_phase", "work_assignments", "Assessment phase", "dropdown",
    "inventory, Inventory | profiling, Profiling | gap, Gap Analysis", section="Work assignment", required="y")
add("assign_item_id", "work_assignments", "Assigned tool or domain ID", required="y")
add("assign_item_name", "work_assignments", "Assigned tool or domain name")
add("assign_group_id", "work_assignments", "Assigned group ID", required="y")
add("assign_group_name", "work_assignments", "Assigned group name")
add("assigned_at", "work_assignments", "Assigned at", validation="datetime_seconds_ymd")

# Repeating: one instance per gap-analysis question response.
add("gap_domain_id", "gap_analysis_responses", "Domain ID", section="Gap-analysis response", required="y")
add("gap_domain_name", "gap_analysis_responses", "Domain name")
add("gap_question_id", "gap_analysis_responses", "Question ID", required="y")
add("gap_question_text", "gap_analysis_responses", "Question", "notes")
add("gap_response", "gap_analysis_responses", "Response", "notes")
add("gap_explanation", "gap_analysis_responses", "Explanation", "notes")
add("gap_comment", "gap_analysis_responses", "Comment", "notes")
add("gap_group_id", "gap_analysis_responses", "Entry group ID")
add("gap_group_name", "gap_analysis_responses", "Entry group name")
add("gap_entered_by", "gap_analysis_responses", "Entered by application username")
add("gap_updated_at", "gap_analysis_responses", "Last updated at", validation="datetime_seconds_ymd")

names = [row[0] for row in rows]
if len(names) != len(set(names)):
    raise SystemExit("Duplicate REDCap variable names detected")
forms = [row[1] for row in rows]
expected_forms = {
    "country_assessment", "working_groups", "inventory_tools", "system_profiling",
    "work_assignments", "gap_analysis_responses",
}
if set(forms) != expected_forms:
    raise SystemExit("Instrument set validation failed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Created {OUTPUT.resolve()}")
print(f"Fields: {len(rows)}")
for form in sorted(expected_forms):
    print(f"{form}: {forms.count(form)}")
