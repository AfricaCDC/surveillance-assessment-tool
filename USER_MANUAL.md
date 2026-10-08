# Africa CDC Surveillance Systems Assessment

## User Manual

Applies to application version **1.0.42**.

This web application supports three assessment components:

1. Inventory of surveillance tools and systems.
2. Profiling of each inventoried system.
3. Gap Analysis across nine assessment domains.

REDCap is the primary assessment database. The browser temporarily holds the active assessment and unsaved field values. Loading an assessment does not save it back to REDCap or create a duplicate record.

## 1. Roles

### Administrator

Administrators can manage application users and all coordinator functions. Only administrators see the Admin Guide and application-user management.

### Coordinator

Coordinators can:

- Create a blank assessment.
- Load an existing country and reporting period from REDCap.
- Enter and review all assessment components.
- Create groups and assign Inventory tools, Profiling systems, and Gap Analysis domains.
- Reset group passwords.
- Generate reports and use the report assistant.

Coordinator passwords remain valid until an administrator resets them.

### Group user

A group user can access only the assigned phase and assigned tools or domains. Group users cannot access administration, REDCap configuration, or other groups' work. They can review their saved work through **My Entries**.

## 2. Start and sign in

1. Open `AfricaCDCWebAssessment.exe`.
2. Wait for the browser to open `http://127.0.0.1:8080/login`.
3. Enter the application username and password.
4. Select **Sign in**.

If the browser reports that `127.0.0.1` refused the connection, close the browser tab, reopen the executable, and wait a few seconds. Do not start multiple copies.

## 3. Open or create an assessment

The application opens the main forms without populating a country assessment.

### Load REDCap data

1. Open **Inventory** under **Data Collection**.
2. In **Assessment data**, select a country and month/year.
3. Select **Load REDCap data**.
4. Wait for the tool, profile, and Gap Analysis counts.

The loaded country and reporting period automatically become the default filters on **Analysis**. You can change them manually when generating another report.

### Add new data

1. Select the country and reporting period in **Assessment data**.
2. Select **Add new data**.
3. Complete the blank Inventory, Profiling, and Gap Analysis forms.
4. Save the active section regularly.

New Member State data is sent to REDCap when saved. Data merely loaded from REDCap is not automatically written back and does not create a duplicate.

### Temporary Test Country workspace

An assessment whose country is exactly **Test Country** is for non-production testing only. Its entries and imports remain in application memory, are never sent to REDCap, and are discarded when the application closes or restarts. After a Test Country save, confirm that the status reads **Test Country: temporary only - not saved to REDCap**. Do not use **Test Country** for information that must be retained.

## 4. Inventory

1. Open **Data Collection > Inventory**.
2. Confirm the country and reporting period.
3. Select **Add another tool** when another surveillance system is required.
4. Complete the system fields.
5. Select **Save Inventory**.
6. Use **Previous tool** and **Next tool** to move between systems.

Coordinators can expand group assignments, add groups, assign tools, and reset group logins.

## 5. Profiling

1. Open **Data Collection > Profiling**.
2. Select a system.
3. Complete each profiling section, including open-ended strengths, challenges, limitations, lessons, enhancements, and priority actions.
4. Record the separate comment associated with each question where clarification is needed.
5. Select **Save Profiling**.

Profiling systems originate from named Inventory tools. The importer matches **System being assessed** to the Inventory name, allowing minor spelling and punctuation differences while preventing stale or unmatched profiling sheets from creating tools. Unanswered dropdowns display **No response** and remain empty; they must not default to the first option. Coordinators assign Profiling work separately from Inventory work.

## 6. Gap Analysis

1. Open **Data Collection > Gap Analysis**.
2. Select the working group or coordinator view.
3. Select an assigned domain.
4. Answer each question and add explanations, findings, comments, and recommendations where requested.
5. Save the domain responses.

Coordinators can assign, reassign, or release domains. Existing responses remain attached to their domain.

## 7. Groups and accounts

- Inventory, Profiling, and Gap Analysis accounts are phase-specific.
- A user must use the account for the assigned phase.
- A reset password replaces the old password immediately.
- Previously saved assessment data is not deleted by a password reset.
- Application coordinators are created and reset only by an administrator under **Users**.

## 8. Analysis and reports

1. Open **Analysis**.
2. Select **Inventory**, **Profiling**, or **Gap Analysis**.
3. Confirm or change the country and reporting period.
4. Select **Generate Report**.

The application uses the currently loaded or newly entered assessment when the filters match it. Otherwise it retrieves the selected assessment from REDCap without replacing the active data-entry workspace.

The Profiling summary is a brief five-part report: **Overview**, **Key capabilities**, **Main gaps and challenges**, **Reported priority actions**, and **Data validation**. Counts use recorded responses only. National coverage includes explicit national-level answers such as National, National scale, and Country-wide; blank, No response, state-level, and subnational answers are excluded.

In **Domain capability scores**, the affirmative and scored totals are answer counts across several yes/no questions; they are not numbers of systems. The report separately states how many profiled systems report data exchange and shows the Inventory total alongside the smaller Profiling denominator.

Available actions include:

- Summary Report and Visual Dashboard.
- Download Word.
- Print or Save PDF.
- Local report assistant.
- Download assistant responses in Microsoft Word format.
- Generate and download report charts as a PNG image.

## 9. Local report assistant

The report assistant uses `qwen3:4b-instruct` through Ollama when available. The header displays **Local AI - qwen3:4b-instruct**.

It receives only:

- The currently generated report.
- Supporting evidence from that selected assessment when required.
- Your question.
- A short recent chat history.

It does not receive REDCap tokens, passwords, unrelated assessments, or the complete application database. Requests use `http://127.0.0.1:11434`, which stays on the same computer.

Administrators may enable an approved online provider. The assistant header then displays **Online AI**. Online mode sends only the generated report and current question; it excludes underlying REDCap records, supporting-evidence JSON, credentials, and chat history. The app does not store online report or response content in SQLite. Provider-side retention is governed by the organisation's approved provider account and terms.

Assistant tools include:

- Professional report.
- Discuss all tables.
- Unified DHIS2 toolkit integration.
- Thematic analysis.
- Action plan.
- Executive summary.
- Recommendations and data-quality review.
- Offline chart generation from the report data loaded in the app.

For **Unified DHIS2 toolkit** analysis, the standard report output ends after the evidence-limitations content. It does not include a separate **Validation gates and indicators** section or the automated **Evidence check warning** that lists unsupported numerical expressions. Users may request specific validation indicators separately when they are needed, and all important figures should still be checked against the source assessment.

### Download an assistant response in Word

1. Generate the report and ask the assistant a question.
2. Wait until the complete response appears.
3. Select **Download latest response in Word** below the conversation.
4. Open the downloaded `.docx` in Microsoft Word or another compatible application.

The export contains the latest completed assistant response, together with the selected country and reporting period. It does not modify REDCap. Before sharing a Unified DHIS2 toolkit export, confirm that it does not contain the removed **Validation gates and indicators** section or the numerical-expression **Evidence check warning**.

### Generate and download charts

After generating a report, type a request such as:

> Generate charts from this report.

The app opens the chart view and generates the available portfolio charts from the assessment data already loaded in the app. These currently cover system types, surveillance-function coverage, responsible units, and API availability. Select **Download charts as PNG** to save the combined high-resolution image.

Chart generation is deterministic and local; Ollama does not invent the chart values. Multi-select categories may have totals greater than the number of inventoried systems.

### Offline operation

Ollama analysis, chart generation, Word export, and PNG download work without internet when the selected assessment report is already loaded and `qwen3:4b-instruct` is installed. Ollama does not connect directly to REDCap. Internet is still required to retrieve an assessment from REDCap after startup or to save changes back to REDCap.

The portable assessment executable does not include Ollama or the model. On each new computer, an administrator must install Ollama and run `ollama pull qwen3:4b-instruct` while internet access is available. Copying only the portable application does not transfer the local AI runtime or model.

Simple answers normally begin sooner. Complex analysis may take one or more minutes on a CPU-only computer, but text streams into the chat as it is generated. Verify important conclusions against the displayed report.

For a request to consolidate and prioritise recommendations, the assistant uses a compact evidence set and must link every recommendation to an explicit supporting finding. It must not transfer one system's finding to another or introduce an unsupported capability. If evidence is incomplete or contradictory, the response should state the validation need.

### Assistant troubleshooting

Confirm the model is installed:

```powershell
ollama list
```

The list must contain `qwen3:4b-instruct`. The application attempts to start the Ollama service automatically. Close unused applications when Windows memory is low.

If a request exceeds the context size, restart the updated executable and regenerate the report before asking again. Ask focused questions when a report is very large.

If a response is incomplete, confirm that the latest executable is running, regenerate the report, and repeat the request. Do not open multiple copies of the executable because background instances can prevent an update from being installed.

If the connection drops during an assistant request, the browser waits up to 90 seconds for the local server, reconnects, and retries the analysis once. Keep the browser page open. If the executable remains stopped, restart it and refresh the page; a browser is not permitted to launch a stopped Windows program automatically.

## 10. Import and export

Use the approved standard Excel format for Inventory, Profiling, and grouped Gap Analysis worksheets. The Profiling worksheet must retain the original section headings, question IDs, question text, Response column, and separate Comments column for every question. Confirm the country and reporting period before import. Review validation counts after import.

After a successful import, the application refreshes the active workspace immediately; a manual browser refresh should not be required. Verify system name, underlying platform, implementation year, diseases/events, coverage, and all Opportunities & Challenges responses. Blank cells must remain **No response**, and custom multi-select values must remain attached to the correct question.

Exports include phase-specific standard workbooks and report downloads. Exporting or generating a report does not change REDCap data.

## 11. Saving and logout

- Save before changing tools, systems, or domains.
- Wait for the successful save message.
- Use **Log out** when finished.
- Loaded REDCap data is not saved again merely because you log out.
- Saved Member State entries remain in REDCap. Test Country entries are discarded when the application closes or restarts.

## 12. Data protection

- Never share the `.env` file or REDCap API token.
- Keep the application-adjacent `.env` file unchanged when updating or restarting the desktop application. It is the authoritative source for the password-security key, ensuring the same password works across terminal, shortcut, and packaged launches.
- Never include passwords or tokens in screenshots.
- Do not delete or rename REDCap records without authorization.
- Before deleting a training record, verify its record ID, country, reporting period, and assessment title. An old local assessment can recreate a deleted REDCap record if it is synchronized again.
- Use **Test Country** for temporary training that must never be written to production REDCap. Use a separately approved, clearly named UAT country only when REDCap persistence itself must be tested.
- Use only approved computers and networks.
- Treat AI-generated recommendations as proposed analysis requiring human review.

## 13. Getting help

Provide the country, reporting period, phase, exact action, exact error message, and a screenshot with credentials hidden. Contact the application administrator for accounts and assignments, IT for application availability, and the REDCap administrator for API permissions.

## Hosted application address

Use the public application URL provided by your administrator. If the application
is hosted under a subpath, keep that prefix in the address, for example
`https://example.org/tools/assessment/`. Login, navigation, language switching,
manual links, downloads, and logout use the same application location.
The login page displays the 12-hour sign-out notice.
