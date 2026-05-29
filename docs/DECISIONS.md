# Decisions

---

Question: Why flat file (semicolon CSV) over IDoc for SAP?

Decision: Semicolon-delimited flat file export.

Why: SAP IDoc is a native EDI format designed for system-to-system transfer over ABAP/RFC connections. It requires middleware (SAP PI/PO or an API gateway), specialist knowledge to parse, and tight coupling to the SAP version. Most analytics and ESG reporting projects with SAP use flat file exports instead -- the "SLIS" ALV report output, which is exactly this format. The semicolon delimiter is the SAP default for German locale exports (comma conflicts with decimal notation).

What I would ask the PM: Does the client have an existing SAP PI/PO setup, or are they exporting manually? If they have EDI infrastructure already, switching to IDoc would be more reliable for production.

---

Question: Why CSV export for utility portal data?

Decision: CSV with ISO date columns and kWh as the value column.

Why: Utility portals (e.g. Vattenfall, E.ON, EnBW in Germany) all offer CSV export as the lowest common denominator. They do not expose APIs to third parties without a formal integration agreement. The column names in the sample data reflect the actual column layout from common German utility portal exports.

What I would ask the PM: Which utility provider are they using? Some have their own XML or PDF billing formats, and the CSV export is an optional feature that needs to be enabled on the account.

---

Question: Why model travel data on Concur's export format?

Decision: Use a CSV modeled on Concur SAP Travel expense export.

Why: Concur is the dominant corporate travel platform for enterprise clients. Their standard export has Trip ID, Expense Type, Amount, and vendor columns. I adapted this into a travel-specific format with origin/destination and distance, since Concur's raw export is expense-focused and needs to be enriched with travel metadata. Real implementations would use Concur's TripLink API or a custom integration.

What I would ask the PM: Is this a Concur client? If so, can we request a sample export file? Concur's column names and date formats vary by company configuration.

---

Question: How to handle non-calendar billing periods for utility data?

Decision: Accept the row and flag it with a warning if the period spans two calendar months.

Why: Pro-rating across months adds complexity without clear benefit -- the total kWh is still correct, and the analyst can see the billing period dates. A flag makes it visible for review. Splitting the row into two monthly records would require inventing an allocation rule (uniform distribution assumes constant usage, which is often not true).

What I would ask the PM: Does the auditor care about monthly granularity, or is billing-period granularity acceptable?

---

Question: What to do when flight distance is missing?

Decision: Compute via haversine using a static airport coordinate lookup.

Why: A surprising number of corporate travel exports omit distance and include only IATA codes. Haversine is simple, correct to within a few percent for straight-line air distance, and requires no external API call. The alternative (calling a flight distance API) adds latency, a network dependency, and a cost per row. Emission factors already have uncertainty at the 10-20% level, so haversine error is not the dominant source of inaccuracy.

What I would ask the PM: How important is precision on flight distances? If the client has access to actual flown distances (some corporates get this from their travel agency), we should use those instead.

---

Question: Session auth vs JWT?

Decision: Django session auth.

Why: The app is a single-domain web app with a React frontend and a Django backend. Sessions are simpler, work out of the box with Django's auth system, and do not require token refresh logic. JWT would add value if we needed stateless auth for mobile clients or third-party API consumers, but we do not. The CSRF cookie is handled by Django and included in Vite's dev proxy config.

What I would ask the PM: Is there a plan to expose this data via a public API to external tools? If yes, JWT makes more sense.

---

Question: Why do admin and analyst have the same permissions?

Decision: Both users share a single permission tier (IsAuthenticated). No RBAC.

Why: Two users were seeded to demonstrate that the system supports multiple actors. Role-based access control — read-only analyst vs. approver admin — was a deliberate tradeoff. The data model and auth system support it, but adding it in this version would require a UserProfile/group mapping, per-view permission checks, and UI gating, none of which changes the core ESG data pipeline being demonstrated. See TRADEOFFS.md for the full reasoning.

What I would ask the PM: Should analysts be able to approve, or only flag and comment? Should upload be restricted to admins only?

---

Question: Why not Celery for ingestion?

Decision: Synchronous ingestion in the request/response cycle.

Why: The parsers are fast (CSV parsing with no I/O). A 50,000-row SAP file takes under a second. Adding Celery would require Redis, a worker process, and polling logic on the frontend, all for no measurable benefit at this scale. The decision should be revisited if files grow beyond a few MB or if network storage is involved.

What I would ask the PM: What is the expected file size? If clients upload multi-MB files weekly, async ingestion becomes worthwhile.
