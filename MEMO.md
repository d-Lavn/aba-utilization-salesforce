# Memo: Authorization Utilization Review

**To:** Director of Clinical Operations
**From:** Dylan Lavner, Operations Analyst
**Date:** November 9, 2026
**Re:** Tempe staffing is driving lost therapy hours; ~$119K of authorized revenue at risk in the next 60 days

*Analysis uses synthetic data in a Salesforce portfolio build. Figures as of Nov 6, 2026.*

---

## Bottom line
Tempe lost staff capacity in August, and its staff-cancelled hours rose from **3% to 21%** in three months. Across all sites, **23 authorizations expire within 60 days** with **~$119K** of approved hours that can no longer be delivered, even with perfect attendance. Most of it can still be reduced if we act this month.

## Key findings
1. **Tempe staffing problem.** Staff-cancelled hours at Tempe went from ~3% (May–Jul) to 11% (Aug), 15% (Sep) and **21% (Oct)**. Delivery fell to 68%. Phoenix and Scottsdale held steady at ~3%.
2. **It's the site, not a clinician.** All three Tempe BCBAs deliver 72–76% of scheduled hours, compared with 84–91% at the other sites. That points to RBT coverage, not individual performance.
3. **Projected lost revenue: ~$119K** across 23 authorizations expiring in ≤60 days. The largest is AUTH-0061 (Tempe, Aetna) at ~$10.6K.
4. **Authorization renewal gaps.** Some Cigna and UnitedHealthcare clients went 1–3 weeks without an active authorization between renewals.
5. **Data quality.** 6 discharged clients still had active authorizations, inflating caseload and revenue figures. *(Fixed; see below.)*

## Recommendations
| # | Action | Owner | When |
|---|---|---|---|
| 1 | Review Tempe RBT headcount and open shifts. Temporarily float Phoenix RBTs to cover Tempe caseloads | Clinical Ops + HR | This week |
| 2 | Work the **Top 10 Authorizations** list weekly: add make-up sessions or request extensions | Scheduling | Starting now |
| 3 | Start renewals **45 days** before End Date for Cigna and UnitedHealthcare, versus 30 for others | Intake / Auth team | Next renewal cycle |
| 4 | Plan for the June–July client-cancellation dip in summer scheduling and revenue forecasts | Clinical Ops + Finance | Q2 planning |

## Already in place
- **Discharge automation:** a Salesforce Flow now closes a client's open authorizations when they are discharged. The 6 bad records were backfilled, and the data-quality count is now 0.
- **Expiration alert:** a daily Flow creates a high-priority task when an authorization hits 30 days left with under 70% used.
- **PHI protection:** client name and date of birth are restricted through field-level security and a permission set, and changes to authorization dates and hours are audit-tracked.

*Dashboard: "ABA Operations Command Center" in Salesforce.*
