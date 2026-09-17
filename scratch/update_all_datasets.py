import csv
import os

CB_UPDATES = {
    "4530d435-b243-41a0-9a8e-9d31eed08f63": {
        "Job Role": "Sales Development Representative (Automotive SaaS & Marketing Services)",
        "Company Name": "Affinitiv",
        "Location": "Bessemer, AL",
        "Company / Job Details": "Identify and qualify prospective leads across automotive dealer groups and OEM-approved dealerships. Communicate with dealership leadership via phone, email, and LinkedIn to schedule qualified software demonstrations for Account Executives and District Sales Managers."
    },
    "93aa0242-9a39-48d7-8981-554a6c2e8f8a": {
        "Job Role": "Sales Development Representative (SDR) Manager",
        "Company Name": "Alertus Technologies, LLC",
        "Location": "Baltimore, MD",
        "Company / Job Details": "Lead, mentor, and scale the SDR team, providing real-time coaching on prospecting, objection handling, and messaging. Work alongside SDRs to generate opportunities, monitor Salesforce activity, and ensure pipeline and meeting targets are consistently exceeded."
    },
    "c2e8879c-3062-480c-9411-89f503be27b2": {
        "Job Role": "Inside Sales Representative - Account Development",
        "Company Name": "LKQ / Keystone Automotive Operations",
        "Location": "Exeter, PA",
        "Company / Job Details": "Proactively contacting an established base of automotive customers to build relationships and grow accounts. Identifying sales opportunities, recommending specialty products (performance, off-road, truck accessories), and turning prospects into active accounts through outbound calling."
    },
    "8f2fe3c8-136f-4b09-afe1-cc1817523412": {
        "Job Role": "Sales Development Representative (Entry Level)",
        "Company Name": "Ulysses Campos Insurance Agency LLC",
        "Location": "San Antonio, TX",
        "Company / Job Details": "Entry-level Sales Development Representative responsible for contacting prospective clients, qualifying insurance needs, handling outbound outreach, and scheduling consultations for licensed insurance agents."
    },
    "d42e271c-7e8a-4dac-a38b-6ae871c5deaa": {
        "Job Role": "Sales Development Representative [REMOTE]",
        "Company Name": "Synerfac Technical Staffing",
        "Location": "Baltimore, MD",
        "Company / Job Details": "Remote Sales Development Representative responsible for B2B outbound prospecting, qualifying technical staffing and software requirements, and booking initial discovery calls with corporate decision makers."
    },
    "653e6902-124c-49ad-ac74-43361dc8eef7": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Clio",
        "Location": "Vancouver, WA",
        "Company / Job Details": "1-2 years of sales experience or transferable experience, including cold-calling; Knowledge and passion for technology and cloud-based products; A competitive mindset; A continuous improvement mindset. Highly organized and agile, focusing on new accounts spanning all legal market segments."
    },
    "58180083-f6c5-4e22-9603-d8f633332a5e": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Facilities Management Express",
        "Location": "Columbus, OH",
        "Company / Job Details": "Generate new business pipeline through strategic prospecting, outbound outreach, and qualifying facilities management software leads for account executives."
    },
    "fa59d13c-a39d-4020-bcd3-38966edd0415": {
        "Job Role": "Sr. Sales Development Representative (SDR)",
        "Company Name": "Alertus Technologies, LLC",
        "Location": "Baltimore, MD",
        "Company / Job Details": "High-volume B2B prospecting (100+ calls daily), outbound outreach, and partnering with the SDR Manager to coach junior SDRs, analyze KPI performance, and generate enterprise emergency management software pipeline."
    },
    "57abd986-8bad-4e89-97ad-4debde91f2ff": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Generac",
        "Location": "Orlando, FL",
        "Company / Job Details": "Drive incremental sales growth across retail and commercial accounts, conduct outbound discovery calls, and qualify prospective clean energy / power system clients."
    },
    "51afe872-3724-4890-bbee-2980306219f6": {
        "Job Role": "Sales Development Representative - Enterprise",
        "Company Name": "Ascera",
        "Location": "Clearwater, FL",
        "Company / Job Details": "Target enterprise accounts, execute outbound multi-channel campaigns, qualify key decision makers, and schedule enterprise software demonstrations."
    },
    "3b946740-c222-49a9-97d6-8c626c02a145": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "Planet Labs",
        "Location": "San Francisco, CA",
        "Company / Job Details": "Support North American territory pipeline building, qualify inbound/outbound satellite data & Earth observation software prospects, and book discovery meetings for regional sales directors."
    },
    "ee3f82b3-bacf-4232-a2a6-7ea154b2bd81": {
        "Job Role": "Business Development Representative",
        "Company Name": "Vaco LLC",
        "Location": "Indianapolis, IN",
        "Company / Job Details": "Identify and cultivate business relationships, prospect prospective clients for specialized IT consulting and talent solutions, and qualify high-value business opportunities."
    },
    "cc2f26bd-c59f-4112-aba4-351a2b036f9a": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Worth AI",
        "Location": "Orlando, FL",
        "Company / Job Details": "Drive outbound lead generation, qualify enterprise AI risk underwriting and intelligence leads, and collaborate with sales directors to accelerate deal cycles."
    },
    "de3c7481-dd8d-4294-9fa5-a13097b787bd": {
        "Job Role": "Sales Development Representative",
        "Company Name": "EAB",
        "Location": "Philadelphia, PA",
        "Company / Job Details": "Identify and qualify prospective higher education institutional partners, conduct consultative discovery calls, and build sales pipeline for the New Business team."
    },
    "2f1208e0-6b6b-48bc-9d08-49a30d267654": {
        "Job Role": "Business Development Representative - Inside Sales",
        "Company Name": "BBB Heart of Texas",
        "Location": "San Antonio, TX",
        "Company / Job Details": "Inside sales and business development outreach to regional businesses, presenting accreditation programs, handling objections, and closing membership agreements."
    },
    "396b42a4-918c-4234-b99a-1ae203c0a1db": {
        "Job Role": "Sr. Sales Development Representative",
        "Company Name": "Ceros Inc.",
        "Location": "New York, NY",
        "Company / Job Details": "Drive outbound pipeline generation for interactive content creation software, prospect marketing and design leaders, and exceed quarterly demo targets."
    },
    "1e2ab39a-390f-4cac-887b-c2add10a5ee0": {
        "Job Role": "Sales Development Representative 2",
        "Company Name": "TEKsystems",
        "Location": "Creve Coeur, MO",
        "Company / Job Details": "Lead generation, market research using LinkedIn and Gong, building customer profiles, and conducting B2B prospecting for technology and business solutions leading to account management."
    },
    "97d1536f-75b9-42eb-a037-77f6b64240d7": {
        "Job Role": "Senior Enterprise Sales Development Representative",
        "Company Name": "Alation",
        "Location": "Redwood City, CA",
        "Company / Job Details": "Senior pipeline-creation position focused on GTM enterprise strategy, executive-level communication, data intelligence, and technical curiosity."
    },
    "cdebabbf-42c7-45b8-a484-13c9fecd5d6b": {
        "Job Role": "Sales Representative [REMOTE]",
        "Company Name": "Rotating Machinery Services",
        "Location": "Remote / USA",
        "Company / Job Details": "Technical sales outreach, customer relationship management, and generating quotes and sales for specialized industrial turbomachinery and engineering services."
    },
    "f54f0779-9d27-4396-b953-5e3fd2fe1383": {
        "Job Role": "Sales Development Representative (PT or FT)",
        "Company Name": "Choate Agency",
        "Location": "Santa Monica, CA",
        "Company / Job Details": "Sales development and lead generation for insurance and financial planning services with full training, ownership, and residual commission structures."
    },
    "57a7e43c-c495-4c03-aee8-57ab4635e377": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "Jump",
        "Location": "Remote / USA",
        "Company / Job Details": "Sales Development Representative About the Role: Open new opportunities with qualified prospective customers for Jump Account Executives. As one of the first SDRs, build Jump's outbound sales motion to deliver and source reliable, qualified pipeline every month."
    },
    "980f6a5f-3564-41bc-be60-29aa2bef8c7a": {
        "Job Role": "Remote Sales Development Representative (Entry Level)",
        "Company Name": "Equis Financial",
        "Location": "Remote / USA",
        "Company / Job Details": "Remote Sales Development Representative | Entry-Level | Full Training Provided. Seeking motivated individuals to join our growing team as Remote Sales Development Representatives with comprehensive mentorship and flexible schedule."
    },
    "52df04a4-109a-4785-a1bb-a7736b2e6c68": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Conversion",
        "Location": "San Francisco, CA",
        "Company / Job Details": "Now hiring. Sales Development Representative opening in San Francisco, California posted by Conversion. Drive outbound experimentation and conversion rate optimization software pipeline, qualify digital marketing decision makers, and book enterprise demos."
    },
    "a5ad7a59-ec64-4faf-8af1-9d1948084f2e": {
        "Job Role": "Remote Sales Development Representative",
        "Company Name": "Guidebook",
        "Location": "Raleigh, NC",
        "Company / Job Details": "Now hiring. Remote Sales Development Representative - (Raleigh, NC - Remote) opening in Raleigh, NC posted by Guidebook. Drive mobile app platform discovery calls, qualify educational and corporate clients, and accelerate outbound sales opportunities."
    },
    "3d3fcf02-874f-46fd-b837-4d24b3b261f7": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Toro TMS",
        "Location": "Chicago, IL",
        "Company / Job Details": "Sales Development Representative About Toro TMS: Trucking runs on pen and paper or software built decades ago, and most carriers are stitching together a half-dozen tools that don't talk to each other. We're replacing all of it. Toro is a modern, end-to-end TMS built specifically for asset-based carriers."
    },
    "b144f73f-71c0-45b9-8c72-2b2d6e74b06a": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Jeffrey Hines State Farm Agency",
        "Location": "Oak Park, IL",
        "Company / Job Details": "As a Sales Development Representative, you will help generate new business by contacting prospective customers, following up on leads, identifying insurance needs, and creating opportunities for our licensed sales team."
    },
    "5de7e913-d004-4ba7-9b54-1fb321291068": {
        "Job Role": "Sales Development Representative",
        "Company Name": "SV Academy",
        "Location": "Charlotte, NC",
        "Company / Job Details": "Now hiring. Sales Development Representative opening in Charlotte, North Carolina posted by SV Academy. Connect aspiring tech professionals with career development programs, conduct outbound admissions and sales discovery calls, and manage candidate pipeline."
    },
    "8bb78823-8dfd-4186-a35f-97c049ee501c": {
        "Job Role": "Commercial Sales Development Representative",
        "Company Name": "Coefficient",
        "Location": "Austin, TX",
        "Company / Job Details": "Now hiring. Commercial Sales Development Representative opening in Austin, TX posted by Coefficient. Accelerate outbound sales for spreadsheet-to-SaaS data connectivity platform, engage finance and RevOps leaders, and build qualified pipeline."
    },
    "01da41a1-79fc-4f34-926f-25ef17c93977": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Tom James Company",
        "Location": "Tampa, FL",
        "Company / Job Details": "The Sales Development Representative (SDR) role is a full-time, in-person opportunity. Our SDRs play a critical role in expanding our company by generating new leads through phone calling and prospecting methods."
    },
    "b85d2fab-8eb7-42a5-ac31-941e22139c26": {
        "Job Role": "Entry Level Sales Development Representative",
        "Company Name": "Michael Page",
        "Location": "Chicago, IL",
        "Company / Job Details": "This Entry Level Sales Development Representative role is an exciting opportunity to begin a career in sales within the business services industry. The role is based in Chicago and focuses on developing strong client & candidate relationships and achieving sales targets for Michael Page Chicago."
    },
    "82dfb563-6832-4b57-bda6-2e30aa4a818d": {
        "Job Role": "Senior Data Engineer",
        "Company Name": "Sovos Compliance",
        "Location": "London, EN",
        "Company / Job Details": "Senior Data Engineer opening in London, England. Design, construct, and maintain scalable data pipelines and architectures for tax compliance and automated regulatory reporting."
    },
    "779774b2-5127-482d-9166-cbe502e137df": {
        "Job Role": "Spanish Research Analyst",
        "Company Name": "NANA Regional Corporation Inc",
        "Location": "Williamsburg, KY",
        "Company / Job Details": "Spanish Research Analyst opening. Perform bilingual open-source research, data analysis, and intelligence synthesis for defense and government services programs."
    },
    "a0f4b23a-58e0-476b-a3b0-463df1891865": {
        "Job Role": "Aladdin Business Analyst",
        "Company Name": "TechDigital",
        "Location": "London, UK",
        "Company / Job Details": "Aladdin Business Analyst opening in London. Support BlackRock Aladdin investment management platform workflows, portfolio analytics, and trading operations."
    },
    "b6a23832-c526-4250-a879-34c5bc089933": {
        "Job Role": "Spanish Research Analyst",
        "Company Name": "Akima",
        "Location": "Williamsburg, KY",
        "Company / Job Details": "Spanish Research Analyst opening in Williamsburg, KY. Conduct document translation, intelligence analysis, and multilingual investigations."
    },
    "01ca9dce-3695-44df-be05-8a88f80771c9": {
        "Job Role": "Investigative Analyst",
        "Company Name": "U.S. Department of Justice",
        "Location": "London, KY",
        "Company / Job Details": "Investigative Analyst opening in London, KY. Analyze case files, gather evidentiary data, and support federal law enforcement operations."
    },
    "e0f6646f-2948-4445-a83a-af9669bbd356": {
        "Job Role": "Senior Sales Operations & Strategy Analyst",
        "Company Name": "Rubrik",
        "Location": "London, EN",
        "Company / Job Details": "Senior Sales Operations & Strategy Analyst opening. Drive sales planning, quota setting, GTM metrics analysis, and revenue operations for Zero Trust Data Security."
    }
}

def update_csv_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
        
    updated_count = 0
    for row in rows:
        url = row.get("Apply Link", "")
        for uid, data in CB_UPDATES.items():
            if uid in url:
                for k, v in data.items():
                    if k in row:
                        row[k] = v
                updated_count += 1
                break
                
    with open(filepath, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"[+] Successfully updated {updated_count} CareerBuilder records in '{filepath}'")

if __name__ == "__main__":
    target_files = [
        "all_scraped_jobs_26_portals.csv",
        "all_scraped_jobs_26_portals_enriched.csv",
        "all_sdr_26_jobs.csv",
        "careerbuilder_jobs.csv"
    ]
    for tf in target_files:
        update_csv_file(tf)
