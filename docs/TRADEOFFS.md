# Tradeoffs

Three things that were not built, and what the real consequence is.

---

## 1. No per-row edit UI

The review dashboard lets analysts approve, reject, and flag rows but not edit individual field values. The data model supports it (manually_edited, edited_by, diff in AuditLog) but the UI does not.

Consequence: If an analyst spots a clearly wrong value (e.g. a fuel quantity entered as 5000 instead of 500), they have to reject the row and ask whoever uploaded the file to re-export and re-upload. That is an extra round trip that could be avoided. In a production system, you would add an inline edit for specific fields (co2e_kg, activity_date, description) with a required reason field, and log the diff.

---

## 2. No real multi-tenant isolation at the API level

The frontend sends `tenant_id=1` as a hardcoded query parameter. The backend filters by that tenant ID, but it trusts the client to send the right one. There is no check that the logged-in user belongs to the tenant they are querying.

Consequence: Any authenticated user can query any tenant's data by changing the tenant_id parameter. In a real deployment you would have a UserProfile or TenantMembership model that maps users to tenants, and the API would look up the user's tenant rather than reading it from the request. This is the most significant security gap in the current implementation.

---

## 3. No role-based access control

Two users are seeded (admin and analyst) but both have identical API permissions. An analyst can approve and reject rows the same as an admin.

Consequence: In production, analysts would typically flag and comment but not approve — approvals would be gated to a senior reviewer or finance lead to satisfy the four-eyes principle required by most carbon reporting standards (GHG Protocol, ISO 14064). The fix is a UserProfile model with a role field and per-view permission decorators. Skipped here because it does not affect the data pipeline being evaluated.

---

## 4. No emission factor versioning

The emission factors (kgCO2e per liter, per kWh, per km) are hardcoded in the parser files. DEFRA, the GHG Protocol, and national grid operators update their factors annually. If a client re-submits data from a prior year, the wrong factor will be used.

Consequence: Historical data will be calculated with current-year factors, which can cause material errors when auditors compare year-over-year numbers. The fix is a database table of emission factors keyed by fuel type / source type / year, looked up at ingestion time. This is standard practice in carbon accounting platforms.
