"""
Universal Job Filter Engine
===========================
Defines the universal filter schema and maps user input queries to portal-specific 
URL query parameters and API payloads across all 26 supported job portals.

Dynamically:
- Evaluates which filters are supported per portal.
- Adapts and formats supported filters to exact portal specs.
- Safely omits unsupported filters per portal to prevent query corruption.
- Provides transparent logging of applied vs. omitted filters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse

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


# Capability registry mapping portal names to supported filter attributes
PORTAL_CAPABILITY_MATRIX: Dict[str, List[str]] = {
    "foundit": [
        "keywords", "job_title", "skills", "company", "location", "experience_min", "experience_max",
        "salary_min", "salary_max", "industry", "department", "company_type", "date_posted_days",
        "top_employers", "employer_type", "job_type", "walk_in_date", "international_jobs", "sort_by", "work_mode"
    ],
    "apna": [
        "keywords", "location", "date_posted_days", "salary_min", "work_mode", "job_type",
        "work_shift", "department", "sort_by", "experience_min"
    ],
    "instahyre": [
        "keywords", "job_title", "location", "experience_min", "experience_max", "salary_min",
        "job_type", "work_mode", "skills", "company", "industry", "date_posted_days", "education", "sort_by", "company_type"
    ],
    "internshala": [
        "keywords", "location", "work_mode", "job_type", "category", "stipend_min",
        "experience_min", "skills", "duration_months", "date_posted_days", "company", "sort_by"
    ],
    "shine": [
        "keywords", "job_title", "location", "experience_min", "salary_min", "industry",
        "department", "job_type", "work_mode", "education", "skills", "company", "date_posted_days", "sort_by"
    ],
    "adzuna": [
        "keywords", "location", "salary_min", "salary_max", "date_posted_days", "job_type",
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
        "work_mode", "job_type", "distance_km", "experience_level", "sort_by"
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
        "keywords", "job_title", "location", "experience_min", "salary_min", "job_type",
        "work_mode", "date_posted_days", "education", "industry", "department", "company", "skills"
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
        "keywords", "location", "salary_min", "salary_max", "job_type", "work_mode",
        "employer_type", "date_posted_days", "specialism", "hide_no_salary", "distance_km"
    ],
    "glassdoor": [
        "keywords", "job_title", "location", "date_posted_days", "job_type", "experience_level",
        "work_mode", "salary_min", "company", "industry", "easy_apply", "distance_km"
    ],
    "himalayas": [
        "keywords", "location", "worldwide", "experience_level", "job_type", "salary_min",
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
    "remote_co": [
        "keywords", "category", "location", "job_type", "experience_level", "skills",
        "company", "date_posted_days", "work_mode"
    ],
    "wellfound": [
        "keywords", "job_title", "location", "salary_min", "equity", "job_type",
        "experience_level", "work_mode", "company_stage", "company_size", "industry"
    ],
    "workable": [
        "keywords", "job_title", "location", "department", "job_type", "work_mode",
        "company", "experience_level"
    ],
    "ziprecruiter": [
        "keywords", "location", "date_posted_days", "distance_km", "job_type", "salary_min",
        "experience_level", "work_mode", "company"
    ],
    "jobspresso": [
        "keywords", "location", "category", "skills"
    ]
}


class FilterEngine:
    """
    Translates UniversalJobFilter instances into portal-specific URL parameters and API payloads.
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
        return " ".join(terms) if terms else "Software Engineer"

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
    # PORTAL-SPECIFIC ADAPTERS
    # -------------------------------------------------------------

    @classmethod
    def _build_foundit(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role,
            "locations": uf.location or ""
        }
        if uf.skills:
            params["skills"] = uf.skills
        if uf.company:
            params["company"] = uf.company
        if uf.experience_min is not None or uf.experience_max is not None:
            emin = uf.experience_min or 0
            emax = uf.experience_max or 30
            params["experienceRanges"] = f"{emin}~{emax}"
        if uf.salary_min or uf.salary_max:
            smin = uf.salary_min or 0
            smax = uf.salary_max or 10000000
            params["salaryRanges"] = f"{smin}~{smax}"
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["postedDate"] = "1"
            elif uf.date_posted_days <= 7:
                params["postedDate"] = "7"
            elif uf.date_posted_days <= 15:
                params["postedDate"] = "15"
            else:
                params["postedDate"] = "30"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workMode"] = "remote"
            elif "hybrid" in wm:
                params["workMode"] = "hybrid"
            elif "wfo" in wm or "office" in wm:
                params["workMode"] = "wfo"
        if uf.job_type:
            params["jobTypes"] = "permanent" if "full" in uf.job_type or "perm" in uf.job_type else "contract"
        if uf.industry:
            params["industries"] = uf.industry
        if uf.department:
            params["functions"] = uf.department
        if uf.company_type:
            params["companyTypes"] = uf.company_type
        if uf.employer_type:
            params["employerTypes"] = uf.employer_type
        if uf.sort_by:
            params["sort"] = "2" if "date" in uf.sort_by.lower() or "recent" in uf.sort_by.lower() else "1"
        return params

    @classmethod
    def _build_apna(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "text": role,
            "location": uf.location or "Bengaluru"
        }
        if uf.work_mode:
            if "remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower():
                params["workLocationType"] = "WORK_FROM_HOME"
            elif "office" in uf.work_mode.lower() or "wfo" in uf.work_mode.lower():
                params["workLocationType"] = "WORK_FROM_OFFICE"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["workType"] = "PART_TIME"
            elif "intern" in jt:
                params["workType"] = "INTERNSHIP"
            else:
                params["workType"] = "FULL_TIME"
        if uf.work_shift:
            params["workShift"] = "NIGHT_SHIFT" if "night" in uf.work_shift.lower() else "DAY_SHIFT"
        if uf.salary_min:
            params["minSalary"] = uf.salary_min
        if uf.experience_min is not None:
            if uf.experience_min == 0:
                params["experience"] = "FRESHER"
            elif uf.experience_min <= 3:
                params["experience"] = "1-3"
            elif uf.experience_min <= 5:
                params["experience"] = "3-5"
            else:
                params["experience"] = "5+"
        if uf.department:
            params["department"] = uf.department
        if uf.sort_by:
            params["sort"] = "RECENT" if "date" in uf.sort_by.lower() or "recent" in uf.sort_by.lower() else "RELEVANCE"
        return params

    @classmethod
    def _build_instahyre(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "skills": uf.skills or role,
            "locations": uf.location or ""
        }
        if uf.experience_min is not None:
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
            elif "contract" in jt:
                params["job_type"] = "1"
            else:
                params["job_type"] = "0"
        if uf.company_type:
            params["company_type"] = uf.company_type
        if uf.work_mode:
            params["work_mode"] = "remote" if "remote" in uf.work_mode.lower() else "office"
        if uf.education:
            params["education"] = uf.education
        return params

    @classmethod
    def _build_internshala(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "role": role,
            "location": uf.location or ""
        }
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["work_from_home"] = "true"
        if uf.job_type and "part" in uf.job_type.lower():
            params["part_time"] = "true"
        if uf.salary_min:
            params["annual_salary"] = uf.salary_min
        if uf.stipend_min:
            params["stipend"] = uf.stipend_min
        if uf.experience_min:
            params["experience"] = uf.experience_min
        if uf.duration_months:
            params["duration"] = uf.duration_months
        if uf.category:
            params["category"] = uf.category
        return params

    @classmethod
    def _build_shine(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "loc": uf.location or ""
        }
        if uf.experience_min is not None:
            params["exp"] = str(uf.experience_min)
        if uf.salary_min:
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
        if uf.department:
            params["functional_area"] = uf.department
        if uf.industry:
            params["industry"] = uf.industry
        if uf.sort_by:
            params["sort"] = "2" if "date" in uf.sort_by.lower() else "1"
        return params

    @classmethod
    def _build_adzuna(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "w": uf.location or ""
        }
        if uf.distance_km:
            params["distance"] = uf.distance_km
        if uf.salary_min:
            params["salary_min"] = uf.salary_min
        if uf.salary_max:
            params["salary_max"] = uf.salary_max
        if uf.job_type:
            jt = uf.job_type.lower()
            if "contract" in jt or "temp" in jt:
                params["contract_type"] = "contract"
            elif "perm" in jt or "full" in jt:
                params["contract_type"] = "permanent"
            if "part" in jt:
                params["working_hours"] = "part_time"
            elif "full" in jt:
                params["working_hours"] = "full_time"
        if uf.sort_by:
            params["sort_by"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_builtin(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "search": role,
            "location": uf.location or ""
        }
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["remote"] = "1"
            elif "hybrid" in wm:
                params["remote"] = "2"
            else:
                params["remote"] = "3"
        if uf.experience_level:
            params["experience"] = uf.experience_level.lower()
        if uf.date_posted_days:
            params["days_since_updated"] = str(uf.date_posted_days)
        if uf.category:
            params["category"] = uf.category
        if uf.company_size:
            params["company_size"] = uf.company_size
        return params

    @classmethod
    def _build_careerjet(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "s": role,
            "l": uf.location or ""
        }
        if uf.distance_km:
            params["radius"] = uf.distance_km
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["f"] = "parttime"
            elif "contract" in jt or "temp" in jt:
                params["f"] = "contract"
            else:
                params["f"] = "fulltime"
        if uf.sort_by:
            params["sort"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_dice(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "location": uf.location or ""
        }
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workplaceTypes"] = "Remote"
            elif "hybrid" in wm:
                params["workplaceTypes"] = "Hybrid"
            else:
                params["workplaceTypes"] = "On-Site"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "contract" in jt:
                params["employmentType"] = "CONTRACTS"
            elif "third" in jt:
                params["employmentType"] = "THIRD_PARTY"
            elif "part" in jt:
                params["employmentType"] = "PARTTIME"
            else:
                params["employmentType"] = "FULLTIME"
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["postedDate"] = "ONE"
            elif uf.date_posted_days <= 7:
                params["postedDate"] = "SEVEN"
            elif uf.date_posted_days <= 14:
                params["postedDate"] = "FOURTEEN"
            else:
                params["postedDate"] = "THIRTY"
        if uf.experience_level:
            el = uf.experience_level.lower()
            if "entry" in el or "fresher" in el or "junior" in el:
                params["experienceLevel"] = "ENTRY_LEVEL"
            elif "mid" in el:
                params["experienceLevel"] = "MID_LEVEL"
            elif "senior" in el or "lead" in el or "exec" in el:
                params["experienceLevel"] = "SENIOR_LEVEL"
        if uf.easy_apply:
            params["easyApply"] = "true"
        return params

    @classmethod
    def _build_simplyhired(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "l": uf.location or ""
        }
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["fdb"] = "1"
            elif uf.date_posted_days <= 7:
                params["fdb"] = "7"
            elif uf.date_posted_days <= 14:
                params["fdb"] = "14"
            else:
                params["fdb"] = "30"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["fjt"] = "parttime"
            elif "contract" in jt:
                params["fjt"] = "contract"
            elif "intern" in jt:
                params["fjt"] = "internship"
            else:
                params["fjt"] = "fulltime"
        if uf.salary_min:
            params["fmi"] = str(uf.salary_min)
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["fworkplace"] = "remote"
        return params

    @classmethod
    def _build_timesjobs(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "location": uf.location or ""
        }
        if uf.experience_min is not None:
            params["cboWorkExp1"] = uf.experience_min
        if uf.experience_max is not None:
            params["cboWorkExp2"] = uf.experience_max
        if uf.date_posted_days:
            params["postDate"] = uf.date_posted_days
        if uf.work_mode:
            params["workMode"] = uf.work_mode
        if uf.department:
            params["function"] = uf.department
        if uf.industry:
            params["industry"] = uf.industry
        return params

    @classmethod
    def _build_freshersworld(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "city": uf.location or ""
        }
        if uf.education:
            params["course"] = uf.education
        if uf.job_type:
            params["jobtype"] = "internship" if "intern" in uf.job_type.lower() else "fulltime"
        return params

    @classmethod
    def _build_linkedin(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "location": uf.location or ""
        }
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["f_TPR"] = "r86400"
            elif uf.date_posted_days <= 7:
                params["f_TPR"] = "r604800"
            elif uf.date_posted_days <= 30:
                params["f_TPR"] = "r2592000"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["f_WT"] = "2"
            elif "hybrid" in wm:
                params["f_WT"] = "3"
            elif "wfo" in wm or "office" in wm:
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
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "location": uf.location or ""
        }
        if uf.experience_min is not None:
            params["experience"] = str(uf.experience_min)
        if uf.salary_min:
            params["salaryRange"] = f"{uf.salary_min}to{uf.salary_max or ''}"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["wfhType"] = "2"
            elif "hybrid" in wm:
                params["wfhType"] = "3"
            else:
                params["wfhType"] = "0"
        if uf.date_posted_days:
            params["jobAge"] = str(uf.date_posted_days)
        return params

    @classmethod
    def _build_reed(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "keywords": role,
            "location": uf.location or ""
        }
        if uf.salary_min:
            params["salarymin"] = str(uf.salary_min)
        if uf.salary_max:
            params["salarymax"] = str(uf.salary_max)
        if uf.hide_no_salary:
            params["hidesalaryjobs"] = "true"
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workfromhome"] = "true"
            elif "hybrid" in wm:
                params["hybrid"] = "true"
        if uf.job_type:
            jt = uf.job_type.lower()
            if "part" in jt:
                params["parttime"] = "true"
            elif "contract" in jt:
                params["contract"] = "true"
            elif "temp" in jt:
                params["temp"] = "true"
            elif "perm" in jt:
                params["permanent"] = "true"
            else:
                params["fulltime"] = "true"
        if uf.distance_km:
            params["distance"] = str(uf.distance_km)
        if uf.date_posted_days:
            if uf.date_posted_days <= 1:
                params["datecreatedoffset"] = "Today"
            elif uf.date_posted_days <= 3:
                params["datecreatedoffset"] = "LastThreeDays"
            elif uf.date_posted_days <= 7:
                params["datecreatedoffset"] = "LastWeek"
            else:
                params["datecreatedoffset"] = "LastTwoWeeks"
        return params

    @classmethod
    def _build_himalayas(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "country": uf.location or ""
        }
        if uf.experience_level:
            params["experience_level"] = uf.experience_level.lower()
        if uf.job_type:
            params["employment_type"] = uf.job_type.lower()
        if uf.salary_min:
            params["min_salary"] = uf.salary_min
        if uf.skills:
            params["skills"] = uf.skills
        if uf.timezone:
            params["timezone"] = uf.timezone
        if uf.sort_by:
            params["sort"] = "recent" if "date" in uf.sort_by.lower() else "featured"
        return params

    @classmethod
    def _build_workable(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role,
            "location": uf.location or ""
        }
        if uf.work_mode:
            wm = uf.work_mode.lower()
            if "remote" in wm or "wfh" in wm:
                params["workplace"] = "remote"
            elif "hybrid" in wm:
                params["workplace"] = "hybrid"
            else:
                params["workplace"] = "on_site"
        if uf.job_type:
            params["employment_type"] = uf.job_type.lower()
        if uf.department:
            params["department"] = uf.department
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

    @classmethod
    def _build_indeed(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "l": uf.location or ""
        }
        if uf.date_posted_days:
            params["fromage"] = str(uf.date_posted_days)
        if uf.job_type:
            params["jt"] = uf.job_type.lower()
        if uf.distance_km:
            params["radius"] = str(int(uf.distance_km * 0.621371))
        if uf.sort_by:
            params["sort"] = "date" if "date" in uf.sort_by.lower() else "relevance"
        return params

    @classmethod
    def _build_glassdoor(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "sc.keyword": role,
            "location": uf.location or ""
        }
        if uf.date_posted_days:
            params["fromAge"] = str(uf.date_posted_days)
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
    def _build_ziprecruiter(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "search": role,
            "location": uf.location or ""
        }
        if uf.date_posted_days:
            params["days"] = str(uf.date_posted_days)
        if uf.salary_min:
            params["refine_by_salary"] = str(uf.salary_min)
        if uf.distance_km:
            params["radius"] = str(int(uf.distance_km * 0.621371))
        return params

    @classmethod
    def _build_jooble(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "role": role,
            "location": uf.location or ""
        }
        if uf.salary_min:
            params["salary"] = str(uf.salary_min)
        if uf.date_posted_days:
            params["date"] = str(uf.date_posted_days)
        if uf.distance_km:
            params["rg"] = str(uf.distance_km)
        if uf.work_mode and ("remote" in uf.work_mode.lower() or "wfh" in uf.work_mode.lower()):
            params["telework"] = "1"
        return params

    @classmethod
    def _build_careerbuilder(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "where": uf.location or ""
        }
        if uf.date_posted_days:
            params["posted"] = str(uf.date_posted_days)
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
    def _build_jobleads(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "q": role,
            "location": uf.location or ""
        }
        if uf.work_mode:
            params["workSetting"] = uf.work_mode.lower()
        if uf.salary_min:
            params["salary"] = str(uf.salary_min)
        if uf.date_posted_days:
            params["posted"] = str(uf.date_posted_days)
        return params

    @classmethod
    def _build_remote_co(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "query": role,
            "location": uf.location or ""
        }
        if uf.category:
            params["category"] = uf.category.lower()
        if uf.job_type:
            params["job_type"] = uf.job_type.lower()
        return params

    @classmethod
    def _build_wellfound(cls, uf: UniversalJobFilter) -> Dict[str, Any]:
        role = cls.get_effective_role(uf)
        params: Dict[str, Any] = {
            "role": role,
            "location": uf.location or ""
        }
        if uf.salary_min:
            params["salary"] = str(uf.salary_min)
        if uf.equity:
            params["equity"] = "true"
        if uf.company_stage:
            params["stage"] = uf.company_stage
        return params
