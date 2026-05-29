# Data Model

## Overview

```
Tenant
  |
  +-- IngestionBatch (source, uploaded_by, timestamps, row counts)
        |
        +-- RawRecord (raw_payload JSONB, parse_error, row_number)
              |
              +-- NormalizedEmission (scope, co2e_kg, status, original + normalized values)
                    |
                    +-- AuditLog (action, who, when, what changed)
```

User is Django's built-in auth user. Each Tenant maps to one enterprise client.

## Tenant

Holds the client identity. Every other table has a foreign key to Tenant. This is how multi-tenancy is enforced — every query filters by tenant, so one client can never see another's data.

We use a simple FK approach rather than row-level security or a separate schema per tenant. For this scale it is sufficient, and it keeps the Django ORM straightforward.

## IngestionBatch

One record per file upload. Tracks the source system (sap / utility / travel), who uploaded it, when, and how many rows parsed vs failed. This lets the analyst see the history of uploads at a glance without querying individual rows.

## RawRecord

Stores the original CSV row as JSONB. This is important for two reasons:
1. If the normalization logic changes later, you can reprocess without re-uploading.
2. If an analyst questions a number, you can show them the exact raw value that came from the source system.

We store `parse_error` as text here for rows that could not be parsed, so failed rows are still recorded (not silently dropped).

## NormalizedEmission

The main working table. Every successfully parsed row becomes one NormalizedEmission. Key fields:

- `scope`: 1, 2, or 3 (direct, electricity, travel)
- `original_value` + `original_unit`: what the source file had (e.g. 500 GAL)
- `normalized_value` + `normalized_unit`: after conversion (e.g. 1892.7 L)
- `co2e_kg`: final emissions in kg CO2 equivalent
- `status`: pending / approved / rejected / flagged
- `flag_reason`: text explanation set by the parser or analyst
- `manually_edited` + `edited_by`: tracks if someone changed the row after ingestion

Once status = approved, the row is locked (enforced in the API views, not at the DB level).

## AuditLog

A separate table that records every status change. Stores the previous status, new status, who made the change, when, a note, and an optional diff JSONB for edits.

We do not use only `updated_at` on NormalizedEmission because that loses history. If an analyst approves, then another rejects, you need the full sequence, not just the final state.

## Unit normalization

SAP: fuel quantities in L, GAL, or KG are all converted to liters. Density conversions are fuel-specific (e.g. HFO, LPG, diesel have different kg/L ratios). After conversion, an emission factor (kgCO2e per liter) is applied.

Utility: kWh stays kWh. A grid emission factor (kgCO2e per kWh) is applied.

Travel: distances stay in km. Emission factors per km differ by mode (flight, car, rail). Hotels are calculated per night.

All original values and units are preserved alongside the normalized ones so nothing is lost.
