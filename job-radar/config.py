"""job-radar 공통 설정: 검색 키워드, 기술스택/업종 분류 사전, DB 경로 등.

새 검색 키워드나 기술스택을 추가하려면 이 파일의 리스트/딕셔너리만 수정하면 된다.
(자세한 방법은 README.md '키워드 추가법' 참고)
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobs.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# --- 1. 검색 키워드 (SPEC 지정) -----------------------------------------
SEARCH_KEYWORDS = [
    "개발자", "백엔드", "프론트엔드", "풀스택", "앱 개발",
    "DevOps", "데이터 엔지니어", "AI 엔지니어", "SI", "SM",
]

# --- 2. 기술스택 키워드 사전 ------------------------------------------------
# key = 대시보드에 표시할 정규화된 이름, value = 본문에서 찾을 표기 변형(대소문자 무시, 단어경계 매칭)
TECH_STACK_KEYWORDS = {
    "Java": ["java"],
    "Kotlin": ["kotlin"],
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "React": ["react", "react.js", "reactjs"],
    "Vue.js": ["vue.js", "vuejs", "vue"],
    "Angular": ["angular"],
    "Spring": ["spring boot", "spring"],
    "Django": ["django"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "PHP": ["php"],
    "C#": ["c#", "csharp"],
    ".NET": [".net", "dotnet"],
    "C++": ["c++"],
    "Go": ["golang", " go "],
    "Ruby on Rails": ["ruby on rails", "rails", "ruby"],
    "Swift": ["swift"],
    "Objective-C": ["objective-c"],
    "Flutter": ["flutter"],
    "React Native": ["react native", "react-native"],
    "Android": ["android"],
    "iOS": ["ios"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Jenkins": ["jenkins"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "Linux": ["linux"],
    "MySQL": ["mysql"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Oracle": ["oracle"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch"],
    "Kafka": ["kafka"],
    "Spark": ["spark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "GraphQL": ["graphql"],
    "Git": ["git"],
    "MSA": ["msa", "microservice", "마이크로서비스"],
    "QA": ["qa", "품질보증"],
}

# --- 3. 업종/도메인 분류 사전 -----------------------------------------------
# 회사명/업종 텍스트에 포함된 키워드로 도메인을 추정한다.
INDUSTRY_KEYWORDS = {
    "금융": ["은행", "카드", "증권", "보험", "캐피탈", "핀테크", "저축은행", "자산운용", "금융"],
    "커머스": ["커머스", "쇼핑", "이커머스", "유통", "리테일", "마켓", "물류", "배달"],
    "SI": ["si", "시스템통합", "솔루션", "정보시스템", "sm", "아웃소싱", "it서비스"],
    "제조": ["제조", "전자", "반도체", "자동차", "화학", "중공업", "부품", "설비"],
    "스타트업": ["스타트업", "startup"],
    "게임": ["게임", "game"],
    "미디어/콘텐츠": ["미디어", "콘텐츠", "방송", "엔터테인먼트", "광고"],
    "교육": ["교육", "에듀"],
    "헬스케어": ["헬스케어", "병원", "제약", "바이오", "의료"],
    "공공/공기업": ["공사", "공단", "공기업", "정부", "공공"],
}
DEFAULT_INDUSTRY = "기타"

# --- 4. 인력유형 / 경력 정규화 ----------------------------------------------
EMPLOYMENT_TYPE_MAP = {
    "정규직": "정규직",
    "계약직": "계약직",
    "파견직": "파견",
    "파견": "파견",
    "프리랜서": "프리랜서",
    "인턴": "인턴",
}
DEFAULT_EMPLOYMENT_TYPE = "정규직"

CAREER_LEVEL_NEW = "신입"
CAREER_LEVEL_EXPERIENCED = "경력"
CAREER_LEVEL_ANY = "무관"

# --- 5. 수집 설정 -----------------------------------------------------------
REQUEST_DELAY_MIN_SEC = 2.0
REQUEST_DELAY_MAX_SEC = 3.0
USER_AGENT = "job-radar-collector/1.0 (+internal BD tooling; contact: admin)"

SOURCE_SARAMIN = "사람인"
SOURCE_JOBKOREA = "잡코리아"
