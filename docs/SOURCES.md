# Sources

---

## SAP Flat File Export

What I looked at: SAP ALV report output documentation, SAP SE standard SLIS reporting format, and public SAP community posts about flat file interfaces for CO2 reporting.

What I learned: SAP uses semicolons as column delimiters in German locale environments because commas are used as decimal separators. Column headers appear in German (Buchungskreis = company code, Werk = plant, Materialnummer = material number, Menge = quantity, Einheit = unit, Buchungsdatum = posting date). Dates are YYYYMMDD with no separators. Plant codes like PLANT_1000 match the typical four-digit plant code pattern in SAP.

Why the sample data looks the way it does: Company codes (1000, 2000) and plant codes (PLANT_1000 through PLANT_4000) match SAP's default numbering. Material codes use a realistic MAT-XXX-NNN pattern. Units mix L, KG, and GAL to reflect real-world cases where some vendors invoice by weight and others by volume.

What would break in production: SAP configurations vary significantly. Column order is not guaranteed -- exports from different ALV reports or different SAP versions may put columns in a different order. The safest approach is to match columns by header name, which this parser does. A real deployment would need a mapping configuration per client.

---

## Utility Portal Export

What I looked at: E.ON, Vattenfall, and EnBW portal documentation (Germany-based), and UK smart meter data export formats from Ofgem guidance.

What I learned: Most utility portals export by billing period, not calendar month. Billing periods are aligned to meter read cycles (28-32 days typically). Some large industrial customers have monthly reads, others have quarterly reads. The demand_kw column (peak demand) appears in commercial invoices but not residential ones. Tariff codes vary by country and provider.

Why the sample data looks the way it does: Most rows have calendar-month billing periods but several span months (e.g. Jan 15 to Feb 14) to test the cross-month detection logic. Some rows have missing meter IDs to simulate portal data quality issues.

What would break in production: Real utility exports include taxes, VAT, and currency columns that vary by country. The emission factor used here (0.207 kgCO2e/kWh) is the UK grid average for 2023-24. German and other European grids have different factors. A production system would look up the factor by country and year, not hardcode it.

---

## Corporate Travel Export (Concur-style)

What I looked at: SAP Concur standard expense report export documentation, the Concur TripLink API schema, and DEFRA travel emission factor guidance 2023.

What I learned: Concur's default export is expense-focused (cost, category, merchant). Travel-specific fields like origin, destination, and distance require either the TripLink module or a custom travel policy configuration. Many clients get flight data as IATA codes only, without distance, which is why haversine is needed. Hotel nights are the standard unit for hotel emissions, not km.

Why the sample data looks the way it does: Trip IDs use a TRP-NNNNN format matching Concur's pattern. Employee IDs are anonymized (EMP-NNNN). Travel types cover all four modes: flight, hotel, car, rail. Some flight rows have distance missing (only IATA codes) to trigger the haversine path. Two rows have dirty data: one with an invalid employee ID format, one with missing origin/destination.

What would break in production: Real Concur exports vary significantly by company configuration. Column names, date formats, and which fields are populated depend on what the travel manager has set up. A real integration would start by requesting a sample export from the client and adjusting the column mapping accordingly. The IATA coordinate lookup table here covers only 17 airports -- a production version needs the full IATA database (~8,000 airports).
