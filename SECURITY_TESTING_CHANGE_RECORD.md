# Post-security-testing change record

Application: Africa CDC Surveillance Digital Tools Assessment Web Application  
Change version: **1.0.42**  
Previous server version: **1.0.41**  
Implementation date: **8 October 2026** (Africa/Addis_Ababa)  
Status: **Implemented in local source; production effective date pending deployment**  
Profile-data format: **3**, unchanged

## Changes effected following team feedback

| Reference | Requested correction | Change implemented | Effective version |
|---|---|---|---|
| SEC-01 | Avoid root-absolute application URLs so the app can run under a subpath. | Browser asset references, API requests, translation files, manual links, downloads, health polling, and sign-in/sign-out navigation now use relative URLs. | 1.0.42 |
| SEC-02 | Support deployment configuration without editing individual frontend files. | Added `AFRICA_CDC_BASE_PATH`. Server routing, redirects, cookie scope, and browser launch address respect the configured mount path. Empty configuration retains domain-root deployment. | 1.0.42 |
| SEC-03 | Remove "Passwords are securely hashed and do not expire." | Removed the sentence from the login page. The 12-hour sign-out notice remains. Password hashing, expiration policy, and session duration were not changed by this wording correction. | 1.0.42 |
| SEC-04 | Keep deployment materials aligned with the fixes. | Updated Docker health-check URL construction, Docker environment example, README, user manual, and deployment guides. In-app guide links use relative URLs. The setup launcher continues to invoke the updated server and needs no code change. | 1.0.42 |

These reference numbers identify this change record only; they are not identifiers supplied by the security-testing team. The changes address the feedback provided in this conversation and do not establish that all security findings have been resolved.

## Validation completed

- JavaScript syntax checks passed for `static/app.js`, `static/login.js`, and `static/i18n.js`.
- Python compilation passed for `server.py`.
- Local HTTP checks passed at the domain root and `/tools/assessment`: login pages, styles, scripts, logo, translations, health endpoint, protected-page redirects, and unauthenticated API/download rejection. The checks used an unauthenticated test handler; they did not exercise a full user sign-in or authenticated report download.
- Relative API URL resolution was checked from login, application, index, and mount-root addresses.
- Docker health-check command syntax and URL construction passed for root and subpath configurations using a stub HTTP response. A Docker image was not built or run for this check.
- Source whitespace checks passed.

## Deployment and effective-date record

For a public address such as `https://example.org/tools/assessment/`, set
`AFRICA_CDC_BASE_PATH=/tools/assessment`, restart the server, and configure the
reverse proxy to preserve the prefix. Docker deployments require an image rebuild
and container recreation. Verify the public health endpoint reports
`app_version: 1.0.42`, then check sign-in, assets, language switching, guide links,
authenticated downloads, and logout.

Production deployment date: **Pending**  
Production verification/approval: **Pending**

## Text for inclusion in the security-testing report

Following security-testing feedback, application version 1.0.42 was updated on
8 October 2026 to replace root-absolute browser URLs with relative paths and add
configurable subpath support through AFRICA_CDC_BASE_PATH. Server routing,
redirects, session-cookie paths, and Docker health checks were aligned with the
configured deployment path. The login-page statement ?Passwords are securely
hashed and do not expire? was removed, and deployment and user documentation
were updated. Local syntax and targeted HTTP checks passed. The changes are
implemented in the local source; their production effective date remains pending
image rebuild, deployment, and public-environment verification.
