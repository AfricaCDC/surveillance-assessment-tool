# Changelog

All controlled releases of the Africa CDC Surveillance Digital Tools Assessment Web Application are recorded here.

## [Unreleased]

- When a real country-period assessment already exists, prompt the user to open it for updating instead of stopping at a duplicate error.
- Reopening Test Country for the same reporting period now resets its disposable in-memory workspace instead of reporting that a saved assessment already exists.
- Test Country logout now clearly discards the temporary workspace and does not attempt a REDCap save.
- Restored the earlier six-column Unified DHIS2 comparison matrix, including Country validation gap and Proposed tool disposition.
- Ensure Unified DHIS2 comparisons receive real named Inventory records from every report section instead of placeholder system labels.
- Keep a compact per-tool evidence set so large inventories retain names and recorded functions during local AI analysis.
- Updated the in-app User Manual and Admin Guide, source/user/deployment/update documentation, packaging readme files, folder reference, and Word regression register through version 1.0.40.

## [1.0.40] - 2026-08-26

- Remove the duplicate **Open-ended themes** shortcut from the Report Assistant header.
- Retain the broader **Thematic analysis** shortcut and free-text assistant questions.

## [1.0.39] - 2026-08-26

- Clarify that Profiling domain scores use affirmative yes/no answer counts, not system counts.
- Report the system-level data-exchange count separately from the domain score.
- State the Inventory total, Profiling denominator, and number of unprofiled systems together.
- Exclude narrative comment fields from yes/no capability scoring and prevent the Report Assistant from converting response counts into systems.

## [1.0.38] - 2026-08-26

- Make the application's adjacent `.env` file authoritative for password security configuration in every launch mode.
- Prevent terminal, shortcut, and packaged launches from inheriting a different password pepper and rejecting a valid password.
- Rehash the existing administrator password against the stable application configuration without changing the password.

## [1.0.37] - 2026-08-26

- Keep assessments named `Test Country` temporary in application memory and never send them to REDCap.
- Show an explicit `temporary only - not saved to REDCap` status after Test Country edits and imports.
- Continue saving real Member State assessments directly to REDCap.

## [1.0.36] - 2026-08-26

- Compact recommendation evidence before sending it to the CPU-based local AI model.
- Use a shorter recommendation-specific instruction prompt and context to reduce first-response timeouts.
- Retain evidence-to-action traceability and complete-output requirements in the compact prompt.

## [1.0.35] - 2026-08-26

- Ensure consolidated recommendation requests receive enough output capacity to finish.
- Require every recommendation to cite explicit supporting findings and explain the evidence-to-action link.
- Prevent unsupported findings from being introduced or incorrectly attributed to named systems.

## [1.0.34] - 2026-08-26

- Clarify that the Profiling summary's recurring functional gaps are reported across the profiled systems and do not necessarily apply to every system.

## [1.0.33] - 2026-08-26

- Count only explicit national-level Profiling coverage responses as national.
- Exclude blank, unanswered, state-level, and subnational responses from the national total.

## [1.0.32] - 2026-08-26

- Display unanswered Profiling dropdown questions explicitly as `No response`.
- Keep the underlying value empty so unanswered coverage is not saved or counted as `National`.
- Apply the explicit no-response display consistently to all select questions.

## [1.0.31] - 2026-08-26

- Format the Profiling summary as Overview, Key capabilities, Main gaps and challenges, Reported priority actions, and Data validation.
- Calculate summary counts and percentages from imported Profiling responses.
- Highlight data-validation concerns without treating every missing function as a confirmed gap.

## [1.0.30] - 2026-08-26

- Preserve the blank option when Profiling dropdown choices are combined with imported values.
- Stop unanswered geographic-coverage questions from displaying `National` by default.
- Apply the correction to all unanswered Profiling dropdown questions.

## [1.0.29] - 2026-08-26

- Replace lengthy system-by-system Profiling summary paragraphs with a concise three-point portfolio summary.
- Summarise coverage and integration, the three most frequent recorded gaps, and counts of challenges, limitations, and priority actions.
- Retain system-level evidence in the detailed report sections instead of duplicating it in the summary.

## [1.0.28] - 2026-08-26

- Count `National scale`, `National level`, and equivalent values as national geographic coverage.
- Report the correct national-coverage numerator against the complete Inventory denominator.
- Exclude nationally deployed systems from the limited-coverage list.

## [1.0.27] - 2026-08-26

- Prevent automatic country refresh from overwriting the display while an Excel import is running.
- Stop interpreting row-1 Inventory column headings as country and reporting-period metadata.
- Keep the selected Member State and period while immediately displaying newly imported tools.

## [1.0.26] - 2026-08-26

- Treat the newly imported Inventory as the authoritative system list.
- Prevent stale or unmatched Profiling tabs from creating additional tools.
- Continue matching minor differences in Profiling and Inventory system names, but ignore profiles that cannot be matched.

## [1.0.25] - 2026-08-26

- Reload the authoritative application state immediately after a successful standard Excel import.
- Display imported Inventory and Profiling data without requiring a browser refresh.
- Reset import selectors and open the relevant data-collection screen after import.

## [1.0.24] - 2026-08-26

- Add a Change Password option for every signed-in user.
- Require the current password and enforce the configured password-strength rules.
- End existing sessions after a successful password change.

## [1.0.23] - 2026-08-26

- Prevent Member State assessment data from being persisted in the local SQLite database.
- Keep country records, inventory, profiling, assignments, and gap-analysis responses in memory only and reload them from REDCap.
- Preserve only authentication sessions and application configuration locally.

## [1.0.22] - 2026-08-26

### Changed

- Match the Profiling form to the Excel `Response` plus `Comments` structure for every A1–L1 question.
- Display, edit, and save question-level comments beside their corresponding responses.
- Remove redundant standalone imported-comments and G7-comments questions while preserving their data in the per-question comments structure.

## [1.0.21] - 2026-08-26

### Changed

- Remove the `no Profiling responses` suffix from system names in the Profiling selector.

## [1.0.20] - 2026-08-26

### Changed

- Use the Inventory system name as the canonical `System being assessed` name in Profiling.
- Match Profiling names to Inventory using worksheet names, normalized aliases, explicit acronyms, and unambiguous acronym expansion.
- Prevent minor spelling and naming differences from creating detached or duplicate Profiling systems.

## [1.0.19] - 2026-08-26

### Fixed

- Open the first populated Profiling system automatically after a standard Excel import.
- Reset stale Inventory and Profiling selection indexes after importing a different workbook.
- Label Inventory systems with no completed Profiling responses in the system selector.

## [1.0.18] - 2026-08-26

### Fixed

- Create Inventory system entries from A1 when importing a Profiling-only workbook without an Inventory sheet.
- Complete the Phase 1 step instead of stopping with `No Inventory table was found` before Profiling data is attached.

## [1.0.17] - 2026-08-26

### Fixed

- Exclude internal blank project placeholders from the country assessment dropdown.
- Prevent empty country or reporting-period values from rendering as `Unnamed country · No period`.

## [1.0.16] - 2026-08-26

### Fixed

- Allow the main Excel import workflow to accept completed Profiling-only workbooks such as `EWARS1.xlsx`.
- Validate all A1–L1 Profiling identifiers without requiring unrelated Inventory or Gap Analysis sheets.
- Create the corresponding Inventory system entry before importing the Profiling responses.

## [1.0.15] - 2026-08-26

### Fixed

- Populate K1–K6 Opportunities & Challenges fields from the question comment when the response cell is blank.
- Preserve the original comment metadata while ensuring comment-only Profiling findings are visible in the form and report.

## [1.0.14] - 2026-08-26

### Fixed

- Prefer the most complete matching Profiling record when an older blank record and a populated imported record refer to the same system.
- Prevent blank legacy records from hiding imported Opportunities & Challenges responses K1–K6.

## [1.0.13] - 2026-08-26

### Changed

- Align the Profiling form wording, response controls, and option lists with the 69-question `EWARS1.xlsx` reference.
- Use single-select controls for D7, F1, H1, H2, and I2 as specified by the workbook.
- Match the workbook's disease, primary-user, coverage, and supported-emergency options.
- Retain a dedicated G7 comments field so linked-system details such as DHIS2 are not lost.

## [1.0.12] - 2026-08-26

### Fixed

- Interpret `Country-wide` Profiling coverage as national geographic coverage.
- Interpret a system name entered in G7, such as DHIS2, as `Data exchange: Yes` and retain the name as the exchange detail.
- Preserve `County Teams` as a valid primary-user option during Profiling import.

## [1.0.11] - 2026-08-26

### Fixed

- Always include the Profiling operational challenges (K2) in each system's short summary.
- Present known limitations (K5) separately when they add information beyond the reported challenges.

## [1.0.10] - 2026-08-26

### Changed

- Replace the exhaustive Profiling question-and-answer transcript with a short, evidence-based summary.
- Summarise each system's context, principal capabilities, important gaps, respondent comments, and priority action.
- Add a compact portfolio overview for national coverage, API access, and data exchange.

## [1.0.9] - 2026-08-25

### Fixed

- Display imported Profiling multi-select values as selected field options, including valid values not present in the original predefined list.
- Preserve question-level imported comments when a Profiling record is opened, edited and saved.

## [1.0.8] - 2026-08-25

### Added

- Add a comprehensive Profiling response summary for every assessed system.
- Include question-level Profiling comments and clarifications alongside their responses.

### Fixed

- Exclude internal identifiers and imported-comment metadata from Profiling completeness calculations.

## [1.0.7] - 2026-08-25

### Added

- Add a clearly labelled `Test Country` option for non-production assessment testing.

## [1.0.6] - 2026-08-25

### Fixed

- Remove positional fallback when loading Profiling records, preventing one system's data from appearing under another system.
- Match legacy Profiling records by system identifier, normalized name, or recognized acronym before displaying or saving them.

## [1.0.5] - 2026-08-25

### Fixed

- Add `Kobo system` as a selectable underlying platform and normalize common Kobo naming variants.
- Map `Ebola Bundibugyo Virus Disease` and Bundibugyo variants to the `Ebola virus disease` selection.
- Preserve slashes inside valid multi-select values such as `AFP/Polio` and `HL7/FHIR Messaging`.

## [1.0.4] - 2026-08-25

### Fixed

- Accept combined Inventory and Profiling workbooks whose `HIS Inventory` headers begin on row 1.
- Allow a combined workbook without Gap Analysis sheets while still validating its Inventory and Profiling data.
- Match Inventory names to Profiling tab aliases such as `HMIS/DHIS2` to `HMIS` and `OCV/ONA` to `OCVONA`.
- Preserve slash-containing Inventory labels such as `IDSR/weekly syndromic surveillance` as one value.

## [1.0.3] - 2026-08-25

### Fixed

- Link Profiling-only workbook tabs to Inventory systems and create missing Inventory system records when required.
- Normalize imported categorical answers such as `NA` and capitalization variants so web controls display them correctly.
- Parse Profiling multi-select values according to the application field definition and preserve workbook comments.
- Correct the laboratory-result receipt options used by the Profiling form.

## [1.0.2] - 2026-08-25

### Fixed

- Recognise `National`, `National geographic`, and other National-qualified geographic coverage values consistently throughout the report.
- Prevent the report from counting systems at national scale and later claiming that no systems have national coverage.

## [1.0.1] - 2026-08-25

### Changed

- Corrected the Unified DHIS2 assistant analysis contract to recognize case investigation, contact follow-up and case classification.
- Treat existing DHIS2 tools as platforms to retain and enhance through Unified DHIS2.
- Replaced the matrix heading `Proposed tool disposition` with `Recommendation` and removed `Country validation gap`.
- Replaced `Evidence insufficient` recommendations with `Integrate with Unified DHIS2` for tools with limited evidence.
- Consolidated duplicate Profiling records before report analysis and scoring.
- Removed repeated and semantically equivalent report findings.
- Excluded placeholders such as `NA` from recommendations and action plans.
- Kept implementation lessons out of gaps and reserved data-quality flags for unclear or contradictory responses.

## [1.0.0] - 2026-08-25

### Baseline

- Established the current application as the first controlled release.
- Added a central application version constant.
- Added application and profile-format versions to the health response.
- Displayed the application version in the web interface footer.
- Retained profile-data format version 3 as a separate compatibility identifier.
