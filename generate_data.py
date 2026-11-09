"""
Synthetic ABA operations dataset for a Salesforce utilization project.

ALL DATA IS FICTIONAL. No real clients, staff, or PHI.
Payer names are used for realism only; rates are made up.

Output (load in this order):
  data/1_payers.csv
  data/2_clinicians.csv
  data/3_clients.csv
  data/4_authorizations.csv
  data/5_session_weeks.csv

Built-in patterns to "discover" in the dashboards:
  1. Tempe has a staffing problem: staff cancellations climb Aug-Oct.
  2. Summer dip: client cancellations rise in June-July.
  3. One commercial payer (Cigna) renews authorizations late, so clients
     go weeks with no billable services between auths.
  4. Several active auths are on pace to expire with lots of unused hours.

Run:  pip install faker  &&  python generate_data.py
"""

import csv
import os
import random
from datetime import date, timedelta

from faker import Faker

SEED = 42
random.seed(SEED)
fake = Faker("en_US")
Faker.seed(SEED)

TODAY = date(2026, 11, 5)
WINDOW_START = date(2026, 5, 4)   # first Monday of data window
WINDOW_END = date(2026, 11, 1)    # last full week ends Sunday Nov 1
AUTH_WEEKS = 26                   # 6-month authorizations
N_CLIENTS = 60
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)


def q(x):
    """Round to 0.25 hr (one 15-minute billing unit)."""
    return round(round(x * 4) / 4, 2)


def write(name, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# ---------------- Payers ----------------
payers = [
    ("PAY-01", "Mercy Care (AHCCCS)", "Medicaid", 52.00, 0),
    ("PAY-02", "Banner University Family Care (AHCCCS)", "Medicaid", 52.00, 0),
    ("PAY-03", "AZ DDD", "State Program", 56.00, 0),
    ("PAY-04", "BCBS of Arizona", "Commercial", 68.00, 0),
    ("PAY-05", "UnitedHealthcare", "Commercial", 64.00, 1),
    ("PAY-06", "Aetna", "Commercial", 62.00, 1),
    ("PAY-07", "Cigna", "Commercial", 60.00, 4),  # slow renewals
]
payer_rows = [
    {"Ext_ID__c": p[0], "Name": p[1], "Payer_Type__c": p[2],
     "Rate_per_Hour__c": f"{p[3]:.2f}"}
    for p in payers
]
payer_delay = {p[0]: p[4] for p in payers}  # max renewal gap in weeks
payer_weights = [22, 14, 18, 14, 12, 10, 10]

# ---------------- Clinicians (BCBAs) ----------------
locations = ["Phoenix", "Tempe", "Scottsdale"]
clinician_rows = []
for i in range(9):
    clinician_rows.append({
        "Ext_ID__c": f"BCBA-{i+1:02d}",
        "Name": fake.name(),
        "Role__c": "BCBA",
        "Location__c": locations[i % 3],
        "Hire_Date__c": fake.date_between(date(2018, 1, 1), date(2025, 6, 1)).isoformat(),
    })
bcbas_by_loc = {l: [c for c in clinician_rows if c["Location__c"] == l] for l in locations}

# ---------------- Clients, Authorizations, Session Weeks ----------------
client_rows, auth_rows, week_rows = [], [], []
auth_n = 0
week_n = 0


def staff_cancel_rate(loc, wk):
    base = 0.03
    if loc == "Tempe" and wk >= date(2026, 8, 1):
        months_in = (wk - date(2026, 8, 1)).days / 30
        base = 0.08 + 0.05 * months_in  # worsening each month
    return base


def client_cancel_mult(wk):
    return 1.8 if wk.month in (6, 7) else 1.0


for i in range(N_CLIENTS):
    cid = f"CL-{i+1:03d}"
    loc = random.choices(locations, weights=[50, 25, 25])[0]
    bcba = random.choice(bcbas_by_loc[loc])
    payer_id = random.choices([p[0] for p in payers], weights=payer_weights)[0]
    weekly_hrs = random.choice([10, 15, 15, 20, 20, 25, 30])
    svc_start = fake.date_between(date(2025, 6, 1), date(2026, 9, 15))
    svc_start -= timedelta(days=svc_start.weekday())  # align to Monday
    client_cancel_base = random.uniform(0.04, 0.18)

    discharged = random.random() < 0.10
    discharge = None
    if discharged:
        d = fake.date_between(max(svc_start + timedelta(weeks=8), WINDOW_START), date(2026, 10, 15))
        discharge = d

    first = fake.first_name()
    last = fake.last_name()
    client_rows.append({
        "Ext_ID__c": cid,
        "Name": f"{first} {last}",
        "First_Name__c": first,
        "Last_Name__c": last,
        "Date_of_Birth__c": fake.date_between(date(2014, 1, 1), date(2023, 12, 31)).isoformat(),
        "Location__c": loc,
        "Primary_BCBA__c": bcba["Ext_ID__c"],
        "Primary_Payer__c": payer_id,
        "Weekly_Prescribed_Hours__c": weekly_hrs,
        "Service_Start_Date__c": svc_start.isoformat(),
        "Status__c": "Discharged" if discharged else "Active",
        "Discharge_Date__c": discharge.isoformat() if discharge else "",
    })

    # Build back-to-back auths (with payer renewal gaps) from service start
    a_start = svc_start
    while a_start <= WINDOW_END:
        a_end = a_start + timedelta(weeks=AUTH_WEEKS) - timedelta(days=1)
        gap = random.randint(0, payer_delay[payer_id]) if payer_delay[payer_id] else 0
        next_start = a_end + timedelta(days=1) + timedelta(weeks=gap)
        if discharge and a_start > discharge:
            break
        if a_end < WINDOW_START:
            a_start = next_start
            continue

        auth_n += 1
        aid = f"AUTH-{auth_n:04d}"
        approved = weekly_hrs * AUTH_WEEKS

        # Simulate every week of the auth; weeks before the window are
        # summarized into Hours_Used_Prior__c ("migrated from legacy system").
        prior_used = 0.0
        wk = a_start
        while wk <= min(a_end, WINDOW_END):
            if discharge and wk > discharge:
                break
            sched = weekly_hrs
            c_rate = min(client_cancel_base * client_cancel_mult(wk) * random.uniform(0.5, 1.5), 0.6)
            s_rate = min(staff_cancel_rate(loc, wk) * random.uniform(0.5, 1.5), 0.6)
            c_can = q(sched * c_rate)
            s_can = q(sched * s_rate)
            delivered = q(max(sched - c_can - s_can, 0))
            if wk < WINDOW_START:
                prior_used += delivered
            else:
                week_n += 1
                week_rows.append({
                    "Ext_ID__c": f"WK-{week_n:05d}",
                    "Authorization__c": aid,
                    "Week_Start__c": wk.isoformat(),
                    "Hours_Scheduled__c": sched,
                    "Hours_Delivered__c": delivered,
                    "Hours_Cancelled_Client__c": c_can,
                    "Hours_Cancelled_Staff__c": s_can,
                })
            wk += timedelta(weeks=1)

        auth_rows.append({
            "Ext_ID__c": aid,
            "Name": aid,
            "Client__c": cid,
            "Payer__c": payer_id,
            "CPT_Code__c": "97153",
            "Approved_Hours__c": approved,
            "Hours_Used_Prior__c": q(prior_used),
            "Start_Date__c": a_start.isoformat(),
            "End_Date__c": a_end.isoformat(),
        })
        a_start = next_start

write("1_payers.csv", payer_rows)
write("2_clinicians.csv", clinician_rows)
write("3_clients.csv", client_rows)
write("4_authorizations.csv", auth_rows)
write("5_session_weeks.csv", week_rows)
total = len(payer_rows) + len(clinician_rows) + len(client_rows) + len(auth_rows) + len(week_rows)
print(f"TOTAL records: {total}  (~{total*2/1024:.1f} MB of the 5 MB Developer Edition limit)")
