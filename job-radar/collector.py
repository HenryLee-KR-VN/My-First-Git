#!/usr/bin/env python3
"""job-radar 채용공고 수집기.

대상: 사람인(오픈 API), 잡코리아(requests + BeautifulSoup, robots.txt 준수)
사용법:
    python collector.py                    # 전체 소스 수집
    python collector.py --sources saramin  # 사람인만
    python collector.py --keywords "백엔드,DevOps"

환경변수:
    SARAMIN_ACCESS_KEY   사람인 오픈 API access-key (필수, 없으면 사람인 수집은 건너뜀)

주의: 사람인 API의 정확한 파라미터/응답 필드명은 개발 환경의 네트워크 제약으로
현재 라이브 확인이 불가능했다. 아래 구현은 공개적으로 알려진 사람인 Open API
(oapi.saramin.co.kr/job-search) 스펙을 기반으로 하되, 여러 후보 태그명을 모두
시도하는 방어적 파싱을 사용한다. 실제 access-key 발급 후 1회 테스트 실행하여
_parse_job()의 필드 매핑이 맞는지 확인/보정할 것 (README 참고).
"""
import argparse
import logging
import os
import random
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config import (
    DEFAULT_EMPLOYMENT_TYPE,
    LOG_DIR,
    REQUEST_DELAY_MAX_SEC,
    REQUEST_DELAY_MIN_SEC,
    SEARCH_KEYWORDS,
    SOURCE_JOBKOREA,
    SOURCE_SARAMIN,
    USER_AGENT,
)
from db import get_conn, init_db, upsert_job
from extract import (
    classify_industry,
    extract_tech_stack,
    normalize_career_level,
    normalize_employment_type,
)

os.makedirs(LOG_DIR, exist_ok=True)
_log_file = os.path.join(LOG_DIR, f"collector_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(_log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("collector")


def _polite_sleep():
    time.sleep(random.uniform(REQUEST_DELAY_MIN_SEC, REQUEST_DELAY_MAX_SEC))


def _first_text(elem, *paths):
    """elem에서 여러 후보 xpath 중 처음으로 값이 있는 텍스트를 반환."""
    for path in paths:
        found = elem.find(path)
        if found is not None and found.text and found.text.strip():
            return found.text.strip()
    return None


def _first_attr(elem, path, attr, default=None):
    found = elem.find(path)
    if found is not None and found.get(attr):
        return found.get(attr)
    return default


class SaraminCollector:
    """사람인 오픈 API(oapi.saramin.co.kr) 클라이언트."""

    BASE_URL = "https://oapi.saramin.co.kr/job-search"
    PAGE_SIZE = 110  # API 최대 허용 건수
    MAX_PAGES_PER_KEYWORD = 3  # 일일 500회 호출 제한을 고려한 안전장치

    def __init__(self, access_key: str | None):
        self.access_key = access_key
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def collect(self, keywords) -> list[dict]:
        if not self.access_key:
            log.warning("SARAMIN_ACCESS_KEY가 설정되지 않아 사람인 수집을 건너뜁니다.")
            log.warning("발급 절차: https://oapi.saramin.co.kr/join 에서 이용신청 -> 승인 메일 -> "
                        "로그인 후 [Application]>[앱 등록] -> access-key 발급 (1일 500회 호출 제한).")
            return []

        all_jobs = []
        for keyword in keywords:
            try:
                jobs = self._search_keyword(keyword)
                log.info("[사람인] '%s' 키워드로 %d건 수집", keyword, len(jobs))
                all_jobs.extend(jobs)
            except Exception:
                log.exception("[사람인] '%s' 키워드 수집 실패", keyword)
            _polite_sleep()
        return all_jobs

    def _search_keyword(self, keyword: str) -> list[dict]:
        jobs = []
        start = 0
        for _ in range(self.MAX_PAGES_PER_KEYWORD):
            params = {
                "access-key": self.access_key,
                "keyword": keyword,
                "fields": "count,industry,job-category,job-type,position,salary,"
                          "experience-level,education-level,deadline-date,posting-date,"
                          "expiration-date,working-location,keyword",
                "count": self.PAGE_SIZE,
                "start": start,
            }
            resp = self.session.get(self.BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)

            job_elems = root.findall(".//job")
            if not job_elems:
                break

            for job_el in job_elems:
                parsed = self._parse_job(job_el, keyword)
                if parsed:
                    jobs.append(parsed)

            total = _first_attr(root, ".", "total", None) or root.findtext(".//total")
            try:
                total = int(total) if total else len(job_elems)
            except ValueError:
                total = len(job_elems)

            start += self.PAGE_SIZE
            if start >= total or len(job_elems) < self.PAGE_SIZE:
                break
            _polite_sleep()
        return jobs

    def _parse_job(self, job_el, keyword: str) -> dict | None:
        try:
            url = _first_text(job_el, "url")
            company_name = _first_text(
                job_el, "company/detail/name", "company/name",
            )
            title = _first_text(job_el, "position/title", "position/job-title")
            if not (url and company_name and title):
                return None

            industry_name = _first_attr(job_el, "position/industry", "name") or \
                _first_text(job_el, "position/industry")
            job_type_name = _first_attr(job_el, "position/job-type", "name") or \
                _first_text(job_el, "position/job-type")
            location_name = _first_attr(job_el, "position/location", "name") or \
                _first_text(job_el, "position/location")
            experience_name = _first_attr(job_el, "position/experience-level", "name") or \
                _first_text(job_el, "position/experience-level")
            keyword_field = _first_text(job_el, "keyword") or ""
            posted_date = _first_text(job_el, "posting-date", "posting-timestamp")
            deadline = _first_text(job_el, "expiration-date", "expiration-timestamp", "deadline-date")

            tech_stack = extract_tech_stack(title, keyword_field)
            industry = classify_industry(industry_name or "", company_name)

            return {
                "source": SOURCE_SARAMIN,
                "company_name": company_name,
                "company_domain": industry,
                "job_title": title,
                "employment_type": normalize_employment_type(job_type_name) if job_type_name else DEFAULT_EMPLOYMENT_TYPE,
                "tech_stack": tech_stack,
                "career_level": normalize_career_level(experience_name),
                "location": location_name,
                "url": url,
                "posted_date": posted_date,
                "deadline": deadline,
                "matched_keyword": keyword,
            }
        except Exception:
            log.exception("[사람인] 공고 파싱 실패, 건너뜀")
            return None


class JobkoreaCollector:
    """잡코리아 - 공식 API 없음. robots.txt 확인 후 requests+BeautifulSoup으로 수집."""

    SEARCH_URL = "https://www.jobkorea.co.kr/Search/"
    ROBOTS_URL = "https://www.jobkorea.co.kr/robots.txt"

    # 잡코리아는 마크업이 자주 바뀔 수 있어, 후보 셀렉터를 여러 개 순서대로 시도한다.
    # 이 세션에서는 네트워크 제약으로 실제 마크업을 확인하지 못했으므로,
    # 최초 실행 후 실패 로그를 보고 이 리스트를 갱신할 것.
    CARD_SELECTORS = [
        "list.post-list-info .list-item",
        ".list-default .list-post",
        "ul.clear li.list-post",
        ".recruit-info",
    ]
    TITLE_SELECTORS = ["a.title", ".title a", "a.dev-info-tit", "h4 a"]
    COMPANY_SELECTORS = ["a.corp-name-link", ".corp-name a", ".company-name"]
    LOCATION_SELECTORS = [".loc-cd", ".option .loc", ".recruit-info .loc"]
    CAREER_SELECTORS = [".career-cd", ".option .career", ".recruit-info .career"]
    DATE_SELECTORS = [".date", ".etc .date", ".reg-date"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.robot_parser = self._load_robots()

    def _load_robots(self):
        rp = RobotFileParser()
        rp.set_url(self.ROBOTS_URL)
        try:
            rp.read()
            return rp
        except Exception:
            log.error("[잡코리아] robots.txt를 읽을 수 없습니다 (%s). "
                      "허용 범위를 확인할 수 없으므로 안전하게 수집을 건너뜁니다.", self.ROBOTS_URL)
            return None

    def _allowed(self, url: str) -> bool:
        if self.robot_parser is None:
            return False
        try:
            return self.robot_parser.can_fetch(USER_AGENT, url)
        except Exception:
            return False

    def collect(self, keywords) -> list[dict]:
        if not self._allowed(self.SEARCH_URL):
            log.warning("[잡코리아] robots.txt 정책상 %s 크롤링이 허용되지 않아 건너뜁니다.", self.SEARCH_URL)
            return []

        all_jobs = []
        for keyword in keywords:
            try:
                jobs = self._search_keyword(keyword)
                log.info("[잡코리아] '%s' 키워드로 %d건 수집", keyword, len(jobs))
                all_jobs.extend(jobs)
            except Exception:
                log.exception("[잡코리아] '%s' 키워드 수집 실패", keyword)
            _polite_sleep()
        return all_jobs

    def _search_keyword(self, keyword: str) -> list[dict]:
        if not self._allowed(self.SEARCH_URL + f"?stext={keyword}"):
            return []
        resp = self.session.get(self.SEARCH_URL, params={"stext": keyword}, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        cards = []
        for selector in self.CARD_SELECTORS:
            cards = soup.select(selector)
            if cards:
                break
        if not cards:
            log.warning("[잡코리아] '%s' 검색결과에서 공고 카드를 찾지 못했습니다. "
                        "마크업이 변경되었을 수 있으니 CARD_SELECTORS를 갱신하세요.", keyword)
            return []

        jobs = []
        for card in cards:
            parsed = self._parse_card(card, keyword)
            if parsed:
                jobs.append(parsed)
        return jobs

    @staticmethod
    def _select_first(card, selectors):
        for sel in selectors:
            el = card.select_one(sel)
            if el and el.get_text(strip=True):
                return el
        return None

    def _parse_card(self, card, keyword: str) -> dict | None:
        try:
            title_el = self._select_first(card, self.TITLE_SELECTORS)
            company_el = self._select_first(card, self.COMPANY_SELECTORS)
            if not (title_el and company_el):
                return None

            title = title_el.get_text(strip=True)
            company_name = company_el.get_text(strip=True)
            href = title_el.get("href") or (company_el.get("href") or "")
            url = urljoin(self.SEARCH_URL, href) if href else None
            if not url:
                return None

            location_el = self._select_first(card, self.LOCATION_SELECTORS)
            career_el = self._select_first(card, self.CAREER_SELECTORS)
            date_el = self._select_first(card, self.DATE_SELECTORS)

            location = location_el.get_text(strip=True) if location_el else None
            career_text = career_el.get_text(strip=True) if career_el else ""
            posted_date = date_el.get_text(strip=True) if date_el else None

            body_text = card.get_text(" ", strip=True)
            tech_stack = extract_tech_stack(title, body_text)
            industry = classify_industry(body_text, company_name)

            return {
                "source": SOURCE_JOBKOREA,
                "company_name": company_name,
                "company_domain": industry,
                "job_title": title,
                "employment_type": normalize_employment_type(body_text),
                "tech_stack": tech_stack,
                "career_level": normalize_career_level(career_text),
                "location": location,
                "url": url,
                "posted_date": posted_date,
                "deadline": None,
                "matched_keyword": keyword,
            }
        except Exception:
            log.exception("[잡코리아] 카드 파싱 실패, 건너뜀")
            return None


def run(sources, keywords):
    init_db()

    collectors = {
        "saramin": lambda: SaraminCollector(os.environ.get("SARAMIN_ACCESS_KEY")).collect(keywords),
        "jobkorea": lambda: JobkoreaCollector().collect(keywords),
    }

    summary = {}
    all_jobs = []
    for name in sources:
        factory = collectors.get(name)
        if not factory:
            log.warning("알 수 없는 소스: %s", name)
            continue
        try:
            jobs = factory()
        except Exception:
            log.exception("[%s] 수집기 전체 실패 - 다른 소스는 계속 진행합니다.", name)
            jobs = []
        summary[name] = {"collected": len(jobs)}
        all_jobs.extend(jobs)

    inserted = updated = 0
    with get_conn() as conn:
        for job in all_jobs:
            result = upsert_job(conn, job)
            if result == "inserted":
                inserted += 1
            else:
                updated += 1

    log.info("=== 수집 결과 요약 ===")
    for name, stat in summary.items():
        log.info("  %s: %d건 조회", name, stat["collected"])
    log.info("  신규 저장: %d건 / 갱신(재등장): %d건 / 총 조회: %d건", inserted, updated, len(all_jobs))
    log.info("로그 파일: %s", _log_file)
    return {"summary": summary, "inserted": inserted, "updated": updated, "total": len(all_jobs)}


def main():
    parser = argparse.ArgumentParser(description="job-radar 채용공고 수집기")
    parser.add_argument("--sources", default="saramin,jobkorea", help="쉼표구분 (saramin,jobkorea)")
    parser.add_argument("--keywords", default=None, help="쉼표구분 검색 키워드 (기본: config.SEARCH_KEYWORDS)")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else SEARCH_KEYWORDS

    run(sources, keywords)


if __name__ == "__main__":
    main()
