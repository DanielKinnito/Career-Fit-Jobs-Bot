"""High-precision multi-signal job vacancy classifier for Telegram channel posts."""

import re
from typing import Tuple, List

# Minimum character length for legitimate vacancy announcements
MIN_VACANCY_LENGTH = 70

# ------------------------------------------------------------------------------
# 1. DISQUALIFYING (NEGATIVE) SIGNALS
# Posts containing these patterns are filtered out as non-job noise
# ------------------------------------------------------------------------------

DISQUALIFYING_PATTERNS = [
    # Charity, donations, medical aid, crowdfunding
    r"\b(donate|donation|donations|fundrais\w*|gofundme|charity|fund\s*raising)\b",
    r"\b(help\s+a\s+(brother|sister|family|child|patient))\b",
    r"\b(medical\s+(assistance|treatment|bill|funds|expenses))\b",
    r"\b(kidney\s+transplant|cancer\s+treatment|urgent\s+medical)\b",
    r"(እርዳታ|ለህክምና|የህክምና\s*እርዳታ|የገንዘብ\s*ድጋፍ|የህክምና\s*ወጪ)",

    # CV / Resume Writing & Redesign Services
    r"\b(cv\s+writing\s+service|resume\s+writing\s+service|cv\s+revamp)\b",
    r"\b(professional\s+cv\s+redesign|standard\s+cv\s+for\s+only)\b",
    r"\b(ats[- ]friendly\s+cv\s+for\s+only|cover\s+letter\s+writing\s+service)\b",
    r"\b(let\s+us\s+redesign\s+your\s+cv|order\s+your\s+cv|we\s+make\s+standard\s+cv)\b",

    # Training, Courses, Bootcamps, Masterclasses (selling training, not hiring)
    r"\b(masterclass|bootcamp|training\s+(program|session|course|fee|batch))\b",
    r"\b(registration\s+fee|admission\s+fee|course\s+fee|tuition\s+fee)\b",
    r"\b(enroll\s+now|limited\s+seats\s+available|batch\s+registration)\b",
    r"\b(learn\s+\w+\s+in\s+\d+\s+(weeks|months|days))\b",
    r"(ስልጠና|የስልጠና\s*ማስታወቂያ|የምዝገባ\s*ክፍያ)",

    # Job Seekers Advertising Themselves ("I am looking for a job")
    r"\b(i\s+am\s+looking\s+for\s+a\s+job|looking\s+for\s+a\s+part[- ]time\s+job)\b",
    r"\b(i\s+need\s+a\s+job|hire\s+me|looking\s+for\s+any\s+(opening|work))\b",
    r"\b(fresh\s+graduate\s+looking\s+for\s+a?\s*job)\b",
    r"(ስራ\s*ፈላጊ\s*ነኝ)",

    # Crypto / Forex / Ponzi / Earning Scams
    r"\b(earn\s+\d+\s*(etb|birr|usd|dollars)?\s*daily\s+from\s+home)\b",
    r"\b(trading\s+signals|forex\s+trading|crypto\s+investment|binary\s+options)\b",
    r"\b(airdrop|usdt\s+giveaway|guaranteed\s+passive\s+income)\b",
    r"\b(vip\s+signals|betting\s+tips|fixed\s+matches)\b",

    # Real estate / Product sales
    r"\b(house\s+for\s+rent|apartment\s+for\s+rent|condo\s+for\s+rent)\b",
    r"\b(office\s+space\s+for\s+rent|car\s+for\s+sale|brand\s+new\s+\w+\s+for\s+sale)\b",
    r"(ቤት\s*ኪራይ|የሚሸጥ\s*መኪና)",

    # Channel cross-promos & social follow spam
    r"\b(cross\s*promotion|paid\s*promo|subscribe\s+to\s+our\s+channel)\b",
    r"\b(follow\s+us\s+on\s+tiktok|follow\s+our\s+instagram)\b",
]

# ------------------------------------------------------------------------------
# 2. POSITIVE VACANCY SIGNALS (DIMENSIONS)
# ------------------------------------------------------------------------------

# Dimension A: Position & Hiring Identity
HEADER_SIGNALS = [
    r"\b(job\s+title|position|job\s+position|vacancy|job\s+vacancy|job\s+opening)\b",
    r"\b(we\s+are\s+hiring|hiring|role|position\s+title|job\s+description)\b",
    r"\b(urgent\s+vacancy|employment\s+opportunity|career\s+opportunity)\b",
    r"(ክፍት\s*የስራ\s*ቦታ|የስራ\s*መደብ|የስራ\s*አይነት)",
]

# Dimension B: Requirements & Qualifications
REQUIREMENT_SIGNALS = [
    r"\b(requirements?|qualifications?|education|experience|responsibilities)\b",
    r"\b(bachelor|degree|diploma|masters?|bsc|ba|msc)\b",
    r"\b(\d+\+?\s*years?\s+(of\s+)?experience|proven\s+experience)\b",
    r"\b(skills?\s+required|job\s+requirements?)\b",
    r"(መስፈርት|የትምህርት\s*ደረጃ|የስራ\s*ልምድ)",
]

# Dimension C: Application Methods & Deadlines
APPLICATION_SIGNALS = [
    r"\b(how\s+to\s+apply|send\s+your\s+cv|send\s+your\s+resume|submit\s+your\s+cv)\b",
    r"\b(apply\s+via|application\s+deadline|deadline|apply\s+before|apply\s+now)\b",
    r"\b(interested\s+applicants|send\s+(your\s+)?application|email\s+your\s+cv)\b",
    r"\b(apply\s+here|application\s+link|submit\s+resume)\b",
    r"(ማመልከት\s*የምትፈልጉ|የማመልከቻ\s*ጊዜ|ማመልከቻ)",
]

# Dimension D: Compensation & Contract Terms
TERM_SIGNALS = [
    r"\b(salary|remuneration|employment\s+type|full[- ]time|part[- ]time)\b",
    r"\b(contract|permanent|internship|negotiable|attractive\s+salary)\b",
    r"(ደመወዝ|የቅጥር\s*ሁኔታ)",
]

# ------------------------------------------------------------------------------
# 3. WORK MODALITY SIGNALS (Remote / Hybrid / On-site)
# ------------------------------------------------------------------------------

REMOTE_PATTERNS = [
    r"\b(remote|work\s+from\s+home|wfh|100%\s+remote|fully\s+remote|work\s+anywhere|telecommute)\b",
    r"(የቤት\s*ውስጥ\s*ስራ|የርቀት\s*ስራ)",
]

HYBRID_PATTERNS = [
    r"\b(hybrid|partially\s+remote|days\s+(in|at)\s+office|hybrid\s+work|hybrid\s+role)\b",
]

ONSITE_PATTERNS = [
    r"\b(on[- ]site|in[- ]person|office[- ]based|at\s+our\s+office)\b",
    r"\b(addis\s+ababa|hawassa|dire\s+dawa|adama|bahir\s+dar|mekelle|bole|located\s+in)\b",
    r"(በአካል)",
]


def extract_work_type(text: str) -> str:
    """Classify work modality into 'Remote', 'Hybrid', 'On-site', or 'Unspecified'."""
    if not text:
        return "Unspecified"

    text_lower = text.lower()

    # Check Remote
    if any(re.search(pat, text_lower) for pat in REMOTE_PATTERNS):
        return "Remote"

    # Check Hybrid
    if any(re.search(pat, text_lower) for pat in HYBRID_PATTERNS):
        return "Hybrid"

    # Check On-site
    if any(re.search(pat, text_lower) for pat in ONSITE_PATTERNS):
        return "On-site"

    return "Unspecified"


def classify_job_post(text: str) -> Tuple[bool, str, List[str]]:
    """
    Classify a post with multi-signal precision.
    Returns (is_job: bool, work_type: str, reasons: List[str]).
    """
    if not text:
        return False, "Unspecified", ["Empty text"]

    cleaned_text = text.strip()
    if len(cleaned_text) < MIN_VACANCY_LENGTH:
        return False, "Unspecified", [f"Too short ({len(cleaned_text)} chars < {MIN_VACANCY_LENGTH})"]

    text_lower = cleaned_text.lower()
    reasons = []

    # 1. Check Disqualifying Signals
    for pat in DISQUALIFYING_PATTERNS:
        match = re.search(pat, text_lower)
        if match:
            reasons.append(f"Disqualified by negative pattern: '{match.group(0)}'")
            return False, "Unspecified", reasons

    # 2. Check Dimensions
    has_header = any(re.search(pat, text_lower) for pat in HEADER_SIGNALS)
    has_requirements = any(re.search(pat, text_lower) for pat in REQUIREMENT_SIGNALS)
    has_application = any(re.search(pat, text_lower) for pat in APPLICATION_SIGNALS)
    has_terms = any(re.search(pat, text_lower) for pat in TERM_SIGNALS)

    matched_dimensions = []
    if has_header:
        matched_dimensions.append("Header/Title")
    if has_requirements:
        matched_dimensions.append("Requirements/Qualifications")
    if has_application:
        matched_dimensions.append("Application/Deadline")
    if has_terms:
        matched_dimensions.append("Terms/Salary")

    work_type = extract_work_type(text)

    # 3. Certification Rules:
    # Rule A: Strong Header + Application method
    if has_header and has_application:
        reasons.append(f"Certified: Header + Application signals matched ({', '.join(matched_dimensions)})")
        return True, work_type, reasons

    # Rule B: Strong Header + Requirements
    if has_header and has_requirements:
        reasons.append(f"Certified: Header + Requirements signals matched ({', '.join(matched_dimensions)})")
        return True, work_type, reasons

    # Rule C: At least 3 distinct vacancy dimensions
    if len(matched_dimensions) >= 3:
        reasons.append(f"Certified: {len(matched_dimensions)} vacancy dimensions matched ({', '.join(matched_dimensions)})")
        return True, work_type, reasons

    reasons.append(f"Insufficient vacancy signals (matched only: {', '.join(matched_dimensions) if matched_dimensions else 'none'})")
    return False, work_type, reasons


def is_certified_job_post(text: str) -> bool:
    """Convenience wrapper returning boolean acceptance for the scraper runner."""
    is_job, _, _ = classify_job_post(text)
    return is_job
