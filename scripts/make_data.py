# Writes the CSVs the Power BI model loads: an invented South African workforce,
# 2016 to September 2026, with hiring, leaving and employment-equity fields.
#   data/employees.csv   one row per person ever employed (no names, IDs only)
#   data/department.csv  departments, with a made-up manager address for row-level security
#   data/job.csv         job titles with their EE occupational level
#   data/calendar.csv    one row per day, 2016 to 2026
#   data/expected.json   the figures the model's measures must reproduce
#
# Departments, job titles, provinces, education and salary ranges follow the HR data
# generator in data-analysis/hr-data-generator. Leaving, EE level, population group and
# disability are added here. Every proportion is invented; none is a real statistic.
# Three patterns are planted for the report to find; they are listed in PLANTED below.
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
SEED = 20261025
START = pd.Timestamp("2016-01-01")
AS_OF = pd.Timestamp("2026-09-30")
CALENDAR_TO = pd.Timestamp("2026-12-31")

PLANTED = {
    "call_centre_from": "2025-07-01",     # call centre agents resign 2.4 times as often from here on
    "call_centre_factor": 2.4,
    "it_women_factor": 1.7,               # women in IT resign 1.7 times as often as men
    "top_designated_share": 0.40,         # designated groups at top and senior management, against about 0.8 overall
}

PROVINCES = {
    "Gauteng": (0.35, ["Johannesburg", "Pretoria", "Soweto"]),
    "Western Cape": (0.15, ["Cape Town", "Stellenbosch", "Paarl"]),
    "KwaZulu-Natal": (0.12, ["Durban", "Pietermaritzburg", "Richards Bay"]),
    "Eastern Cape": (0.10, ["Gqeberha", "East London", "Mthatha"]),
    "Free State": (0.07, ["Bloemfontein", "Welkom", "Bethlehem"]),
    "Limpopo": (0.06, ["Polokwane", "Tzaneen", "Thohoyandou"]),
    "Mpumalanga": (0.06, ["Mbombela", "Emalahleni", "Secunda"]),
    "North West": (0.05, ["Rustenburg", "Mahikeng", "Klerksdorp"]),
    "Northern Cape": (0.04, ["Kimberley", "Upington", "Springbok"]),
}

# EE occupational levels, from the Employment Equity Act's reporting categories.
LEVELS = ["Top management", "Senior management", "Professionally qualified", "Skilled technical", "Semi-skilled"]

# department: (share of hires, [(job title, EE level, salary range, education options), ...])
DEPARTMENTS = {
    "Executive": (0.005, [
        ("Executive Director", 0, (2_400_000, 3_600_000), ["Master", "PhD"]),
        ("General Manager", 0, (2_000_000, 3_000_000), ["Honours", "Master"]),
        ("Head of Division", 0, (1_900_000, 2_900_000), ["Honours", "Master"]),
        ("Regional Executive", 0, (1_600_000, 2_400_000), ["Honours", "Master"]),
    ]),
    "HR": (0.02, [
        ("HR Manager", 1, (450_000, 650_000), ["Honours", "Master"]),
        ("HR Officer", 2, (300_000, 450_000), ["Bachelor", "Honours"]),
        ("Recruitment Consultant", 3, (250_000, 400_000), ["Diploma", "Bachelor"]),
        ("HR Assistant", 4, (200_000, 300_000), ["Matric", "Diploma"]),
    ]),
    "IT": (0.18, [
        ("IT Manager", 1, (700_000, 1_200_000), ["Master", "PhD"]),
        ("Software Engineer", 2, (500_000, 800_000), ["Bachelor", "Honours"]),
        ("System Administrator", 3, (350_000, 600_000), ["Diploma", "Bachelor"]),
        ("IT Support Technician", 4, (250_000, 400_000), ["Matric", "Diploma"]),
    ]),
    "Sales": (0.22, [
        ("Sales Executive", 1, (600_000, 1_000_000), ["Bachelor", "Honours"]),
        ("Business Development Manager", 2, (500_000, 900_000), ["Bachelor", "Honours"]),
        ("Account Manager", 2, (350_000, 700_000), ["Bachelor", "Honours"]),
        ("Sales Consultant", 3, (300_000, 600_000), ["Diploma", "Bachelor"]),
    ]),
    "Marketing": (0.08, [
        ("Marketing Director", 1, (800_000, 1_200_000), ["Master", "Honours"]),
        ("Social Media Manager", 2, (400_000, 700_000), ["Diploma", "Bachelor"]),
        ("Content Strategist", 3, (350_000, 600_000), ["Diploma", "Bachelor"]),
        ("Digital Marketer", 3, (300_000, 500_000), ["Diploma", "Bachelor"]),
    ]),
    "Finance": (0.06, [
        ("Financial Manager", 1, (800_000, 1_300_000), ["Honours", "Master"]),
        ("Financial Analyst", 2, (500_000, 900_000), ["Bachelor", "Honours"]),
        ("Accountant", 2, (450_000, 800_000), ["Bachelor", "Honours"]),
        ("Payroll Officer", 3, (350_000, 600_000), ["Diploma", "Bachelor"]),
    ]),
    "Operations": (0.245, [
        ("Operations Manager", 1, (700_000, 1_100_000), ["Bachelor", "Honours"]),
        ("Supply Chain Analyst", 2, (500_000, 800_000), ["Bachelor", "Honours"]),
        ("Warehouse Supervisor", 3, (300_000, 600_000), ["Diploma", "Bachelor"]),
        ("Logistics Coordinator", 3, (250_000, 500_000), ["Diploma", "Bachelor"]),
    ]),
    "Customer Service": (0.19, [
        ("Customer Service Manager", 1, (600_000, 900_000), ["Bachelor", "Honours"]),
        ("Support Specialist", 3, (250_000, 450_000), ["Matric", "Diploma"]),
        ("Call Centre Agent", 4, (200_000, 400_000), ["Matric", "Diploma"]),
        ("Help Desk Assistant", 4, (250_000, 400_000), ["Matric", "Diploma"]),
    ]),
}
# Within a department, the first (manager) title is rarer than the others.
TITLE_WEIGHTS = [0.07, 0.31, 0.31, 0.31]

GROUPS = ["African", "Coloured", "Indian", "White"]
GROUP_SHARES = [0.74, 0.10, 0.05, 0.11]                 # whole workforce (invented)
TOP_GROUP_SHARES = [0.27, 0.07, 0.06, 0.60]             # top and senior management: designated (non-white) share 0.40

MONTHLY = {"Resigned": 0.0075, "Dismissed": 0.0012, "Retired": 0.0006, "Retrenched": 0.0004}


def month_starts(a, b):
    return pd.date_range(a, b, freq="MS")


def make_employees(seed=SEED):
    rng = np.random.default_rng(seed)
    dept_names = list(DEPARTMENTS)
    dept_p = np.array([DEPARTMENTS[d][0] for d in dept_names])
    dept_p = dept_p / dept_p.sum()
    prov_names = list(PROVINCES)
    prov_p = np.array([PROVINCES[p][0] for p in prov_names])
    rows = []
    months = month_starts(START, AS_OF)
    cc_from = months.get_loc(pd.Timestamp(PLANTED["call_centre_from"]))
    for i, m in enumerate(months):
        # Hiring grows from about 60 to about 95 a month; January is the busiest month.
        mean = (60 + 35 * i / len(months)) * (1.3 if m.month == 1 else 1.0)
        for _ in range(rng.poisson(mean)):
            hire = m + pd.Timedelta(days=int(rng.integers(0, m.days_in_month)))
            if hire > AS_OF:
                continue
            dept = dept_names[rng.choice(len(dept_names), p=dept_p)]
            titles = DEPARTMENTS[dept][1]
            w = np.ones(len(titles)) / len(titles) if dept == "Executive" else np.array(TITLE_WEIGHTS)
            title, level, (lo, hi), edu = titles[rng.choice(len(titles), p=w)]
            senior = level <= 1
            gender = "Female" if rng.random() < (0.32 if senior else 0.50) else "Male"
            group = GROUPS[rng.choice(4, p=TOP_GROUP_SHARES if senior else GROUP_SHARES)]
            prov = prov_names[rng.choice(len(prov_names), p=prov_p)]
            leave, reason = None, ""
            # Each later month, a chance of leaving for each reason; resignations carry the planted factors.
            for k in range(i + 1, len(months)):
                factor = 1.0
                if title == "Call Centre Agent" and k >= cc_from:
                    factor = PLANTED["call_centre_factor"]
                if dept == "IT" and gender == "Female":
                    factor = PLANTED["it_women_factor"]
                r = rng.random()
                acc = 0.0
                for why, p in MONTHLY.items():
                    acc += p * (factor if why == "Resigned" else 1.0)
                    if r < acc:
                        mm = months[k]
                        leave, reason = min(mm + pd.Timedelta(days=int(rng.integers(0, mm.days_in_month))), AS_OF), why
                        break
                if leave is not None:
                    break
            rows.append({
                "hire_date": hire.strftime("%Y-%m-%d"),
                "leave_date": leave.strftime("%Y-%m-%d") if leave is not None else "",
                "leave_reason": reason,
                "department": dept,
                "job_title": title,
                "province": prov,
                "city": PROVINCES[prov][1][rng.integers(0, 3)],
                "gender": gender,
                "population_group": group,
                "disability": "Yes" if rng.random() < 0.015 else "No",
                "education": edu[rng.integers(0, len(edu))],
                "salary": int(rng.integers(lo // 1000, hi // 1000 + 1)) * 1000,
                "performance": ["Excellent", "Good", "Satisfactory", "Needs improvement"][rng.choice(4, p=[0.15, 0.5, 0.25, 0.1])],
            })
    df = pd.DataFrame(rows).sort_values(["hire_date", "department", "job_title"], kind="stable").reset_index(drop=True)
    df.insert(0, "employee_id", [f"E{i + 1:05d}" for i in range(len(df))])
    return df


def make_jobs():
    return pd.DataFrame([
        {"job_title": t, "department": d, "ee_level": LEVELS[lvl], "level_sort": lvl + 1}
        for d, (_, titles) in DEPARTMENTS.items() for t, lvl, _, _ in titles
    ])


def make_departments():
    return pd.DataFrame([
        {"department": d, "manager_email": d.lower().replace(" ", ".") + ".manager@example.com", "department_sort": i + 1}
        for i, d in enumerate(DEPARTMENTS)
    ])


def make_calendar():
    days = pd.date_range(START, CALENDAR_TO, freq="D")
    return pd.DataFrame({
        "date": days.strftime("%Y-%m-%d"),
        "year": days.year,
        "quarter": days.year.astype(str) + "-Q" + days.quarter.astype(str),
        "month_no": days.month,
        "month": days.strftime("%b"),
        "year_month": days.strftime("%Y-%m"),
        "is_month_end": days.is_month_end.astype(int),
    })


def headcount(df, day):
    day = pd.Timestamp(day)
    hired = pd.to_datetime(df["hire_date"]) <= day
    left = pd.to_datetime(df["leave_date"].replace("", None)) <= day
    return int((hired & ~left.fillna(False)).sum())


def attrition_12m(df, end, mask=None):
    """Leavers in the 12 months to `end`, over average headcount (start and end of the window)."""
    d = df if mask is None else df[mask]
    end = pd.Timestamp(end)
    start = end - pd.DateOffset(years=1)
    leave = pd.to_datetime(d["leave_date"].replace("", None))
    leavers = int(((leave > start) & (leave <= end)).sum())
    avg = (headcount(d, start) + headcount(d, end)) / 2
    return round(100 * leavers / avg, 1) if avg else None


def expected(df):
    agents = df["job_title"] == "Call Centre Agent"
    it = df["department"] == "IT"
    senior = df["job_title"].map(dict(zip(make_jobs().job_title, make_jobs().level_sort))) <= 2
    current = (pd.to_datetime(df["hire_date"]) <= AS_OF) & (df["leave_date"] == "")
    designated = df["population_group"] != "White"
    return {
        "people_ever_employed": int(len(df)),
        "headcount_as_of": headcount(df, AS_OF),
        "headcount_by_department": {d: headcount(df[df.department == d], AS_OF) for d in DEPARTMENTS},
        "attrition_12m_as_of": attrition_12m(df, AS_OF),
        "call_centre_agent_attrition_12m": {
            "to_2025-06-30": attrition_12m(df, "2025-06-30", agents),
            "to_2026-06-30": attrition_12m(df, "2026-06-30", agents),
        },
        "it_attrition_12m_as_of": {
            "Female": attrition_12m(df, AS_OF, it & (df.gender == "Female")),
            "Male": attrition_12m(df, AS_OF, it & (df.gender == "Male")),
        },
        "designated_share_pct": {
            "all_current": round(100 * (current & designated).sum() / current.sum(), 1),
            "top_and_senior_current": round(100 * (current & designated & senior).sum() / (current & senior).sum(), 1),
        },
    }


def main():
    DATA.mkdir(exist_ok=True)
    df = make_employees()
    df.to_csv(DATA / "employees.csv", index=False, lineterminator="\n")
    make_jobs().to_csv(DATA / "job.csv", index=False, lineterminator="\n")
    make_departments().to_csv(DATA / "department.csv", index=False, lineterminator="\n")
    make_calendar().to_csv(DATA / "calendar.csv", index=False, lineterminator="\n")
    (DATA / "expected.json").write_text(json.dumps(expected(df), indent=2) + "\n", newline="\n")
    print(f"Wrote {len(df)} people, headcount {headcount(df, AS_OF)} on {AS_OF:%d %b %Y}")


if __name__ == "__main__":
    main()
