import pandas as pd
import json

# 1. Read existing selective_2.csv
df = pd.read_csv('selective_2.csv')
print(f"Original shape: {df.shape}")

# Backup existing to selective_2.csv.bak_before_wf_fix
df.to_csv('selective_2.csv.bak_before_wf_fix', index=False)

# Load verified Wellfound jobs
with open('scratch/verified_wellfound_jobs.json', 'r', encoding='utf-8') as f:
    wf_jobs = json.load(f)

df_wf = pd.DataFrame(wf_jobs)
# Ensure columns match
df_wf = df_wf[df.columns]

# Remove old Wellfound rows
non_wf_df = df[df['Source'] != 'Wellfound']
print(f"Non-Wellfound rows: {len(non_wf_df)}")

# Concatenate non-Wellfound with new Wellfound jobs
new_df = pd.concat([non_wf_df, df_wf], ignore_index=True)
print(f"New shape: {new_df.shape}")

# Save to selective_2.csv
new_df.to_csv('selective_2.csv', index=False)
print("Updated selective_2.csv successfully!")
