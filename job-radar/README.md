# job-radar

개발자 인력소싱(ITO) 업체 BD 담당자를 위한 채용공고 수집·분석 시스템.
사람인/잡코리아에서 개발자 채용공고를 수집해 SQLite에 저장하고, 웹 대시보드로
기업/도메인/기술스택 트렌드를 보여준다 (영업 타겟팅 활용 목적).

## ⚠️ 개발 환경 관련 중요 안내

이 프로젝트는 네트워크가 제한된 개발 샌드박스에서 작성되었다. `saramin.co.kr`,
`jobkorea.co.kr` 등 외부 도메인으로의 아웃바운드 접속이 정책상 차단되어 있어서,
**collector.py의 실제 API 호출/스크래핑을 라이브로 테스트하지 못했다.**
그래서:

- `jobs.db`에는 `scripts/seed_sample_data.py`로 넣은 **가상 샘플 데이터 24건**이
  들어있다. 회사명은 전부 가상(fictional)이며 대시보드 UI·필터·차트 집계 로직을
  검증하기 위한 용도다. 실제 회사와 무관하다.
- 사람인 API 응답 필드명은 공개적으로 알려진 스펙을 기반으로 방어적으로
  파싱하도록 구현했지만(`collector.py`의 `SaraminCollector._parse_job`), 실제
  access-key로 1회 실행해서 필드가 잘 채워지는지 확인/보정이 필요하다.
- 잡코리아는 마크업이 자주 바뀌고, 이 환경에서 실제 HTML을 확인하지 못했다.
  `collector.py`의 `JobkoreaCollector`에 있는 `CARD_SELECTORS` 등 CSS
  셀렉터 후보들을 브라우저 개발자도구로 실제 검색결과 페이지를 열어 확인 후
  갱신해야 한다. robots.txt는 collector가 실행 시점에 매번 직접 조회해서
  허용 범위를 확인하며, 허용되지 않거나 조회 실패 시 안전하게 수집을 건너뛴다.

인터넷 접근이 되는 환경(개발자 PC 등)에서 아래 절차대로 실행하면 실제 데이터로
전환된다.

## 1. 설치

```bash
cd job-radar
python3 -m venv venv && source venv/bin/activate   # 선택사항
pip install -r requirements.txt
```

## 2. 데이터 수집 (collector.py)

### 2-1. 사람인 오픈 API access-key 발급

1. https://oapi.saramin.co.kr/join 에서 이용신청
2. 승인 메일 수신 후 사람인 로그인 → [Application] → [앱 등록]
3. access-key 발급 (1일 최대 500회 호출 제한)
4. 환경변수로 등록:
   ```bash
   export SARAMIN_ACCESS_KEY="발급받은-키"
   ```

access-key가 없으면 collector.py는 사람인 수집을 건너뛰고 경고 로그만 남긴다
(에러로 죽지 않음).

### 2-2. 잡코리아

공식 API가 없어 `requests` + `BeautifulSoup`으로 수집한다. 매 실행마다
`robots.txt`를 조회해서 허용 범위를 확인하고, 요청 사이 2~3초 딜레이를 둔다.
잡코리아가 마크업을 바꾸면 `collector.py`의 `JobkoreaCollector` 상단
`CARD_SELECTORS`/`TITLE_SELECTORS` 등을 실제 페이지에 맞게 수정해야 한다.

### 2-3. 실행

```bash
python collector.py                      # 사람인 + 잡코리아 전체 수집
python collector.py --sources saramin    # 사람인만
python collector.py --keywords "백엔드,DevOps"   # 키워드 지정
```

실행 결과는 `logs/collector_YYYYMMDD_HHMMSS.log`에 저장되고, 마지막에 소스별
수집 건수·신규저장/갱신 건수 요약이 남는다. 한 소스가 실패해도 다른 소스는
계속 수집된다.

### 2-4. (개발용) 샘플 데이터로 대시보드만 먼저 확인하고 싶을 때

```bash
python scripts/seed_sample_data.py
```

## 3. 웹 대시보드 (app.py)

```bash
python app.py
```

브라우저에서 http://localhost:8080 접속. 탭 2개:

- **공고 리스트**: 등록일 최신순, 출처/도메인/스택(다중선택)/인력유형/경력/지역
  필터 + 키워드 검색. 카드 클릭 시 원본 공고를 새 탭으로 연다.
- **트렌드 대시보드**: 최근 7일/30일 토글, 도메인별 공고 수·기술스택 TOP15·
  일별 등록량 추이·공고 많이 올린 기업 TOP10(영업 타겟 리스트) 차트와 요약 카드.

Chart.js는 `static/js/vendor/chart.umd.js`에 로컬로 포함되어 있어 인터넷
연결 없이도 대시보드가 동작한다.

## 4. 스케줄링 (매일 09:00 KST 자동 수집)

```bash
bash scripts/register_schedule.sh
```

OS를 자동 감지해서 등록한다:

- **macOS**: `~/Library/LaunchAgents/com.jobradar.collector.plist` 생성 후
  `launchctl load -w`로 등록
- **Linux**: `crontab`에 등록 (cron 데몬이 없으면 먼저 설치 필요:
  `sudo apt-get install -y cron && sudo service cron start`)

시스템 로컬 타임존이 KST가 아니어도 스크립트가 "KST 09:00"에 해당하는 로컬
시/분을 자동 계산해서 등록하므로 그대로 실행하면 된다.

### 스케줄 수정법

- **시간 변경**: `scripts/register_schedule.sh`에서 `datetime.time(9, 0)` 부분을
  원하는 KST 시각으로 바꾼 뒤 스크립트를 다시 실행하면 기존 등록을 덮어쓴다.
- **수동으로 crontab 확인/수정**: `crontab -l` / `crontab -e`
  (job-radar 항목은 줄 끝의 `# job-radar-collector` 마커로 식별된다)
- **macOS에서 직접 수정**: plist 파일의 `Hour`/`Minute` 값을 수정 후
  `launchctl unload -w ~/Library/LaunchAgents/com.jobradar.collector.plist` →
  `launchctl load -w 같은경로`
- **해제**: Linux는 `crontab -l | grep -v '# job-radar-collector' | crontab -`,
  macOS는 `launchctl unload ~/Library/LaunchAgents/com.jobradar.collector.plist`

## 5. 키워드 추가법

`config.py` 상단의 리스트/딕셔너리만 수정하면 된다 (코드 변경 불필요):

- `SEARCH_KEYWORDS`: 수집 시 검색할 키워드 목록
- `TECH_STACK_KEYWORDS`: 공고 본문에서 추출할 기술스택과 그 표기 변형들
- `INDUSTRY_KEYWORDS`: 기업 업종을 분류하는 도메인별 키워드
- `EMPLOYMENT_TYPE_MAP`: 인력유형(정규직/계약직/파견/프리랜서 등) 정규화 사전

## 6. 프로젝트 구조

```
job-radar/
├── collector.py            # 수집기 (사람인 API + 잡코리아 스크래퍼)
├── app.py                  # Flask 웹 대시보드
├── config.py                # 키워드/기술스택/업종 등 공통 설정
├── db.py                    # SQLite 저장 레이어 (스키마, upsert)
├── extract.py                # 기술스택/업종/경력 추출 유틸
├── templates/index.html     # 대시보드 단일 HTML (탭 2개)
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── js/vendor/chart.umd.js  # Chart.js (로컬 vendoring)
├── scripts/
│   ├── seed_sample_data.py   # (개발용) 가상 샘플 데이터 시딩
│   └── register_schedule.sh  # 스케줄러 등록 (launchd/crontab)
├── jobs.db                   # SQLite DB (수집기가 자동 생성)
├── logs/                     # 수집 로그
└── requirements.txt
```

## 7. DB 스키마 (jobs 테이블)

`hash`(기업명+공고제목+URL의 SHA-256)로 중복을 제거한다. 이미 존재하는 공고가
다시 수집되면 `last_seen`, `deadline`만 갱신하고 새 행을 만들지 않는다.

주요 컬럼: `source`, `company_name`, `company_domain`, `job_title`,
`employment_type`, `tech_stack`(콤마 구분), `career_level`, `location`, `url`,
`posted_date`, `deadline`, `first_seen`, `last_seen`, `collected_at`.
