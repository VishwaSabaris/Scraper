from bs4 import BeautifulSoup
import json
import re

with open("./scratch/dice_sample.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
jobs = []

for s in soup.find_all("script"):
    if s.string and "jobList" in s.string:
        txt = s.string
        idx = txt.find('{"jobList":')
        if idx == -1:
            idx = txt.find('{\\"jobList\\":')
        
        if idx != -1:
            raw_str = txt[idx:]
            # Clean backslashes
            cleaned = raw_str.encode('utf-8').decode('unicode_escape')
            idx2 = cleaned.find('{"jobList":')
            if idx2 != -1:
                sub = cleaned[idx2:]
                depth = 0
                end_idx = 0
                for i, char in enumerate(sub):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break
                if end_idx > 0:
                    try:
                        d = json.loads(sub[:end_idx])
                        data_list = d.get("jobList", {}).get("data", [])
                        print("Successfully parsed Dice jobs:", len(data_list))
                        if data_list:
                            j = data_list[0]
                            print("Sample Dice job:", {
                                "title": j.get("title"),
                                "company": j.get("companyName"),
                                "location": j.get("jobLocation", {}).get("displayName") if isinstance(j.get("jobLocation"), dict) else j.get("jobLocation"),
                                "posted": j.get("postedDate"),
                                "link": j.get("detailsPageUrl"),
                                "salary": j.get("salary"),
                                "type": j.get("employmentType")
                            })
                    except Exception as e:
                        print("JSON parse error:", e)

