import os
import glob
import csv
import shutil

TARGET_HEADERS = [
    "Job Role", "Company Name", "Location", "Date Posted",
    "Apply Link", "Company Link", "No. of Applicants",
    "Job Description", "Source",
    "website", "apply_link_url"
]

def migrate_csv(filepath):
    """
    Migrates a CSV file to have a single 'Job Description' column,
    eliminating redundant 'Company / Job Details' and 'job_description' duplicates.
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            rows = list(reader)
    except Exception as e:
        print(f"[!] Skipping {filepath} (cannot read): {e}")
        return False, 0, 0

    if not fieldnames:
        return False, 0, 0

    has_comp_det = "Company / Job Details" in fieldnames
    has_job_desc = "job_description" in fieldnames
    has_unified = "Job Description" in fieldnames

    # Only migrate files that have both description columns or need header unification
    if not (has_comp_det and has_job_desc) and not (has_job_desc and not has_unified):
        return False, len(fieldnames), len(rows)

    migrated_rows = []
    for r in rows:
        # Collect candidates
        candidates = []
        for k in ["Job Description", "job_description", "Company / Job Details"]:
            val = str(r.get(k, "") or "").strip()
            if val and val.lower() not in ["n/a", "none", "null", "nan", ""]:
                candidates.append(val)

        if candidates:
            # Sort preferring informative description text over generic fallback strings
            candidates.sort(key=lambda s: (not s.startswith("Role:") and not s.startswith("Company:"), len(s)), reverse=True)
            chosen_desc = candidates[0]
        else:
            role = r.get("Job Role", "Professional")
            comp = r.get("Company Name", "Company")
            loc = r.get("Location", "Remote")
            src = r.get("Source", "JobPortal")
            chosen_desc = f"Company: {comp} | Location: {loc} | Role: {role} | Source: {src} | Actively hiring qualified candidates."

        new_row = {
            "Job Role": r.get("Job Role", ""),
            "Company Name": r.get("Company Name", ""),
            "Location": r.get("Location", ""),
            "Date Posted": r.get("Date Posted", ""),
            "Apply Link": r.get("Apply Link", "") or r.get("apply_link_url", ""),
            "Company Link": r.get("Company Link", "") or r.get("website", ""),
            "No. of Applicants": r.get("No. of Applicants", "Actively Hiring"),
            "Job Description": chosen_desc,
            "Source": r.get("Source", ""),
            "website": r.get("website", "") or r.get("Company Link", ""),
            "apply_link_url": r.get("apply_link_url", "") or r.get("Apply Link", "")
        }
        migrated_rows.append(new_row)

    tmp_path = filepath + ".migrated.tmp"
    with open(tmp_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=TARGET_HEADERS)
        writer.writeheader()
        writer.writerows(migrated_rows)

    shutil.move(tmp_path, filepath)
    return True, len(fieldnames), len(migrated_rows)

def main():
    csv_files = sorted(glob.glob("*.csv"))
    print(f"[*] Scanning {len(csv_files)} CSV files in workspace...")
    migrated_count = 0

    for f in csv_files:
        did_migrate, old_cols, count = migrate_csv(f)
        if did_migrate:
            migrated_count += 1
            print(f"[+] Migrated: {f:35s} | Columns: {old_cols} -> {len(TARGET_HEADERS)} | Rows: {count}")

    print(f"\n[++++] Completed migration of {migrated_count} CSV files to unified 'Job Description' column.")

if __name__ == "__main__":
    main()
