#!/usr/bin/env python3
"""[개발/검증용] 대시보드 확인을 위한 가상 샘플 데이터 시딩 스크립트.

이 스크립트가 넣는 회사명/공고는 전부 가상(fictional)이며 실제 기업과 무관하다.
개발 샌드박스의 네트워크 정책상 사람인/잡코리아에 실제로 접속할 수 없어
collector.py의 실 수집을 테스트할 수 없었기 때문에, 동일한 저장 로직(db.upsert_job)을
거치는 가상 데이터로 대시보드 UI/집계 로직을 검증하기 위해 작성했다.

실제 운영 시에는 이 스크립트를 실행하지 말고 SARAMIN_ACCESS_KEY를 설정한 뒤
`python collector.py`로 실 데이터를 수집할 것. (jobs.db를 초기화하려면 파일을 삭제 후
collector.py 또는 이 스크립트를 다시 실행하면 된다.)
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_conn, init_db, upsert_job  # noqa: E402

TODAY = datetime.now()


def d(days_ago):
    return (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")


SAMPLE_JOBS = [
    dict(source="사람인", company_name="블루오션커머스", company_domain="커머스", job_title="백엔드 개발자 (Java/Spring)",
         employment_type="정규직", tech_stack="Java,Spring,MySQL,AWS", career_level="경력", location="서울 강남구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/1", posted_date=d(1), deadline=d(-20), matched_keyword="백엔드"),
    dict(source="사람인", company_name="블루오션커머스", company_domain="커머스", job_title="프론트엔드 개발자 (React)",
         employment_type="정규직", tech_stack="React,TypeScript,JavaScript", career_level="경력", location="서울 강남구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/2", posted_date=d(1), deadline=d(-20), matched_keyword="프론트엔드"),
    dict(source="잡코리아", company_name="한빛저축은행", company_domain="금융", job_title="금융 IT 시스템 운영 (SM)",
         employment_type="계약직", tech_stack="Java,Oracle,Linux", career_level="경력", location="서울 중구",
         url="https://www.jobkorea.co.kr/Recruit/sample/3", posted_date=d(2), deadline=d(-15), matched_keyword="SM"),
    dict(source="사람인", company_name="그린테크시스템", company_domain="SI", job_title="SI 프로젝트 백엔드 개발자",
         employment_type="파견", tech_stack="Java,Spring,MySQL", career_level="경력", location="경기 성남시",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/4", posted_date=d(2), deadline=d(-25), matched_keyword="SI"),
    dict(source="사람인", company_name="그린테크시스템", company_domain="SI", job_title="공공기관 SM 인력 모집",
         employment_type="파견", tech_stack="Java,Oracle", career_level="무관", location="서울 종로구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/5", posted_date=d(3), deadline=d(-25), matched_keyword="SM"),
    dict(source="잡코리아", company_name="그린테크시스템", company_domain="SI", job_title="프론트엔드 파견 개발자 모집",
         employment_type="파견", tech_stack="JavaScript,Vue.js", career_level="경력", location="서울 종로구",
         url="https://www.jobkorea.co.kr/Recruit/sample/6", posted_date=d(4), deadline=d(-25), matched_keyword="프론트엔드"),
    dict(source="사람인", company_name="파인애플페이먼츠", company_domain="금융", job_title="풀스택 개발자",
         employment_type="정규직", tech_stack="Node.js,React,PostgreSQL", career_level="신입", location="서울 서초구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/7", posted_date=d(4), deadline=d(-18), matched_keyword="풀스택"),
    dict(source="사람인", company_name="스카이모빌리티", company_domain="제조", job_title="차량 임베디드 SW 개발자",
         employment_type="정규직", tech_stack="C++,Linux", career_level="경력", location="경기 화성시",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/8", posted_date=d(5), deadline=d(-10), matched_keyword="개발자"),
    dict(source="잡코리아", company_name="넥스트웨이브게임즈", company_domain="게임", job_title="게임 서버 개발자",
         employment_type="정규직", tech_stack="Java,Kotlin,Redis,AWS", career_level="경력", location="서울 강남구",
         url="https://www.jobkorea.co.kr/Recruit/sample/9", posted_date=d(5), deadline=d(-12), matched_keyword="백엔드"),
    dict(source="사람인", company_name="클라우드나인스타트업", company_domain="스타트업", job_title="DevOps 엔지니어",
         employment_type="정규직", tech_stack="Docker,Kubernetes,AWS,Terraform", career_level="경력", location="서울 성동구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/10", posted_date=d(6), deadline=d(-14), matched_keyword="DevOps"),
    dict(source="사람인", company_name="클라우드나인스타트업", company_domain="스타트업", job_title="데이터 엔지니어",
         employment_type="정규직", tech_stack="Python,Spark,Airflow,AWS", career_level="경력", location="서울 성동구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/11", posted_date=d(6), deadline=d(-14), matched_keyword="데이터 엔지니어"),
    dict(source="잡코리아", company_name="메디헬스바이오", company_domain="헬스케어", job_title="AI 엔지니어 (의료영상)",
         employment_type="정규직", tech_stack="Python,PyTorch,TensorFlow", career_level="경력", location="서울 송파구",
         url="https://www.jobkorea.co.kr/Recruit/sample/12", posted_date=d(7), deadline=d(-9), matched_keyword="AI 엔지니어"),
    dict(source="사람인", company_name="한강전자제조", company_domain="제조", job_title="제조 MES 시스템 SM 담당자",
         employment_type="계약직", tech_stack="Java,Oracle,MSA", career_level="경력", location="경기 수원시",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/13", posted_date=d(8), deadline=d(-8), matched_keyword="SM"),
    dict(source="사람인", company_name="스마트커머스랩", company_domain="커머스", job_title="앱 개발자 (Android)",
         employment_type="정규직", tech_stack="Kotlin,Android", career_level="경력", location="서울 마포구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/14", posted_date=d(9), deadline=d(-7), matched_keyword="앱 개발"),
    dict(source="잡코리아", company_name="스마트커머스랩", company_domain="커머스", job_title="앱 개발자 (iOS)",
         employment_type="정규직", tech_stack="Swift,iOS", career_level="경력", location="서울 마포구",
         url="https://www.jobkorea.co.kr/Recruit/sample/15", posted_date=d(9), deadline=d(-7), matched_keyword="앱 개발"),
    dict(source="사람인", company_name="퍼스트캐피탈", company_domain="금융", job_title="백엔드 개발자 (결제시스템)",
         employment_type="정규직", tech_stack="Java,Spring,Kafka,MySQL", career_level="경력", location="서울 여의도",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/16", posted_date=d(11), deadline=d(-5), matched_keyword="백엔드"),
    dict(source="사람인", company_name="에듀브릿지", company_domain="교육", job_title="프리랜서 프론트엔드 개발자",
         employment_type="프리랜서", tech_stack="React,JavaScript", career_level="무관", location="서울 강동구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/17", posted_date=d(13), deadline=d(-3), matched_keyword="프론트엔드"),
    dict(source="잡코리아", company_name="오션미디어그룹", company_domain="미디어/콘텐츠", job_title="풀스택 개발자",
         employment_type="정규직", tech_stack="Node.js,Vue.js,MongoDB", career_level="신입", location="서울 마포구",
         url="https://www.jobkorea.co.kr/Recruit/sample/18", posted_date=d(15), deadline=d(-1), matched_keyword="풀스택"),
    dict(source="사람인", company_name="한국물류공사", company_domain="공공/공기업", job_title="공공 SI 백엔드 개발자",
         employment_type="파견", tech_stack="Java,Spring,Oracle", career_level="경력", location="세종특별자치시",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/19", posted_date=d(18), deadline=d(-2), matched_keyword="SI"),
    dict(source="사람인", company_name="딥마인드팩토리", company_domain="스타트업", job_title="AI 엔지니어 (LLM)",
         employment_type="정규직", tech_stack="Python,PyTorch", career_level="경력", location="서울 강남구",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/20", posted_date=d(20), deadline=d(-1), matched_keyword="AI 엔지니어"),
    dict(source="잡코리아", company_name="그린테크시스템", company_domain="SI", job_title="데이터 엔지니어 파견",
         employment_type="파견", tech_stack="Python,Spark,Hadoop", career_level="경력", location="서울 종로구",
         url="https://www.jobkorea.co.kr/Recruit/sample/21", posted_date=d(22), deadline=d(2), matched_keyword="데이터 엔지니어"),
    dict(source="사람인", company_name="퍼스트캐피탈", company_domain="금융", job_title="DevOps 엔지니어 (금융클라우드)",
         employment_type="정규직", tech_stack="AWS,Docker,Kubernetes,Jenkins", career_level="경력", location="서울 여의도",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/22", posted_date=d(25), deadline=d(3), matched_keyword="DevOps"),
    dict(source="사람인", company_name="웨이브패션커머스", company_domain="커머스", job_title="백엔드 개발자 (신입)",
         employment_type="정규직", tech_stack="Python,Django,PostgreSQL", career_level="신입", location="서울 성수동",
         url="https://www.saramin.co.kr/zf_user/jobs/sample/23", posted_date=d(27), deadline=d(5), matched_keyword="개발자"),
    dict(source="잡코리아", company_name="스카이모빌리티", company_domain="제조", job_title="SM 담당 개발자 (사내 IT)",
         employment_type="계약직", tech_stack="Java,MySQL", career_level="경력", location="경기 화성시",
         url="https://www.jobkorea.co.kr/Recruit/sample/24", posted_date=d(28), deadline=d(6), matched_keyword="SM"),
]


def main():
    init_db()
    inserted = updated = 0
    with get_conn() as conn:
        for job in SAMPLE_JOBS:
            result = upsert_job(conn, job)
            if result == "inserted":
                inserted += 1
            else:
                updated += 1
    print(f"샘플 데이터 시딩 완료: 신규 {inserted}건 / 갱신 {updated}건 (총 {len(SAMPLE_JOBS)}건)")


if __name__ == "__main__":
    main()
