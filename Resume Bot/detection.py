# detection.py
import re
import os
from rapidfuzz import fuzz
from logger import logger

# -------------------------------------------------
# FUZZY MATCH
# -------------------------------------------------

def fuzzy_contains(text, keyword, threshold=85):
    if keyword in text:
        return True
    words = text.split()

    for word in words:
        if fuzz.ratio(word, keyword) >= threshold:
            return True

    return False


# -------------------------------------------------
# IDENTITY EXTRACTION
# -------------------------------------------------

EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"(\+?\d[\d\s\-]{8,15}\d)"

PERSONAL_EMAIL_DOMAINS = (
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com"
)


def has_personal_email(text):

    matches = re.findall(EMAIL_REGEX, text)

    if not matches:
        return False

    for email in matches:

        domain = email.split("@")[-1]

        for p_domain in PERSONAL_EMAIL_DOMAINS:
            if fuzz.ratio(domain, p_domain) > 80:
                return True

    return False


def has_phone(text):
    tokens = re.findall(r"\+?\d[\d\s\-]{6,20}", text)
    for t in tokens:
        digits = re.sub(r"\D", "", t)
        if 8 <= len(digits) <= 15:
            return True
    return False


# -------------------------------------------------
# RESUME SCORING
# -------------------------------------------------

RESUME_SECTIONS = [
    "education",
    "experience",
    "skills",
    "projects",
    "internship",
    "certification",
    "summary",
    "objective",
    "profile",
    "technical skills",
    "professional experience",
]


def resume_score(text):

    score = 0

    email_detected = has_personal_email(text)
    phone_detected = has_phone(text)

    logger.info(f"EMAIL DETECTED: {email_detected}")
    logger.info(f"PHONE DETECTED: {phone_detected}")

    if email_detected and phone_detected:
        score += 5

    matched_sections = []

    for section in RESUME_SECTIONS:
        if fuzzy_contains(text, section):
            score += 2
            matched_sections.append(section)

    if matched_sections:
        logger.info(f"Matched resume sections: {matched_sections}")

    return score


# -------------------------------------------------
# JD SCORING
# -------------------------------------------------

JD_STRONG = [
    "job description",
    "vacancy",
    "vacancies",
    "hiring",
    "recruitment",
    "job opening",
    "position available",
    "apply",
    "kindly share",
    "walk in",
    "job role",
    "salary",
    "trainees",
    "accommodation",
    "interested candidates",
    "notice period",
]

JD_MEDIUM = [
    "resumes",
    "looking for",
    "looking out for",
    "required",
    "work location",
    "immediate",
]

JD_WEAK = [
    "responsibilities",
    "requirements",
    "interview",
    "eligibility",
    "candidate",
]


def jd_score(text):

    text = text.lower()
    score = 0
    matched = []

    for kw in JD_STRONG:
        if kw in text:
            score += 5
            matched.append(kw)
        elif fuzz.partial_ratio(kw, text) > 75:
            score += 5
            matched.append(f"~{kw}")

    for kw in JD_MEDIUM:
        if kw in text:
            score += 3
            matched.append(kw)
        elif fuzz.partial_ratio(kw, text) > 75:
            score += 3
            matched.append(f"~{kw}")

    for kw in JD_WEAK:
        if kw in text:
            score += 1
            matched.append(kw)
        elif fuzz.partial_ratio(kw, text) > 75:
            score += 1
            matched.append(f"~{kw}")

    if matched:
        logger.info(f"Matched JD keywords: {matched}")

    return score

# -------------------------------------------------
# MAIN CLASSIFIER
# -------------------------------------------------

def is_resume_content(text):

    r_score = resume_score(text)
    j_score = jd_score(text)

    # [LOGGER ADDED]
    logger.info(f"ResumeScore={r_score} JDScore={j_score}")

    if j_score - r_score > 2:
        logger.info("CLASSIFICATION → JOB DESCRIPTION")
        return False

    if r_score < 4:
        logger.info("CLASSIFICATION → NOT RESUME (low score)")
        return False

    logger.info("CLASSIFICATION → RESUME")
    return True


# -------------------------------------------------
# JD FILENAME
# -------------------------------------------------

def is_jd_filename(filename: str) -> bool:

    name = os.path.splitext(filename)[0].lower()

    normalized = re.sub(r"[^a-z0-9]+", " ", name)

    jd_keywords = (
        "jd",
        "job",
        "job_description",
        "job_desc",
        "hiring",
        "vacancy",
        "opening",
        "recruitment",
        "advertisement",
        "notification",
    )

    return any(k in normalized for k in jd_keywords)