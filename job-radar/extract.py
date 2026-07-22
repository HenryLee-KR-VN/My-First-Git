"""공고 본문/텍스트에서 기술스택·업종·경력·인력유형을 추출하는 유틸리티."""
import re

from config import (
    CAREER_LEVEL_ANY,
    CAREER_LEVEL_EXPERIENCED,
    CAREER_LEVEL_NEW,
    DEFAULT_EMPLOYMENT_TYPE,
    DEFAULT_INDUSTRY,
    EMPLOYMENT_TYPE_MAP,
    INDUSTRY_KEYWORDS,
    TECH_STACK_KEYWORDS,
)


def extract_tech_stack(*texts: str) -> str:
    """여러 텍스트(제목+본문 등)에서 기술스택 키워드를 찾아 콤마로 join한 문자열 반환."""
    haystack = " ".join(t for t in texts if t).lower()
    found = []
    for canonical, aliases in TECH_STACK_KEYWORDS.items():
        for alias in aliases:
            pattern = r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])"
            if re.search(pattern, haystack):
                found.append(canonical)
                break
    return ",".join(found)


def classify_industry(*texts: str) -> str:
    haystack = " ".join(t for t in texts if t).lower()
    for domain, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in haystack:
                return domain
    return DEFAULT_INDUSTRY


def normalize_employment_type(text: str) -> str:
    if not text:
        return DEFAULT_EMPLOYMENT_TYPE
    for key, value in EMPLOYMENT_TYPE_MAP.items():
        if key in text:
            return value
    return DEFAULT_EMPLOYMENT_TYPE


def normalize_career_level(text: str) -> str:
    if not text:
        return CAREER_LEVEL_ANY
    t = text.replace(" ", "")
    if "신입" in t and "경력" in t:
        return CAREER_LEVEL_ANY
    if "무관" in t:
        return CAREER_LEVEL_ANY
    if "신입" in t:
        return CAREER_LEVEL_NEW
    if "경력" in t:
        return CAREER_LEVEL_EXPERIENCED
    return CAREER_LEVEL_ANY
