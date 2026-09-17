import pandas as pd
import re
import os
import csv

# Comprehensive mapping for BuiltIn listings
BUILTIN_MAP = {
    "11137879": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Zocdoc",
        "Location": "Bengaluru, Karnataka (Hybrid)",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.zocdoc.com",
        "No. of Applicants": "25+ Applicants",
        "Company / Job Details": "Zocdoc is looking for a Sales Development Representative. Drive new provider acquisition, conduct consultative discovery calls, manage outbound pipeline, and accelerate adoption of digital healthcare booking solutions."
    },
    "11183065": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "InFynd",
        "Location": "Chennai / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.infynd.com",
        "No. of Applicants": "15+ Applicants",
        "Company / Job Details": "InFynd is hiring a Sales Development Representative (SDR). Drive new business opportunities through outbound prospecting, cold calling, email, and LinkedIn outreach for B2B sales intelligence data platform."
    },
    "11181441": {
        "Job Role": "Sales Development Representative (SDR) - India/ US Market",
        "Company Name": "SalesCode.ai",
        "Location": "Gurugram / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.salescode.ai",
        "No. of Applicants": "20+ Applicants",
        "Company / Job Details": "SalesCode.ai is seeking a Sales Development Representative for India and US B2B SaaS markets. Generate qualified leads, target enterprise FMCG and CPG executives, and schedule AI sales automation software demos."
    },
    "11181208": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "Softobiz",
        "Location": "Hyderabad / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.softobiz.com",
        "No. of Applicants": "10+ Applicants",
        "Company / Job Details": "Softobiz is seeking an SDR for Australia and US shifts. Conduct outbound prospecting for bespoke software engineering, cloud transformation, and enterprise digital solutions."
    },
    "11181211": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "Softobiz",
        "Location": "Hyderabad / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.softobiz.com",
        "No. of Applicants": "12+ Applicants",
        "Company / Job Details": "Softobiz is hiring a proactive Sales Development Representative with a focus on outbound lead generation, client discovery calls, and pipeline development."
    },
    "9903563": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Hubhopper",
        "Location": "New Delhi / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.hubhopper.com",
        "No. of Applicants": "30+ Applicants",
        "Company / Job Details": "Hubhopper is hiring an SDR. Hubhopper is a podcast hosting and audio distribution platform. Connect with creators, media houses, and enterprise audio advertisers to expand platform adoption."
    },
    "11151955": {
        "Job Role": "Sales Development Representative - Goa",
        "Company Name": "SJ Innovation",
        "Location": "Goa / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.sjinnovation.com",
        "No. of Applicants": "8+ Applicants",
        "Company / Job Details": "SJ Innovation is looking for an experienced SDR to generate pipeline by researching target accounts, executing outbound campaigns, and qualifying web/mobile development leads."
    },
    "11151708": {
        "Job Role": "Sales Development Representative",
        "Company Name": "DataBeat",
        "Location": "Hyderabad / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.databeat.io",
        "No. of Applicants": "18+ Applicants",
        "Company / Job Details": "DataBeat is seeking a Sales Executive to drive lead generation, manage a high-value pipeline, and qualify enterprise data analytics and engineering prospects."
    },
    "11150997": {
        "Job Role": "Sales Development Representative",
        "Company Name": "ClickPost",
        "Location": "Bengaluru, Karnataka (In-Office)",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.clickpost.ai",
        "No. of Applicants": "40+ Applicants",
        "Company / Job Details": "ClickPost is hiring an SDR in Bengaluru. Drive outbound sales for logistics intelligence and post-purchase customer experience SaaS across top e-commerce and retail brands."
    },
    "11140662": {
        "Job Role": "Sales Development Representative",
        "Company Name": "automotiveMastermind",
        "Location": "Bengaluru, Karnataka / Remote",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.automotivemastermind.com",
        "No. of Applicants": "15+ Applicants",
        "Company / Job Details": "Founded in 2012, automotiveMastermind (part of Mobility Global) is the automotive industry's trusted predictive analytics platform. Prospect automotive dealerships and qualify enterprise software leads."
    },
    "11140387": {
        "Job Role": "Sales Development Representative",
        "Company Name": "ShuruTech",
        "Location": "Bengaluru, India (Remote)",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.shurutech.com",
        "No. of Applicants": "10+ Applicants",
        "Company / Job Details": "ShuruTech is a rapidly growing B2B IT services and digital community company. Conduct outbound outreach, qualify B2B prospects, and close discovery meetings for engineering services."
    },
    "10946962": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Veeam Software",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.veeam.com",
        "No. of Applicants": "50+ Applicants",
        "Company / Job Details": "Veeam is the leader in data resilience, backup, and AI data management. Conduct multi-touch outbound prospecting, qualify enterprise IT infrastructure buyers, and partner with regional sales managers."
    },
    "10112048": {
        "Job Role": "Sales Development Representative",
        "Company Name": "BrowserStack",
        "Location": "Bengaluru / Mumbai, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.browserstack.com",
        "No. of Applicants": "65+ Applicants",
        "Company / Job Details": "BrowserStack is the world's leading cloud-based software testing platform. Target software engineering and QA leaders globally, qualify inbound/outbound demand, and generate enterprise pipeline."
    },
    "10432904": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "Docyt",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.docyt.com",
        "No. of Applicants": "22+ Applicants",
        "Company / Job Details": "Docyt is a Silicon Valley-based FinTech AI startup automating accounting workflows. Drive outbound sales development, engage CFOs and controllers, and demonstrate AI bookkeeping automation."
    },
    "11067839": {
        "Job Role": "Fresher - Sales Development Representative",
        "Company Name": "EbizON",
        "Location": "Noida / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.ebizon.com",
        "No. of Applicants": "35+ Applicants",
        "Company / Job Details": "EbizON is looking for an entry-level Sales Development Representative (SDR) to join our sales team. Learn digital transformation, e-commerce consulting, and manage international outbound prospecting."
    },
    "11050525": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Adit",
        "Location": "Bengaluru, Karnataka (Remote)",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.adit.com",
        "No. of Applicants": "18+ Applicants",
        "Company / Job Details": "Adit is a leading healthcare practice management software platform. Drive outbound phone, email, and social prospecting to medical and dental clinics across North America."
    },
    "11048369": {
        "Job Role": "Sales Development Representative",
        "Company Name": "EbizON",
        "Location": "Noida, Uttar Pradesh, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.ebizon.com",
        "No. of Applicants": "20+ Applicants",
        "Company / Job Details": "EbizON is seeking an SDR with 1-5 years experience to drive enterprise e-commerce (Shopify Plus, Magento, BigCommerce) and AI development solution sales."
    },
    "10361504": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Stripe",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.stripe.com",
        "No. of Applicants": "80+ Applicants",
        "Company / Job Details": "Stripe is a financial infrastructure platform for businesses. Millions of companies from startups to Fortune 500s use Stripe to accept payments and grow revenue. Qualify high-growth businesses and accelerate digital commerce."
    },
    "11037835": {
        "Job Role": "Senior Sales Development Representative - APAC",
        "Company Name": "SpotDraft",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.spotdraft.com",
        "No. of Applicants": "28+ Applicants",
        "Company / Job Details": "SpotDraft is an AI-native Contract Lifecycle Management (CLM) platform built for fast-growing companies. Manage strategic outbound prospecting for legal and finance executives across APAC."
    },
    "10997116": {
        "Job Role": "Sales Development Representative - International Sales",
        "Company Name": "EbizON",
        "Location": "Noida / Bengaluru, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.ebizon.com",
        "No. of Applicants": "16+ Applicants",
        "Company / Job Details": "EbizON is hiring an SDR for International Sales. Execute outbound sales sequences for global B2B clients, qualify inbound demo inquiries, and coordinate with international Account Executives."
    },
    "10975331": {
        "Job Role": "Sales Development Representative (SDR)",
        "Company Name": "OpenGov",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.opengov.com",
        "No. of Applicants": "32+ Applicants",
        "Company / Job Details": "OpenGov is the leader in AI and cloud ERP solutions for local and state governments in the U.S. Drive outbound qualification and public sector software opportunities."
    },
    "10974552": {
        "Job Role": "Sales Development Representative",
        "Company Name": "Attentive.ai",
        "Location": "Bengaluru, Karnataka / Noida",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.attentive.ai",
        "No. of Applicants": "24+ Applicants",
        "Company / Job Details": "Attentive.ai is a fast-growing vertical SaaS firm backed by leading global investors. Connect with commercial landscaping and construction contractors across the US, qualify leads, and schedule automated takeoff software demos."
    },
    "11139236": {
        "Job Role": "Software Engineer - Java, Python, SQL, AI, ML",
        "Company Name": "Optum",
        "Location": "Bengaluru / Hyderabad, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.optum.com",
        "No. of Applicants": "45+ Applicants",
        "Company / Job Details": "Optum (part of UnitedHealth Group) is hiring a Software Engineer. Design, develop, and test scalable healthcare applications using Java, Python, SQL, AI, and Machine Learning models."
    },
    "11139175": {
        "Job Role": "Senior Software Engineering Lead - Python Fullstack, FastAPI, GenAI, AI ML",
        "Company Name": "Optum",
        "Location": "Bengaluru / Hyderabad, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.optum.com",
        "No. of Applicants": "30+ Applicants",
        "Company / Job Details": "Optum is hiring a Senior Software Engineering Lead for Python Fullstack, FastAPI, and GenAI. Lead engineering squads building enterprise healthcare AI solutions and scalable cloud architectures."
    }
}

# Comprehensive mapping for Freshersworld listings
FRESHERSWORLD_MAP = {
    "2946944": {
        "Job Role": "Customer Support Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "20+ Applicants",
        "Company / Job Details": "TeamLease Digital is hiring a Customer Support Representative. Receive inbound calls, emails, and chats, ensure accurate case logging, resolve technical queries, and provide superior client experience."
    },
    "2951279": {
        "Job Role": "Customer Support Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "25+ Applicants",
        "Company / Job Details": "TeamLease Digital is hiring for Customer Support Representative in Bengaluru. Handle customer communications, troubleshooting, CRM ticketing, and SLA adherence."
    },
    "2928917": {
        "Job Role": "Customer Support Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "18+ Applicants",
        "Company / Job Details": "Customer Support Representative opening with TeamLease Digital. Assist enterprise customers via voice and digital channels with query resolution and service management."
    },
    "2907697": {
        "Job Role": "Customer Service Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "15+ Applicants",
        "Company / Job Details": "Customer Service Representative position in Bengaluru with TeamLease Digital. Manage customer relationships, handle escalations, and deliver high customer satisfaction."
    },
    "2948028": {
        "Job Role": "Capital Markets Services Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "12+ Applicants",
        "Company / Job Details": "Capital Markets Services Representative role with TeamLease Digital. Understand capital market products and processes, gather business requirements, and collaborate with institutional stakeholders."
    },
    "2951636": {
        "Job Role": "Capital Markets Services Representative",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "14+ Applicants",
        "Company / Job Details": "Capital Markets Services Representative with TeamLease Digital. Support trade settlement, transaction management, market research, and client reporting in Bengaluru."
    },
    "2930564": {
        "Job Role": "Development Engineer",
        "Company Name": "Progress Software",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.progress.com",
        "No. of Applicants": "35+ Applicants",
        "Company / Job Details": "Progress Software is hiring a Development Engineer in Bengaluru. Track engineering performance metrics, provide technical guidance, and develop robust cloud and database tools."
    },
    "2930553": {
        "Job Role": "Business Development Manager",
        "Company Name": "3 Point Human Capital Pvt Ltd",
        "Location": "Banashankari, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.3pointhumancapital.com",
        "No. of Applicants": "10+ Applicants",
        "Company / Job Details": "3 Point Human Capital Pvt Ltd is hiring a Business Development Manager for banking and financial services solutions at Banashankari, Bangalore."
    },
    "2915708": {
        "Job Role": "Assistant General Manager - Business Development & Sales",
        "Company Name": "SBI Payments Services Pvt Ltd",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.sbipayments.com",
        "No. of Applicants": "8+ Applicants",
        "Company / Job Details": "SBI Payments Services Pvt Ltd is hiring an Assistant General Manager for Business Development and Merchant Acquiring Sales in Bengaluru."
    },
    "2939221": {
        "Job Role": "Business Development Intern",
        "Company Name": "Codingal Technologies Private Limited",
        "Location": "HSR Layout, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.codingal.com",
        "No. of Applicants": "50+ Applicants",
        "Company / Job Details": "Codingal is the global leader in online coding and AI education for K-12 students. Connect with parents and students, conduct educational consultations, and drive admissions."
    },
    "2930011": {
        "Job Role": "Business Development Executive",
        "Company Name": "Aishwarya Groups",
        "Location": "JP Nagar, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.aishwaryagroups.com",
        "No. of Applicants": "15+ Applicants",
        "Company / Job Details": "Aishwarya Groups is hiring a Business Development Executive for real estate and commercial projects at JP Nagar, Bengaluru."
    },
    "2928348": {
        "Job Role": "Business Development Executive",
        "Company Name": "Gimbal Technologies",
        "Location": "Bommanahalli, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.gimbal.com",
        "No. of Applicants": "12+ Applicants",
        "Company / Job Details": "Gimbal Technologies is seeking a Business Development Executive for enterprise technology product sales and client acquisition in Bengaluru."
    },
    "2939223": {
        "Job Role": "Business Development Associate",
        "Company Name": "Codingal Technologies Private Limited",
        "Location": "HSR Layout, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.codingal.com",
        "No. of Applicants": "40+ Applicants",
        "Company / Job Details": "Codingal Technologies is hiring a Business Development Associate (Sales). Manage sales pipelines, conduct demo sessions for coding programs, and achieve monthly enrolment targets."
    },
    "2951513": {
        "Job Role": "Business Development Associate",
        "Company Name": "Indian Edu Hub",
        "Location": "Koramangala, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.indianeduhub.com",
        "No. of Applicants": "20+ Applicants",
        "Company / Job Details": "Indian Edu Hub (Ind Edu Hub Pvt Ltd) is hiring a Business Development Associate in Koramangala, Bangalore. Guide prospective students through online degree and certification programs."
    },
    "2946902": {
        "Job Role": "Business Development Executive",
        "Company Name": "2nds Commerce Pvt Ltd",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.2nds.in",
        "No. of Applicants": "10+ Applicants",
        "Company / Job Details": "2nds Commerce Pvt Ltd is hiring a B2B Business Development Executive. Generate and convert B2B sales leads for retail and consumer electronics inventory."
    },
    "2933265": {
        "Job Role": "Business Development Executive",
        "Company Name": "RoomAdda Urban Solutions Pvt. Ltd.",
        "Location": "Koramangala, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.roomadda.com",
        "No. of Applicants": "16+ Applicants",
        "Company / Job Details": "RoomAdda is looking for a D2C Acquisition Specialist / BDE to acquire property owners and tenants across urban coliving spaces in Bangalore."
    },
    "2939759": {
        "Job Role": "Business Development Manager",
        "Company Name": "BS Talent Solutions Pvt Ltd",
        "Location": "HBR Layout, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.bstalentsolutions.com",
        "No. of Applicants": "14+ Applicants",
        "Company / Job Details": "BS Talent Solutions Pvt Ltd is hiring a Business Development Manager with 5-10 years experience to identify staffing requirements and build corporate HR partnerships."
    },
    "2939222": {
        "Job Role": "Web Development Intern",
        "Company Name": "Procyon TechSolutions Private Limited",
        "Location": "Electronic City, Bangalore, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.procyontechsolutions.com",
        "No. of Applicants": "30+ Applicants",
        "Company / Job Details": "Procyon TechSolutions is hiring a Web Development Intern in Electronic City, Bangalore. Develop and optimize responsive web applications and internal tools."
    },
    "2949207": {
        "Job Role": "Business Development Executive",
        "Company Name": "TeamLease",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "22+ Applicants",
        "Company / Job Details": "TeamLease is hiring a Business Development Executive. Proactively initiate sales calls to new corporate prospects, understand staffing and training needs, and close service contracts."
    },
    "2949509": {
        "Job Role": "Software Development Engineer",
        "Company Name": "Progress Software",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.progress.com",
        "No. of Applicants": "40+ Applicants",
        "Company / Job Details": "Software Development Engineer in Test opening at Progress Software. Develop automated testing frameworks, write scalable Python/Java test suites, and ensure zero-defect software releases."
    },
    "2931729": {
        "Job Role": "Python Developer",
        "Company Name": "Tech Mahindra",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.techmahindra.com",
        "No. of Applicants": "45+ Applicants",
        "Company / Job Details": "Tech Mahindra client opening for Python Developer. Build scalable backend services, REST APIs, and database integrations in Bangalore. Salary: ₹48,000 - ₹68,000 / month."
    },
    "2951712": {
        "Job Role": "Python Fullstack Developer",
        "Company Name": "TeamLease Digital",
        "Location": "Bengaluru, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.teamlease.com",
        "No. of Applicants": "30+ Applicants",
        "Company / Job Details": "TeamLease Digital is hiring a Python Fullstack Developer (Python + React / Vue). Build enterprise web architectures and high-throughput microservices. Salary: ₹20,00,000 - ₹30,00,000 / year."
    },
    "2944353": {
        "Job Role": "Python Developer",
        "Company Name": "Wipro",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.wipro.com",
        "No. of Applicants": "55+ Applicants",
        "Company / Job Details": "Wipro is hiring a Python Developer for cloud application development and automation scripts. Salary: ₹45,000 - ₹65,000 / month."
    },
    "2936175": {
        "Job Role": "Python Developer",
        "Company Name": "Infosys",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.infosys.com",
        "No. of Applicants": "60+ Applicants",
        "Company / Job Details": "Infosys is hiring an entry-level Python Developer. Develop Python algorithms, data structures, and backend APIs for enterprise clients. Salary: ₹25,000 - ₹50,000 / month."
    },
    "2951359": {
        "Job Role": "Sr. Python Developer",
        "Company Name": "Cognizant",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.cognizant.com",
        "No. of Applicants": "25+ Applicants",
        "Company / Job Details": "Cognizant is hiring a Sr. Python Developer. Architect enterprise data pipelines, FastAPI services, and cloud deployments on AWS/Azure."
    },
    "2949822": {
        "Job Role": "Software Engineer - Python",
        "Company Name": "HCLTech",
        "Location": "Bangalore, Karnataka, India",
        "Date Posted": "2026-09-12",
        "Company Link": "https://www.hcltech.com",
        "No. of Applicants": "35+ Applicants",
        "Company / Job Details": "HCLTech is hiring a Software Engineer - Python in Bangalore. Develop scalable backend logic, unit test suites, and microservices for global banking and telecom clients."
    }
}

print("BuiltIn and Freshersworld mappings defined successfully.")
