# ABA Utilization & Authorization Command Center (Salesforce)

Portfolio project: a Salesforce data model, dashboards and automation that track ABA authorization utilization, cancellations and revenue at risk.

**All data is synthetic.** It contains no real clients, staff or PHI. Payer names are included for realism, and every rate is made up.

---

## Day 1: Org setup, data model, data load

### 1. Create the org (10 min)
1. Sign up for a free Developer Edition at developer.salesforce.com/signup.
2. Skip NPSP for this project. A Developer org has **5 MB of data storage**, and NPSP creates a Household Account for every Contact. Using a custom Client object keeps the whole dataset at about 2.7 MB. (Interview line: "In production I'd model clients on NPSP Contacts/Households. I used a custom object here because of dev-org storage limits.")
3. Check storage anytime at Setup → Storage Usage.

### 2. Build the objects (≈2–3 hrs)
Setup → Object Manager → Create → Custom Object. Build them **in this order**, because later objects look up to earlier ones.

On every object, create **`Ext_ID__c`** as a Text(20) field with **External ID** and **Unique** checked. The import uses it to link records together.

**Payer__c** (Record Name: Text)
| Field | Type |
|---|---|
| Payer_Type__c | Picklist: Medicaid, State Program, Commercial |
| Rate_per_Hour__c | Currency(6,2) |

**Clinician__c** (Record Name: Text)
| Field | Type |
|---|---|
| Role__c | Picklist: BCBA, RBT |
| Location__c | Picklist: Phoenix, Tempe, Scottsdale |
| Hire_Date__c | Date |

**Client__c** (Record Name: Text)
| Field | Type |
|---|---|
| First_Name__c, Last_Name__c | Text(40) — PHI |
| Date_of_Birth__c | Date — PHI |
| Location__c | Picklist: Phoenix, Tempe, Scottsdale |
| Primary_BCBA__c | Lookup(Clinician__c) |
| Primary_Payer__c | Lookup(Payer__c) |
| Weekly_Prescribed_Hours__c | Number(3,0) |
| Service_Start_Date__c | Date |
| Status__c | Picklist: Active, Discharged |
| Discharge_Date__c | Date |

**Authorization__c** (Record Name: Text)
| Field | Type |
|---|---|
| Client__c | Lookup(Client__c) |
| Payer__c | Lookup(Payer__c) |
| CPT_Code__c | Picklist: 97151, 97153, 97155, 97156 |
| Approved_Hours__c | Number(6,2) |
| Hours_Used_Prior__c | Number(6,2). Hours delivered before May 2026, "migrated from the legacy system" |
| Start_Date__c, End_Date__c | Date |

**Session_Week__c** (Record Name: **Auto Number** `SW-{00000}`). One record is one client-week of 97153 services.
| Field | Type |
|---|---|
| Authorization__c | **Master-Detail(Authorization__c)** |
| Week_Start__c | Date |
| Hours_Scheduled__c | Number(5,2) |
| Hours_Delivered__c | Number(5,2) |
| Hours_Cancelled_Client__c | Number(5,2) |
| Hours_Cancelled_Staff__c | Number(5,2) |

Weekly roll-ups instead of individual sessions also keep you under the storage limit. Session-level detail comes back in Project 2 as the "EHR export."

### 3. Add the calculated fields on Authorization__c (≈30 min)
Create these **after** Session_Week__c exists.

| Field | Type | Formula |
|---|---|---|
| Hours_Used_Window__c | Roll-Up Summary | SUM(Session_Week__c.Hours_Delivered__c) |
| Hours_Used__c | Formula (Number) | `Hours_Used_Window__c + Hours_Used_Prior__c` |
| Hours_Remaining__c | Formula (Number) | `Approved_Hours__c - Hours_Used__c` |
| Utilization__c | Formula (Percent) | `Hours_Used__c / Approved_Hours__c` |
| Days_Remaining__c | Formula (Number) | `End_Date__c - TODAY()` |
| Auth_Status__c | Formula (Text) | `IF(End_Date__c < TODAY(), "Expired", "Active")` |
| Revenue_at_Risk__c | Formula (Currency) | `IF(End_Date__c >= TODAY(), Hours_Remaining__c * Payer__r.Rate_per_Hour__c, 0)` |

### 4. Load the data (≈1 hr)
Use **Setup → Data Import Wizard → Custom objects**, or dataloader.io (free tier) if the wizard gives you trouble. Load files **in order**:

1. `data/1_payers.csv` → Payer__c
2. `data/2_clinicians.csv` → Clinician__c
3. `data/3_clients.csv` → Client__c (match Primary_BCBA__c and Primary_Payer__c **by Ext_ID__c**)
4. `data/4_authorizations.csv` → Authorization__c (match Client__c and Payer__c by Ext_ID__c)
5. `data/5_session_weeks.csv` → Session_Week__c (match Authorization__c by Ext_ID__c)

Each lookup column in the CSVs holds the parent's **Ext_ID**. When the wizard asks how to match the related record, choose the Ext_ID__c field. Dates use YYYY-MM-DD format.

**Check the counts after loading:** 7 payers, 9 clinicians, 60 clients, 92 authorizations, 1,234 session weeks.

### 5. Create a custom report type (10 min, needed on Day 2)
Setup → Report Types → New: **Authorizations with Session Weeks** (primary object Authorization__c, related object Session_Week__c). Add the Client and Payer lookup fields via "Add fields related via lookup."

---

## What's in the data (keep this to yourself until the memo)
The dataset has these patterns built in for you to find on Day 2:
- **Tempe staffing problem:** staff-cancelled hours rise from about 3% to about 21% between August and October. Delivery rate falls to 68%.
- **Summer dip:** client cancellations jump in June and July at every location.
- **Commercial renewal gaps:** clients on Cigna and UnitedHealthcare wait 1–3 weeks between authorizations, which means weeks with no billable services.
- **Unused hours:** several active authorizations are on pace to expire well below 80% utilization.
- **Data quality issue:** some discharged clients still have "Active" authorizations. Flag this in your memo; Day 3's governance work can fix it.

## Regenerating the data
```
pip install faker
python generate_data.py
```
Seed is fixed (42), so the output is reproducible.
