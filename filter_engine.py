"""
Universal Job Filter Engine
===========================
Defines the universal filter schema and maps user input queries to portal-specific 
URL query parameters and API payloads across all 26 supported job portals.

Dynamically:
- Evaluates which filters are supported per portal.
- Adapts and formats supported filters to exact portal specs.
- Builds full, high-fidelity web search URLs matching live portal filter schemas.
- Safely omits unsupported filters per portal to prevent query corruption.
- Provides transparent logging of applied vs. omitted filters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse
import re

@dataclass
class UniversalJobFilter:
    # 1. Keywords & Roles
    keywords: str = ""
    job_title: str = ""
    skills: str = ""
    company: str = ""
    
    # 2. Location & Geography
    location: str = ""
    distance_km: Optional[int] = None
    worldwide: bool = False
    timezone: str = ""
    
    # 3. Experience
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    experience_level: str = ""  # 'fresher', 'entry', 'mid', 'senior', 'lead', 'executive'
    
    # 4. Compensation & Salary
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    hide_no_salary: bool = False
    equity: bool = False
    stipend_min: Optional[int] = None
    
    # 5. Work Settings & Modes
    work_mode: str = ""  # 'remote', 'hybrid', 'wfo' (work from office), 'all'
    work_shift: str = "" # 'day', 'night'
    
    # 6. Job & Employment Types
    job_type: str = ""   # 'full_time', 'part_time', 'contract', 'permanent', 'internship', 'temporary', 'third_party'
    
    # 7. Freshness & Posting Date
    date_posted_days: Optional[int] = None # 1 (today/24h), 3, 7 (week), 14/15, 30 (month)
    
    # 8. Industry & Department / Functional Area
    industry: str = ""
    department: str = "" # / functional area
    category: str = ""   # e.g., 'developer', 'ai-data', 'design', 'sales', etc.
    specialism: str = ""
    
    # 9. Company Specifics
    company_type: str = "" # 'startup', 'enterprise', 'mnc', 'corporate'
    company_size: str = "" # 'small', 'midsize', 'large'
    company_stage: str = "" # 'seed', 'series_a', 'series_b', 'public'
    top_employers: bool = False
    employer_type: str = "" # 'company', 'consultant', 'agency'
    
    # 10. Education & Qualification
    education: str = "" # 'be_btech', 'bachelors', 'masters', 'phd'
    
    # 11. Special Filters
    easy_apply: bool = False
    under_10_applicants: bool = False
    early_applicant: bool = False
    freshers_only: bool = False
    walk_in_date: str = ""
    international_jobs: bool = False
    duration_months: Optional[int] = None
    
    # 12. Sorting
    sort_by: str = "relevance" # 'relevance', 'date', 'salary'

    def __post_init__(self):
        if self.location and "remote" in self.location.lower().strip() and not self.work_mode:
            self.work_mode = "remote"


# Capability registry mapping portal names to supported filter attributes
PORTAL_CAPABILITY_MATRIX: Dict[str, List[str]] = {
    "foundit": [
        "keywords", "job_title", "skills", "company", "location", "experience_min", "experience_max",
        "salary_min", "salary_max", "industry", "department", "company_type", "date_posted_days",
        "top_employers", "employer_type", "job_type", "walk_in_date", "international_jobs", "sort_by", "work_mode"
    ],
    "apna": [
        "keywords", "job_title", "location", "date_posted_days", "salary_min", "work_mode", "job_type",
        "work_shift", "department", "sort_by", "experience_min"
    ],
    "instahyre": [
        "keywords", "job_title", "location", "experience_min", "experience_max", "salary_min",
        "job_type", "work_mode", "skills", "company", "industry", "date_posted_days", "education", "sort_by", "company_type", "company_size"
    ],
    "internshala": [
        "keywords", "job_title", "location", "work_mode", "job_type", "category", "stipend_min",
        "experience_min", "skills", "duration_months", "date_posted_days", "company", "salary_min", "sort_by"
    ],
    "shine": [
        "keywords", "job_title", "location", "experience_min", "salary_min", "industry",
        "department", "job_type", "work_mode", "education", "skills", "company", "date_posted_days", "sort_by", "employer_type"
    ],
    "adzuna": [
        "keywords", "job_title", "location", "salary_min", "salary_max", "date_posted_days", "job_type",
        "work_mode", "category", "industry", "company", "distance_km", "sort_by"
    ],
    "builtin": [
        "job_title", "company", "keywords", "location", "work_mode", "early_applicant",
        "job_type", "category", "experience_level", "industry", "company_size", "skills", "salary_min", "sort_by", "date_posted_days"
    ],
    "careerjet": [
        "keywords", "job_title", "location", "distance_km", "salary_min", "job_type",
        "date_posted_days", "company", "category", "work_mode", "sort_by"
    ],
    "dice": [
        "job_title", "skills", "company", "keywords", "location", "easy_apply", "date_posted_days",
        "work_mode", "job_type", "distance_km", "experience_level", "sort_by", "employer_type"
    ],
    "simplyhired": [
        "keywords", "job_title", "skills", "company", "location", "distance_km", "job_type",
        "salary_min", "date_posted_days", "work_mode", "sort_by"
    ],
    "timesjobs": [
        "keywords", "job_title", "location", "experience_min", "experience_max", "salary_min",
        "department", "industry", "job_type", "company", "education", "skills", "date_posted_days", "work_mode", "sort_by"
    ],
    "freshersworld": [
        "keywords", "job_title", "location", "experience_min", "salary_min", "job_type",
        "industry", "department", "education", "skills", "company", "work_mode", "freshers_only", "date_posted_days", "sort_by"
    ],
    "linkedin": [
        "keywords", "job_title", "location", "date_posted_days", "job_type", "experience_level",
        "work_mode", "easy_apply", "under_10_applicants", "company", "industry", "department", "salary_min", "sort_by"
    ],
    "naukri": [
        "keywords", "job_title", "location", "experience_min", "experience_max", "experience_level",
        "salary_min", "salary_max", "job_type", "work_mode", "date_posted_days", "education",
        "industry", "department", "company", "skills", "sort_by", "employer_type", "distance_km", "freshers_only"
    ],
    "careerbuilder": [
        "keywords", "job_title", "location", "date_posted_days", "job_type", "work_mode",
        "experience_level", "salary_min", "company", "industry", "category"
    ],
    "jooble": [
        "keywords", "job_title", "location", "salary_min", "job_type", "date_posted_days",
        "work_mode", "distance_km", "experience_level", "sort_by"
    ],
    "reed": [
        "keywords", "job_title", "location", "salary_min", "salary_max", "job_type", "work_mode",
        "employer_type", "date_posted_days", "specialism", "hide_no_salary", "distance_km"
    ],
    "glassdoor": [
        "keywords", "job_title", "location", "date_posted_days", "job_type", "experience_level",
        "work_mode", "salary_min", "salary_max", "company", "industry", "easy_apply", "distance_km"
    ],
    "himalayas": [
        "keywords", "job_title", "location", "worldwide", "experience_level", "job_type", "salary_min",
        "skills", "company", "industry", "timezone", "sort_by"
    ],
    "indeed": [
        "keywords", "job_title", "location", "date_posted_days", "work_mode", "job_type",
        "salary_min", "experience_level", "company", "education", "distance_km", "sort_by"
    ],
    "jobleads": [
        "keywords", "job_title", "location", "work_mode", "industry", "salary_min",
        "job_type", "experience_level", "company", "date_posted_days"
    ],
    "remote": [
        "keywords", "job_title", "category", "location", "job_type", "experience_level", "skills",
        "company", "date_posted_days", "work_mode", "salary_min"
    ],
    "remote_co": [
        "keywords", "job_title", "category", "location", "job_type", "experience_level", "skills",
        "company", "date_posted_days", "work_mode"
    ],
    "wellfound": [
        "keywords", "job_title", "location", "salary_min", "equity", "job_type",
        "experience_level", "work_mode", "company_stage", "company_size", "industry"
    ],
    "workable": [
        "keywords", "job_title", "location", "department", "job_type", "work_mode",
        "company", "experience_level", "date_posted_days"
    ],
    "workatastartup": [
        "keywords", "job_title", "location", "work_mode", "job_type", "experience_min", "company_size",
        "industry", "equity", "salary_min"
    ],
    "ziprecruiter": [
        "keywords", "job_title", "location", "date_posted_days", "distance_km", "job_type", "salary_min",
        "experience_level", "work_mode", "company"
    ],
    "jobspresso": [
        "keywords", "job_title", "location", "category", "skills"
    ]
}


class FilterEngine:
    """
    Translates UniversalJobFilter instances into portal-specific URL parameters and API payloads.
    Also constructs exact web search URLs matching real-world portal specifications.
    """

    @staticmethod
    def get_effective_role(uf: UniversalJobFilter) -> str:
        """Returns the primary role or keyword search string."""
        terms = []
        if uf.job_title:
            terms.append(uf.job_title)
        if uf.keywords and uf.keywords != uf.job_title:
            terms.append(uf.keywords)
        if not terms and uf.skills:
            terms.append(uf.skills)
        if not terms and uf.company:
            terms.append(uf.company)
        return " ".join(terms) if terms else ""

    @classmethod
    def adapt_for_portal(cls, portal_key: str, uf: UniversalJobFilter) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Translates universal filter to portal-specific parameters.
        Returns:
            (portal_params_dict, applied_filters_list, omitted_filters_list)
        """
        portal_key = portal_key.lower().strip()
        supported = PORTAL_CAPABILITY_MATRIX.get(portal_key, [])
        
        applied = []
        omitted = []
        
        # Check all active fields on UniversalJobFilter
        for k, v in uf.__dict__.items():
            if v is not None and v != "" and v is not False:
                if k in supported:
                    applied.append(f"{k}={v}")
                else:
                    omitted.append(k)

        # Build portal-specific parameter dictionary
        adapter_method = getattr(cls, f"_build_{portal_key}", None)
        if adapter_method:
            portal_params = adapter_method(uf)
        else:
            portal_params = {
                "role": cls.get_effective_role(uf),
                "location": uf.location or ""
            }

        return portal_params, applied, omitted

    # -------------------------------------------------------------
    # PORTAL-SPECIFIC ADAPTERS & URL BUILDERS
    # -------------------------------------------------------------

    @classmethod
    def _build_adzuna(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["w"] = uf.location
        if uf.job_type:
            jt = uf.job_type.lower()
            if "contract" in jt or "temp" in jt:
                params["cty"] = "contract"
                params["contract_type"] = "contract"
            else:
                params["cty"] = "permanent"
                params["contract_type"] = "permanent"
        if uf.date_posted_days:
            days = uf.date_posted_days
            params["date_posted"] = str(days)
            params["f"] = str(days)
        if uf.salary_min:
            params["salary_min"] = str(uf.salary_min)
        if uf.salary_max:
            params["salary_max"] = str(uf.salary_max)
        if uf.distance_km:
            params["distance"] = str(uf.distance_km)
        if uf.sort_by:
            params["sort_by"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_apna(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "search": "true",
            "text": role,
            "raw_text_correction": "true"
        }
        if uf.location:
            params["location_name"] = uf.location if "Region" in uf.location else f"{uf.location} Region"
            params["location"] = uf.location
        if uf.experience_min is not None:
            params["minExperience"] = str(uf.experience_min)
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["workType"] = "part_time"
            elif "intern" in jt:
                params["workType"] = "internship"
            else:
                params["workType"] = "full_time"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workMode"] = "wfh"
                params["workLocationType"] = "WORK_FROM_HOME"
            elif "hybrid" in wm:
                params["workMode"] = "hybrid"
            else:
                params["workMode"] = "wfo"
                params["workLocationType"] = "WORK_FROM_OFFICE"
        if uf.date_posted_days:
            # Apna uses hours in 'postedIn' (24 for 1 day, 168 for 7 days, 720 for 30 days)
            if uf.date_posted_days <= 1:
                params["postedIn"] = "24"
            elif uf.date_posted_days <= 7:
                params["postedIn"] = "168"
            else:
                params["postedIn"] = "720"
        if uf.salary_min:
            params["salary"] = str(uf.salary_min)
            params["minSalary"] = str(uf.salary_min)
        if uf.work_shift:
            params["workShift"] = "NIGHT_SHIFT" if "night" in uf.work_shift.lower() else "DAY_SHIFT"
        if uf.department:
            params["department"] = uf.department
        if uf.sort_by:
            params["sort"] = "RECENT" if "date" in uf.sort_by.lower() else "RELEVANCE"
        return params

    @classmethod
    def _build_builtin(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "search": role,
            "allLocations": "true"
        }
        if uf.location:
            loc = uf.location.lower().strip()
            if any(k in loc for k in ["uk", "gbr", "london", "united kingdom"]):
                params["country"] = "GBR"
            elif any(k in loc for k in ["us", "usa", "united states", "boston", "nyc", "sf"]):
                params["country"] = "USA"
            elif any(k in loc for k in ["in", "ind", "india", "bangalore", "bengaluru"]):
                params["country"] = "IND"
            params["location"] = uf.location
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["remote"] = "1"
                params["workplace_path"] = "remote"
            elif "hybrid" in wm:
                params["remote"] = "2"
                params["workplace_path"] = "hybrid"
            else:
                params["remote"] = "3"
                params["workplace_path"] = "office"
        if uf.experience_level:
            params["experience"] = uf.experience_level.lower()
        if uf.date_posted_days:
            params["days_since_updated"] = str(uf.date_posted_days)
        if uf.company_size:
            params["company_size"] = uf.company_size
        return params

    @classmethod
    def _build_careerbuilder(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["where"] = uf.location
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["recency"] = "last 24 hours"
                params["posted"] = "1"
            elif uf.date_posted_days <= 7:
                params["recency"] = "last 7 days"
                params["posted"] = "7"
            else:
                params["recency"] = "last month"
                params["posted"] = "30"
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["cb_workplace"] = "telecommute"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["emp"] = "jtpt"
            elif "contract" in jt:
                params["emp"] = "jtct"
            else:
                params["emp"] = "jtft"
        return params

    @classmethod
    def _build_careerjet(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "s": role
        }
        if uf.location:
            params["l"] = uf.location
        if uf.date_posted_days:
            params["nw"] = str(uf.date_posted_days)
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["cp"] = "p"
            else:
                params["cp"] = "f"
            if "contract" in jt or "temp" in jt:
                params["ct"] = "c"
            else:
                params["ct"] = "p"
        if uf.distance_km:
            params["radius"] = str(uf.distance_km)
        if uf.sort_by:
            params["sort"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_dice(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["location"] = uf.location
        params["radius"] = str(uf.distance_km or 30)
        params["radiusUnit"] = "mi"
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["filters.postedDate"] = "ONE"
            elif uf.date_posted_days <= 3:
                params["filters.postedDate"] = "THREE"
            elif uf.date_posted_days <= 7:
                params["filters.postedDate"] = "SEVEN"
            elif uf.date_posted_days <= 14:
                params["filters.postedDate"] = "FOURTEEN"
            else:
                params["filters.postedDate"] = "THIRTY"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "contract" in jt:
                params["filters.employmentType"] = "CONTRACTS"
            elif "third" in jt:
                params["filters.employmentType"] = "THIRD_PARTY"
            elif "part" in jt:
                params["filters.employmentType"] = "PARTTIME"
            else:
                params["filters.employmentType"] = "FULLTIME"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["filters.workplaceTypes"] = "Remote"
            elif "hybrid" in wm:
                params["filters.workplaceTypes"] = "Hybrid"
            else:
                params["filters.workplaceTypes"] = "On-Site"
        if uf.employer_type:
            params["filters.employerType"] = "Direct Hire" if "company" in uf.employer_type.lower() or "direct" in uf.employer_type.lower() else "Recruiter"
        else:
            params["filters.employerType"] = "Direct Hire"
        if uf.experience_level:
            el = uf.experience_level.lower()
            if "entry" in el or "fresher" in el or "junior" in el:
                params["filters.experienceLevel"] = "ENTRY_LEVEL"
            elif "mid" in el:
                params["filters.experienceLevel"] = "MID_LEVEL"
            elif "senior" in el or "lead" in el or "exec" in el:
                params["filters.experienceLevel"] = "SENIOR_LEVEL"
        return params

    @classmethod
    def _build_foundit(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role,
            "queryDerived": "true"
        }
        if uf.location:
            params["location"] = uf.location
            params["jobCities"] = uf.location
            params["locations"] = uf.location
        if uf.experience_min is not None or uf.experience_max is not None:
            emin = uf.experience_min if uf.experience_min is not None else 0
            emax = uf.experience_max if uf.experience_max is not None else emin
            params["experienceRanges"] = f"{emin}~{emax}"
        if uf.date_posted_days:
            params["jobFreshness"] = str(uf.date_posted_days)
            params["postedDate"] = str(uf.date_posted_days)
        if uf.job_type:
            params["jobTypes"] = "Permanent Job" if "full" in uf.job_type.lower() or "perm" in uf.job_type.lower() else "Contract"
        if uf.employer_type:
            params["postedBy"] = "Company" if "company" in uf.employer_type.lower() or "direct" in uf.employer_type.lower() else "Consultant"
        else:
            params["postedBy"] = "Company"
        if uf.salary_min or uf.salary_max:
            smin = uf.salary_min or 0
            smax = uf.salary_max or 10000000
            params["salaryRanges"] = f"{smin}~{smax}"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workMode"] = "remote"
            elif "hybrid" in wm:
                params["workMode"] = "hybrid"
            else:
                params["workMode"] = "wfo"
        if uf.sort_by:
            params["sort"] = "2" if "date" in uf.sort_by.lower() else "1"
        return params

    @classmethod
    def _build_freshersworld(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role
        }
        if uf.location:
            params["city"] = uf.location
        if uf.education:
            params["course"] = uf.education
        if uf.job_type:
            params["jobtype"] = "internship" if "intern" in uf.job_type.lower() else "fulltime"
        return params

    @classmethod
    def _build_glassdoor(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "sc.keyword": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.date_posted_days:
            params["fromAge"] = str(uf.date_posted_days)
        if uf.salary_min:
            params["minSalary"] = str(uf.salary_min)
        if uf.salary_max:
            params["maxSalary"] = str(uf.salary_max)
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["remoteWorkType"] = "1"
            elif "hybrid" in wm:
                params["remoteWorkType"] = "2"
            else:
                params["remoteWorkType"] = "0"
        if uf.job_type:
            params["jobType"] = uf.job_type.lower()
        return params

    @classmethod
    def _build_indeed(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["l"] = uf.location
        if uf.date_posted_days:
            params["fromage"] = str(uf.date_posted_days)
        if uf.distance_km:
            params["radius"] = str(int(uf.distance_km * 0.621371))
        else:
            params["radius"] = "25"
        if uf.salary_min:
            params["salaryType"] = str(uf.salary_min)
        if uf.job_type:
            params["jt"] = uf.job_type.lower()
        if uf.sort_by:
            params["sort"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_instahyre(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "skills": uf.skills or role,
            "search": "true",
            "isLandingPage": "true",
            "company_size": "0"
        }
        if uf.location:
            params["location"] = uf.location
            params["locations"] = uf.location
        if uf.experience_min is not None:
            params["years"] = str(uf.experience_min)
            if uf.experience_min <= 2:
                params["experience"] = "0-2"
            elif uf.experience_min <= 5:
                params["experience"] = "3-5"
            elif uf.experience_min <= 8:
                params["experience"] = "6-8"
            else:
                params["experience"] = "9-12"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "intern" in jt:
                params["job_type"] = "2"
            else:
                params["job_type"] = "1"
        return params

    @classmethod
    def _build_himalayas(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "view": "filters",
            "src": "adv"
        }
        if uf.location:
            params["country"] = uf.location
        if uf.job_type:
            params["employment_type"] = "full-time" if "full" in uf.job_type.lower() else uf.job_type.lower()
        if uf.salary_min or uf.salary_max:
            smin = uf.salary_min or 0
            smax = uf.salary_max or 100000
            params["salary"] = f"{smin},{smax}"
            params["currency"] = "inr" if uf.location and "india" in uf.location.lower() else "usd"
        return params

    @classmethod
    def _build_jobleads(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["filter_by_remote"] = "remote"
            elif "hybrid" in wm:
                params["filter_by_remote"] = "hybrid"
            else:
                params["filter_by_remote"] = "in_person"
        if uf.salary_min:
            params["minSalary"] = str(uf.salary_min)
            params["salary"] = str(uf.salary_min)
        if uf.date_posted_days:
            params["posted"] = str(uf.date_posted_days)
        return params

    @classmethod
    def _build_internshala(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "role": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.experience_min is not None:
            params["experience"] = str(uf.experience_min)
        if uf.salary_min:
            # Internshala salary filters are in lakhs (e.g. 5 for 5 LPA)
            sal_lakhs = uf.salary_min // 100000 if uf.salary_min >= 100000 else uf.salary_min
            params["salary"] = str(sal_lakhs)
            params["annual_salary"] = str(sal_lakhs)
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["work_from_home"] = "true"
        if uf.job_type and "part" in uf.job_type.lower():
            params["part_time"] = "true"
        return params

    @classmethod
    def _build_jooble(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "ukw": role,
            "role": role
        }
        if uf.location:
            params["rgns"] = uf.location
            params["location"] = uf.location
        if uf.date_posted_days:
            params["date"] = str(uf.date_posted_days)
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["jt"] = "2"
            elif "contract" in jt:
                params["jt"] = "3"
            elif "intern" in jt:
                params["jt"] = "4"
            else:
                params["jt"] = "1"
        if uf.salary_min:
            params["salaryMin"] = str(uf.salary_min)
            params["salary"] = str(uf.salary_min)
            params["salaryRate"] = "5" # Annual salary
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["telework"] = "1"
        return params

    @classmethod
    def _build_linkedin(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        is_remote = (
            (uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower())) or
            (uf.location and "remote" in uf.location.lower().strip())
        )
        is_hybrid = uf.work_mode and "hybrid" in uf.work_mode.lower()
        is_wfo = uf.work_mode and ("wfo" in uf.work_mode.lower() or "office" in uf.work_mode.lower() or "onsite" in uf.work_mode.lower())

        effective_keywords = role
        if is_remote:
            if "remote" not in effective_keywords.lower():
                effective_keywords = f"{effective_keywords} Remote"
        elif is_hybrid:
            if "hybrid" not in effective_keywords.lower():
                effective_keywords = f"{effective_keywords} Hybrid"
        elif is_wfo:
            if "on-site" not in effective_keywords.lower() and "onsite" not in effective_keywords.lower():
                effective_keywords = f"{effective_keywords} On-site"

        params: Dict[str, Any] = {
            "keywords": effective_keywords
        }
        
        # If location is simply 'remote', 'worldwide', or 'any', omit location parameter
        # so LinkedIn searches worldwide and doesn't match geographic towns named 'Remote'
        if uf.location:
            loc_clean = uf.location.strip()
            if loc_clean.lower() not in ["remote", "worldwide", "any"]:
                params["location"] = loc_clean

        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["f_TPR"] = "r86400"
            elif uf.date_posted_days <= 7:
                params["f_TPR"] = "r604800"
            elif uf.date_posted_days <= 30:
                params["f_TPR"] = "r2592000"

        if is_remote:
            params["f_WT"] = "2"
        elif is_hybrid:
            params["f_WT"] = "3"
        elif is_wfo:
            params["f_WT"] = "1"
        if uf.experience_level:
            el = uf.experience_level.lower()
            if "intern" in el:
                params["f_E"] = "1"
            elif "entry" in el or "fresher" in el or "junior" in el:
                params["f_E"] = "2"
            elif "associate" in el:
                params["f_E"] = "3"
            elif "mid" in el or "senior" in el:
                params["f_E"] = "4"
            elif "director" in el:
                params["f_E"] = "5"
            elif "exec" in el:
                params["f_E"] = "6"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["f_JT"] = "P"
            elif "contract" in jt:
                params["f_JT"] = "C"
            elif "temp" in jt:
                params["f_JT"] = "T"
            elif "intern" in jt:
                params["f_JT"] = "I"
            else:
                params["f_JT"] = "F"
        if uf.easy_apply:
            params["f_AL"] = "true"
        if uf.under_10_applicants:
            params["f_EA"] = "true"
        if uf.sort_by:
            params["sortBy"] = "DD" if "date" in uf.sort_by.lower() else "R"
        return params

    @classmethod
    def _build_naukri(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        """
        Translates UniversalJobFilter into exact, case-sensitive Naukri URL query parameters.
        Matches live Naukri.com search routing, facet IDs, and parameter keys:
        - k: keywords / job role
        - l: location name
        - cityTypeGid: city grouping ID (e.g. 9508 for Bangalore, 9513 for Chennai)
        - experience: experience years/range (e.g. '0', '1', '2', '3', '3-5')
        - wfhType: 0 (Work from office), 1 (Hybrid), 2 (Remote)
        - ctcFilter: salary CTC bracket (0to3, 3to6, 6to10, 10to15, 15to25, 25to50, 50to75, 75to100, 100to500)
        - department: exact department name from the 32 official Naukri departments
        - jobAge: freshness in days (1, 3, 7, 15, 30)
        - sort: 'r' (Relevance), 'f' (Freshness / Date)
        - jobType: '1' (Full-time), '2' (Part-time), '3' (Contractual), '4' (Internship)
        - postedBy: '1' (Company), '2' (Consultant)
        - education: exact qualification string (e.g. 'B.Tech/B.E.', 'MCA', 'MBA/PGDM')
        - industry: exact industry string (e.g. 'IT Services & Consulting', 'Software Product')
        - qproductJobSource: '2' (Desktop job search source)
        - nignbevent_src: 'jobsearchDeskGNB' (Desktop GNB search event)
        - naukriCampus: 'true' (appended for 0-experience / campus / fresher jobs)
        """
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "k": role
        }
        
        # 1. Location
        if uf.location:
            params["l"] = uf.location

        # Standard desk navigation tracking parameters
        params["qproductJobSource"] = "2"
        params["nignbevent_src"] = "jobsearchDeskGNB"

        # 2. Experience Filter (direct integer value or range)
        if uf.experience_min is not None and uf.experience_max is not None:
            params["experience"] = f"{uf.experience_min}-{uf.experience_max}"
            if uf.experience_min == 0:
                params["naukriCampus"] = "true"
        elif uf.experience_min is not None:
            params["experience"] = str(uf.experience_min)
            if uf.experience_min == 0:
                params["naukriCampus"] = "true"
        elif uf.freshers_only:
            params["experience"] = "0"
            params["naukriCampus"] = "true"
        elif uf.experience_level:
            el = uf.experience_level.lower().strip()
            if any(k in el for k in ["fresher", "intern", "entry", "0", "campus"]):
                params["experience"] = "0"
                params["naukriCampus"] = "true"
            elif "associate" in el:
                params["experience"] = "1-2"
            elif "mid" in el:
                params["experience"] = "3-5"
            elif any(k in el for k in ["senior", "sr"]):
                params["experience"] = "6-10"
            elif any(k in el for k in ["lead", "director", "exec"]):
                params["experience"] = "10+"

        # 3. Work Mode Filter (wfhType: 0=Office, 1=Hybrid, 2=Remote)
        if uf.work_mode:
            wm = uf.work_mode.lower().strip()
            if any(k in wm for k in ["both", "all"]):
                params["wfhType"] = "0,1,2"
            elif ("remote" in wm or "wfh" in wm or "home" in wm) and "hybrid" in wm:
                params["wfhType"] = "1,2"
            elif any(k in wm for k in ["remote", "wfh", "home"]):
                params["wfhType"] = "2"
            elif "hybrid" in wm:
                params["wfhType"] = "1"
            elif any(k in wm for k in ["office", "wfo", "onsite", "on-site"]):
                params["wfhType"] = "0"
            else:
                params["wfhType"] = "0"

        # 4. Salary / CTC Filter (exact Naukri brackets: 0to3, 3to6, 6to10, 10to15, 15to25, 25to50, 50to75, 75to100, 100to500)
        if uf.salary_min or uf.salary_max:
            smin = uf.salary_min or 0
            if smin < 300000:
                params["ctcFilter"] = "0to3"
            elif smin < 600000:
                params["ctcFilter"] = "3to6"
            elif smin < 1000000:
                params["ctcFilter"] = "6to10"
            elif smin < 1500000:
                params["ctcFilter"] = "10to15"
            elif smin < 2500000:
                params["ctcFilter"] = "15to25"
            elif smin < 5000000:
                params["ctcFilter"] = "25to50"
            elif smin < 7500000:
                params["ctcFilter"] = "50to75"
            elif smin < 10000000:
                params["ctcFilter"] = "75to100"
            else:
                params["ctcFilter"] = "100to500"

        # 5. Freshness / Date Posted (jobAge: 1, 3, 7, 15, 30)
        if uf.date_posted_days:
            days = uf.date_posted_days
            if days <= 1:
                params["jobAge"] = "1"
            elif days <= 3:
                params["jobAge"] = "3"
            elif days <= 7:
                params["jobAge"] = "7"
            elif days <= 15:
                params["jobAge"] = "15"
            else:
                params["jobAge"] = "30"

        # 6. Sort Order (sort: 'r'=Relevance, 'f'=Freshness / Date Posted)
        if uf.sort_by:
            params["sort"] = "f" if any(k in uf.sort_by.lower() for k in ["date", "fresh", "recent"]) else "r"

        # 7. Employment / Job Type (jobType: 1=Full-time, 2=Part-time, 3=Contractual, 4=Internship)
        if uf.job_type:
            jt = uf.job_type.lower().strip()
            if any(k in jt for k in ["part"]):
                params["jobType"] = "2"
            elif any(k in jt for k in ["contract", "temp"]):
                params["jobType"] = "3"
            elif any(k in jt for k in ["intern"]):
                params["jobType"] = "4"
            else:
                params["jobType"] = "1"

        # 8. Employer Type (postedBy: 1=Company, 2=Consultant)
        if uf.employer_type:
            et = uf.employer_type.lower().strip()
            params["postedBy"] = "2" if any(k in et for k in ["consultant", "agency", "recruiter"]) else "1"

        # 9. Education Qualification (exact letter and casing mapping)
        if uf.education:
            ed_raw = uf.education.strip()
            ed_lower = ed_raw.lower()
            if any(k in ed_lower for k in ["b.e/b.tech", "be/btech", "b.tech", "btech", "b.e", "be"]):
                params["education"] = "B.Tech/B.E."
            elif "mca" in ed_lower:
                params["education"] = "MCA"
            elif any(k in ed_lower for k in ["m.tech", "mtech"]):
                params["education"] = "M.Tech"
            elif any(k in ed_lower for k in ["ms", "m.sc", "msc"]):
                params["education"] = "MS/M.Sc(Science)"
            elif "bca" in ed_lower:
                params["education"] = "BCA"
            elif any(k in ed_lower for k in ["b.sc", "bsc"]):
                params["education"] = "B.Sc"
            elif any(k in ed_lower for k in ["b.com", "bcom"]):
                params["education"] = "B.Com"
            elif any(k in ed_lower for k in ["b.a", "ba"]):
                params["education"] = "B.A"
            elif any(k in ed_lower for k in ["b.b.a", "bba", "bms"]):
                params["education"] = "B.B.A/B.M.S"
            elif any(k in ed_lower for k in ["mba", "pgdm"]):
                params["education"] = "MBA/PGDM"
            elif "any graduate" in ed_lower:
                params["education"] = "Any Graduate"
            elif "any post" in ed_lower:
                params["education"] = "Any Postgraduate"
            else:
                params["education"] = ed_raw

        # 10. Industry (exact letter and casing mapping)
        if uf.industry:
            ind_raw = uf.industry.strip()
            ind_lower = ind_raw.lower()
            if any(k in ind_lower for k in ["it services", "information technology", "tech", "it"]):
                params["industry"] = "IT Services & Consulting"
            elif any(k in ind_lower for k in ["software product", "product"]):
                params["industry"] = "Software Product"
            elif any(k in ind_lower for k in ["financial", "finance", "bfsi"]):
                params["industry"] = "Financial Services"
            elif "banking" in ind_lower:
                params["industry"] = "Banking"
            elif any(k in ind_lower for k in ["health", "pharma", "life science"]):
                params["industry"] = "Healthcare & Life Sciences"
            elif any(k in ind_lower for k in ["internet", "ecommerce", "e-commerce"]):
                params["industry"] = "Internet"
            elif any(k in ind_lower for k in ["recruitment", "staffing"]):
                params["industry"] = "Recruitment / Staffing"
            elif any(k in ind_lower for k in ["education", "edtech", "training"]):
                params["industry"] = "Education / Training"
            elif any(k in ind_lower for k in ["telecom", "telecommunication"]):
                params["industry"] = "Telecommunication"
            elif any(k in ind_lower for k in ["auto", "automotive", "automobile"]):
                params["industry"] = "Automobile"
            else:
                params["industry"] = ind_raw

        # 11. Department (Exact mapping for all 32 official Naukri UI departments)
        if uf.department:
            dept_raw = uf.department.strip()
            dept_lower = dept_raw.lower()
            
            # Official 32 Naukri departments list:
            canonical_departments = [
                "Engineering - Software & QA",
                "Sales & Business Development",
                "Customer Success, Service & Operations",
                "Data Science & Analytics",
                "IT & Information Security",
                "Engineering - Hardware & Networks",
                "Marketing & Communication",
                "Human Resources",
                "Finance & Accounting",
                "BFSI, Investments & Trading",
                "Research & Development",
                "Healthcare & Life Sciences",
                "Teaching & Training",
                "Production, Manufacturing & Engineering",
                "Other",
                "Administration & Facilities",
                "Product Management",
                "Content, Editorial & Journalism",
                "Procurement & Supply Chain",
                "Quality Assurance",
                "UX, Design & Architecture",
                "Food, Beverage & Hospitality",
                "Consulting",
                "Project & Program Management",
                "Media Production & Entertainment",
                "Strategic & Top Management",
                "Construction & Site Engineering",
                "CSR & Social Service",
                "Environment Health & Safety",
                "Legal & Regulatory",
                "Merchandising, Retail & eCommerce",
                "Security Services"
            ]
            
            # Exact match check
            matched_dept = None
            for c_dept in canonical_departments:
                if dept_lower == c_dept.lower():
                    matched_dept = c_dept
                    break
                    
            if not matched_dept:
                # Intelligent alias / keyword mapping to official 32 departments
                if any(k in dept_lower for k in ["data science", "analytics", "data analyst", "data scientist", "machine learning", "ai", "artificial intelligence", "bi", "business intelligence", "deep learning"]):
                    matched_dept = "Data Science & Analytics"
                elif any(k in dept_lower for k in ["software & qa", "software", "sdet", "developer", "development", "frontend", "backend", "fullstack", "devops", "cloud", "web dev"]):
                    matched_dept = "Engineering - Software & QA"
                elif any(k in dept_lower for k in ["hardware", "embedded", "vlsi", "telecom infra", "network engineer"]):
                    matched_dept = "Engineering - Hardware & Networks"
                elif any(k in dept_lower for k in ["sales", "bd", "business development", "sdr", "bdr", "inside sales", "account executive"]):
                    matched_dept = "Sales & Business Development"
                elif any(k in dept_lower for k in ["customer success", "customer service", "customer support", "csm", "call center", "bpo", "operations"]):
                    matched_dept = "Customer Success, Service & Operations"
                elif any(k in dept_lower for k in ["security", "cyber", "infosec", "information security", "system admin"]):
                    matched_dept = "IT & Information Security"
                elif any(k in dept_lower for k in ["marketing", "communication", "growth", "seo", "sem", "digital marketing", "pr"]):
                    matched_dept = "Marketing & Communication"
                elif any(k in dept_lower for k in ["hr", "human resources", "recruitment", "talent acquisition", "people ops", "payroll"]):
                    matched_dept = "Human Resources"
                elif any(k in dept_lower for k in ["finance", "accounting", "tax", "audit", "ca", "financial reporting"]):
                    matched_dept = "Finance & Accounting"
                elif any(k in dept_lower for k in ["bfsi", "banking", "wealth", "trading", "investment", "fintech", "insurance"]):
                    matched_dept = "BFSI, Investments & Trading"
                elif any(k in dept_lower for k in ["r&d", "research & development", "scientist", "scientific"]):
                    matched_dept = "Research & Development"
                elif any(k in dept_lower for k in ["healthcare", "life science", "pharma", "biotech", "clinical", "hospital", "medical"]):
                    matched_dept = "Healthcare & Life Sciences"
                elif any(k in dept_lower for k in ["teaching", "training", "trainer", "professor", "faculty", "education", "tutor"]):
                    matched_dept = "Teaching & Training"
                elif any(k in dept_lower for k in ["manufacturing", "production", "plant", "mechanical", "industrial"]):
                    matched_dept = "Production, Manufacturing & Engineering"
                elif any(k in dept_lower for k in ["admin", "facility", "facilities", "office manager", "front office"]):
                    matched_dept = "Administration & Facilities"
                elif any(k in dept_lower for k in ["product management", "product manager", "pm", "product owner", "technical pm"]):
                    matched_dept = "Product Management"
                elif any(k in dept_lower for k in ["content", "editorial", "journalism", "copywriter", "writer", "editor"]):
                    matched_dept = "Content, Editorial & Journalism"
                elif any(k in dept_lower for k in ["procurement", "supply chain", "logistics", "purchase", "warehouse", "inventory"]):
                    matched_dept = "Procurement & Supply Chain"
                elif any(k in dept_lower for k in ["quality assurance", "quality control", "iso"]):
                    matched_dept = "Quality Assurance"
                elif any(k in dept_lower for k in ["ux", "ui/ux", "product designer", "graphic designer", "visual design", "design & architecture"]):
                    matched_dept = "UX, Design & Architecture"
                elif any(k in dept_lower for k in ["food", "beverage", "hospitality", "hotel", "chef", "restaurant", "catering"]):
                    matched_dept = "Food, Beverage & Hospitality"
                elif any(k in dept_lower for k in ["consulting", "consultant", "advisory", "strategy consultant"]):
                    matched_dept = "Consulting"
                elif any(k in dept_lower for k in ["project & program", "project management", "program management", "scrum master", "agile"]):
                    matched_dept = "Project & Program Management"
                elif any(k in dept_lower for k in ["media", "entertainment", "video editor", "animator", "broadcasting"]):
                    matched_dept = "Media Production & Entertainment"
                elif any(k in dept_lower for k in ["strategic", "top management", "strategy", "cxo", "ceo", "director", "vp", "general manager"]):
                    matched_dept = "Strategic & Top Management"
                elif any(k in dept_lower for k in ["construction", "site engineering", "civil", "structural"]):
                    matched_dept = "Construction & Site Engineering"
                elif any(k in dept_lower for k in ["csr", "social service", "ngo", "social work", "sustainability"]):
                    matched_dept = "CSR & Social Service"
                elif any(k in dept_lower for k in ["environment health", "ehs", "safety officer", "industrial safety"]):
                    matched_dept = "Environment Health & Safety"
                elif any(k in dept_lower for k in ["legal", "regulatory", "lawyer", "advocate", "compliance"]):
                    matched_dept = "Legal & Regulatory"
                elif any(k in dept_lower for k in ["retail", "ecommerce", "e-commerce", "merchandising", "category manager"]):
                    matched_dept = "Merchandising, Retail & eCommerce"
                elif any(k in dept_lower for k in ["security services", "physical security", "security guard", "surveillance"]):
                    matched_dept = "Security Services"
                else:
                    matched_dept = dept_raw
                    
            params["department"] = matched_dept

        # 12. Specific Company Name
        if uf.company:
            params["company"] = uf.company.strip()

        # 13. Specific Skills
        if uf.skills:
            params["skills"] = uf.skills.strip()

        return params

    @classmethod
    def _build_reed(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "keywords": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.salary_min:
            params["salaryFrom"] = str(uf.salary_min)
            params["salarymin"] = str(uf.salary_min)
        if uf.salary_max:
            params["salarymax"] = str(uf.salary_max)
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["partTime"] = "true"
            elif "contract" in jt:
                params["contract"] = "true"
            elif "temp" in jt:
                params["temp"] = "true"
            else:
                params["perm"] = "true"
                params["fullTime"] = "true"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workingOption"] = "remote"
                params["workfromhome"] = "true"
            elif "hybrid" in wm:
                params["workingOption"] = "hybrid"
                params["hybrid"] = "true"
            else:
                params["workingOption"] = "onSite"
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["dateCreatedOffSet"] = "today"
            elif uf.date_posted_days <= 3:
                params["dateCreatedOffSet"] = "lastthreedays"
            elif uf.date_posted_days <= 7:
                params["dateCreatedOffSet"] = "lastweek"
            else:
                params["dateCreatedOffSet"] = "lasttwoweeks"
        return params

    @classmethod
    def _build_remote(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role
        }
        if uf.location:
            loc = uf.location.lower().strip()
            if any(k in loc for k in ["india", "in", "ind", "bangalore", "bengaluru"]):
                params["country"] = "IND"
            elif any(k in loc for k in ["us", "usa", "united states", "boston", "nyc"]):
                params["country"] = "USA"
            elif any(k in loc for k in ["uk", "gbr", "united kingdom", "london"]):
                params["country"] = "GBR"
            else:
                params["country"] = uf.location
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["employmentType"] = "part_time"
            elif "contract" in jt:
                params["employmentType"] = "contract"
            else:
                params["employmentType"] = "full_time"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workplaceLocation"] = "remote"
            elif "hybrid" in wm:
                params["workplaceLocation"] = "hybrid"
            else:
                params["workplaceLocation"] = "on_site"
        if uf.experience_level:
            el = uf.experience_level.lower()
            if "entry" in el or "junior" in el or "fresher" in el:
                params["seniority"] = "entry_level"
            elif "senior" in el or "lead" in el:
                params["seniority"] = "senior_level"
            else:
                params["seniority"] = "mid_level"
        params["compensationCurrency"] = "USD"
        return params

    @classmethod
    def _build_remote_co(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        return cls._build_remote(uf)

    @classmethod
    def _build_shine(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        slug_role = role.lower().strip().replace(" ", "-")
        params: Dict[str, Any] = {
            "q": slug_role,
            "qActual": role,
            "pure": "1",
            "emp_type": "1" # Permanent / Full Time
        }
        if uf.location:
            params["loc"] = uf.location
            params["location"] = uf.location
        if uf.experience_min is not None:
            params["fexp"] = str(uf.experience_min)
            params["exp"] = str(uf.experience_min)
        if uf.salary_min:
            params["fsalary"] = "2"
            params["salary"] = str(uf.salary_min)
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["posted_date"] = "1"
            elif uf.date_posted_days <= 7:
                params["posted_date"] = "7"
            else:
                params["posted_date"] = "30"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["work_mode"] = "remote"
            elif "hybrid" in wm:
                params["work_mode"] = "hybrid"
            else:
                params["work_mode"] = "wfo"
        return params

    @classmethod
    def _build_simplyhired(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role
        }
        if uf.location:
            params["l"] = uf.location
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["jt"] = "CF3CP"
                params["fjt"] = "parttime"
            elif "contract" in jt:
                params["jt"] = "CF3CP"
                params["fjt"] = "contract"
            else:
                params["jt"] = "CF3CP"
                params["fjt"] = "fulltime"
        if uf.salary_min:
            params["mip"] = str(uf.salary_min)
            params["fmi"] = str(uf.salary_min)
        if uf.date_posted_days:
            days = str(uf.date_posted_days)
            params["t"] = days
            params["fdb"] = days
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["fworkplace"] = "remote"
        return params

    @classmethod
    def _build_timesjobs(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "refreshed": "true"
        }
        if uf.location:
            params["location"] = uf.location
        if uf.experience_min is not None:
            params["experience"] = str(uf.experience_min)
            params["cboWorkExp1"] = uf.experience_min
        if uf.experience_max is not None:
            params["cboWorkExp2"] = uf.experience_max
        if uf.date_posted_days:
            params["postDate"] = uf.date_posted_days
        if uf.work_mode:
            params["workMode"] = uf.work_mode
        return params

    @classmethod
    def _build_wellfound(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "role": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.salary_min:
            params["salary"] = str(uf.salary_min)
        if uf.equity:
            params["equity"] = "true"
        if uf.company_stage:
            params["stage"] = uf.company_stage
        return params

    @classmethod
    def _build_workable(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role
        }
        if uf.location:
            params["location"] = uf.location
        if uf.date_posted_days:
            params["day_range"] = str(uf.date_posted_days)
        else:
            params["day_range"] = "30"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workplace"] = "remote"
            elif "hybrid" in wm:
                params["workplace"] = "hybrid"
            else:
                params["workplace"] = "on_site"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["employment_type"] = "part_time"
            elif "contract" in jt:
                params["employment_type"] = "contract"
            else:
                params["employment_type"] = "full_time"
        if uf.experience_level:
            params["experience"] = "mid_senior_level" if "mid" in uf.experience_level.lower() or "senior" in uf.experience_level.lower() else "entry_level"
        else:
            params["experience"] = "mid_senior_level"
        return params

    @classmethod
    def _build_workatastartup(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "demographic": "any",
            "hasEquity": "any",
            "hasSalary": "any",
            "industry": uf.industry or "any",
            "interviewProcess": "any",
            "jobType": "fulltime" if not uf.job_type or "full" in uf.job_type.lower() else uf.job_type.lower(),
            "layout": "list-compact",
            "query": role,
            "role": "any",
            "sortBy": "keyword",
            "tab": "any",
            "usVisaNotRequired": "any"
        }
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["locations"] = "Remote"
        elif uf.location:
            loc_lower = uf.location.lower().strip()
            if "remote" in loc_lower:
                params["locations"] = "Remote"
            elif loc_lower in ["uk", "gb", "united kingdom", "great britain", "england"]:
                params["locations"] = "GB"
            elif loc_lower in ["india", "in", "ind"]:
                params["locations"] = "IN"
            elif loc_lower in ["us", "usa", "united states", "america"]:
                params["locations"] = "US"
            else:
                params["locations"] = uf.location.strip()
        if uf.experience_min is not None:
            params["minExperience"] = str(uf.experience_min)
        return params

    @classmethod
    def _build_ziprecruiter(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "search": role,
            "location_explicitly_set": "true",
            "radius": str(uf.distance_km or 25)
        }
        if uf.location:
            params["location"] = uf.location
        if uf.date_posted_days:
            params["days"] = str(uf.date_posted_days)
        else:
            params["days"] = "30"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["refine_by_employment"] = "employment_type:part_time"
            elif "contract" in jt:
                params["refine_by_employment"] = "employment_type:contractor"
            else:
                params["refine_by_employment"] = "employment_type:full_time"
        else:
            params["refine_by_employment"] = "employment_type:full_time"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["refine_by_location_type"] = "only_remote"
            else:
                params["refine_by_location_type"] = "no_remote"
        if uf.experience_level:
            el = uf.experience_level.lower()
            if "entry" in el or "junior" in el or "fresher" in el:
                params["refine_by_experience_level"] = "entry_level"
            elif "senior" in el or "lead" in el:
                params["refine_by_experience_level"] = "senior"
            else:
                params["refine_by_experience_level"] = "mid"
        else:
            params["refine_by_experience_level"] = "mid"
        if uf.salary_min:
            params["refine_by_salary"] = str(uf.salary_min)
        return params

    @classmethod
    def _build_jobspresso(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "s": role
        }
        if uf.category:
            params["category"] = uf.category.lower()
        return params

    # -------------------------------------------------------------
    # HIGH-LEVEL WEB URL GENERATOR FOR ALL 26 PORTALS
    # -------------------------------------------------------------

    @classmethod
    def build_portal_url(cls, portal_key: str, uf: UniversalJobFilter) -> str:
        """
        Builds the exact realistic web search URL matching the user's filtered browser URL structure.
        """
        portal_key = portal_key.lower().strip()
        params, _, _ = cls.adapt_for_portal(portal_key, uf)
        role = cls.get_effective_role(uf)
        loc = uf.location or ""
        
        role_slug = re.sub(r'[^a-zA-Z0-9]+', '-', role.strip().lower()).strip('-')
        loc_slug = re.sub(r'[^a-zA-Z0-9]+', '-', loc.strip().lower()).strip('-') if loc else ""

        if portal_key == "adzuna":
            return f"https://www.adzuna.in/search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "apna":
            return f"https://apna.co/jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "builtin":
            work_path = params.get("workplace_path", "")
            subpath = f"/{work_path}" if work_path else ""
            clean_params = {k: v for k, v in params.items() if k != "workplace_path"}
            return f"https://builtin.com/jobs{subpath}?{urllib.parse.urlencode(clean_params)}"
            
        elif portal_key == "careerbuilder":
            return f"https://www.careerbuilder.com/job-listings/search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "careerjet":
            return f"https://www.careerjet.co.in/jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "dice":
            return f"https://www.dice.com/jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "foundit":
            if loc_slug:
                return f"https://www.foundit.in/search/{role_slug}-jobs-in-{loc_slug}?{urllib.parse.urlencode(params)}"
            return f"https://www.foundit.in/search/{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "freshersworld":
            if loc_slug:
                return f"https://www.freshersworld.com/jobs/jobsearch/{role_slug}-jobs-in-{loc_slug}?{urllib.parse.urlencode(params)}"
            return f"https://www.freshersworld.com/jobs/jobsearch/{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "glassdoor":
            if loc_slug:
                return f"https://www.glassdoor.co.in/Job/{loc_slug}-{role_slug}-jobs-SRCH_IL.0,{len(loc_slug)}_KO{len(loc_slug)+1},{len(loc_slug)+1+len(role_slug)}.htm?{urllib.parse.urlencode(params)}"
            return f"https://www.glassdoor.co.in/Job/jobs.htm?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "indeed":
            domain = "in.indeed.com" if "india" in loc.lower() or "bangalore" in loc.lower() or "bengaluru" in loc.lower() else "www.indeed.com"
            return f"https://{domain}/jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "instahyre":
            return f"https://www.instahyre.com/search-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "himalayas":
            country_slug = "india" if "india" in loc.lower() or "bangalore" in loc.lower() or "bengaluru" in loc.lower() else ("united-states" if "us" in loc.lower() else "worldwide")
            emp_type = params.get("employment_type", "full-time")
            return f"https://himalayas.app/jobs/countries/{country_slug}/{emp_type}-{role_slug}?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "jobleads":
            country_code = "in" if "india" in loc.lower() or "bangalore" in loc.lower() or "bengaluru" in loc.lower() else "us"
            encoded_role = urllib.parse.quote(role)
            if loc:
                encoded_loc = urllib.parse.quote(loc)
                return f"https://www.jobleads.com/{country_code}/jobs/l/{encoded_loc}/q/{encoded_role}?{urllib.parse.urlencode(params)}"
            return f"https://www.jobleads.com/{country_code}/jobs/q/{encoded_role}?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "internshala":
            exp_str = f"/experience-{params['experience']}" if "experience" in params else ""
            sal_str = f"/salary-{params['salary']}" if "salary" in params else ""
            if loc_slug:
                return f"https://internshala.com/jobs/{role_slug}-jobs-in-{loc_slug}{exp_str}{sal_str}"
            return f"https://internshala.com/jobs/{role_slug}-jobs{exp_str}{sal_str}"
            
        elif portal_key == "jooble":
            return f"https://in.jooble.org/SearchResult?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "linkedin":
            return f"https://www.linkedin.com/jobs/search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "naukri":
            if loc_slug:
                return f"https://www.naukri.com/{role_slug}-jobs-in-{loc_slug}?{urllib.parse.urlencode(params)}"
            return f"https://www.naukri.com/{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "reed":
            mode_prefix = "on-site-" if params.get("workingOption") == "onSite" else ""
            if loc_slug:
                return f"https://www.reed.co.uk/jobs/{mode_prefix}{role_slug}-jobs-in-{loc_slug}?{urllib.parse.urlencode(params)}"
            return f"https://www.reed.co.uk/jobs/{mode_prefix}{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key in ["remote", "remote_co"]:
            return f"https://remote.com/jobs/all?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "shine":
            return f"https://www.shine.com/job-search/{role_slug}-jobs?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "simplyhired":
            return f"https://www.simplyhired.co.in/search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "timesjobs":
            return f"https://www.timesjobs.com/job-search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "wellfound":
            if loc_slug:
                return f"https://wellfound.com/role/l/{role_slug}/{loc_slug}"
            return f"https://wellfound.com/role/l/{role_slug}"
            
        elif portal_key == "workable":
            return f"https://jobs.workable.com/search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "workatastartup":
            return f"https://www.workatastartup.com/companies?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "ziprecruiter":
            return f"https://www.ziprecruiter.com/jobs-search?{urllib.parse.urlencode(params)}"
            
        elif portal_key == "jobspresso":
            return f"https://jobspresso.co/?{urllib.parse.urlencode(params)}"
            
        return f"https://www.google.com/search?q={urllib.parse.quote(role + ' ' + loc)}"
