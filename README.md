# WoW KR Radar v0.4.2

한국 월드 오브 워크래프트 **본섭(리테일)** 플레이어를 위한 모바일/PC 대시보드. 공식 뉴스, Wowhead, 와우 인벤, Reddit 등의 공개 기사/게시물 메타데이터를 수집하고 원문 링크로 연결합니다.

## 포함
- 최신 기사 검색, 출처/주제 필터, 한국어 UI
- 공식·핫픽스 / 직업·밸런스 / 쐐기·레이드 / 로드맵 / 국내 소식
- 주간 아카이브 (각 ISO 주 `data/history/YYYY-Www.json`), 지난 기록 탐색 및 JSON 저장
- GitHub Actions 자동 수집: **매주 월요일 07:00 KST** (GitHub 실행 지연 가능)
- 해외 기사 제목과 요약의 선택적 AI 한국어 변환 (OpenAI API Key 필요)
- GitHub Pages 자동 배포, 반응형 지원

## 설치/로컬 실행
Node.js 22, Python 3.12 권장.
```bash
npm install
npm run dev
```
최초 포함 데이터는 데모/출처 안내로 표시됩니다. 실제 수집은 아래 명령 실행 후 브라우저를 새로고침하세요.
```bash
python -m pip install -r scripts/requirements.txt
python scripts/collect.py
npm run build
```

## GitHub 자동 운영
1. 새 GitHub 저장소에 전체 파일을 업로드하고 기본 브랜치를 **main**으로 설정.
2. **Settings → Pages → Build and deployment → Source = GitHub Actions** 선택.
3. **Actions**에서 `Collect WoW Retail News` 워크플로를 처음 한 번 수동 실행.
4. 필요한 경우 **Settings → Secrets and variables → Actions → New repository secret**에서 `OPENAI_API_KEY`를 설정하면 해외 제목 및 한 줄 요약이 한국어로 생성됩니다. 설정하지 않아도 원문 중심 피드는 동작하지만, 해외 기사 자동 번역은 실행되지 않습니다.
5. `Deploy Dashboard` 워크플로가 활성화되면 Pages URL에서 볼 수 있습니다.

**주의:** Actions는 운영 시작 전 설치/권한 설정이 필요합니다. 파일을 생성한 것만으로 자동 업데이트가 가동되지는 않습니다.

## 뉴스/번역 정책
- RSS 및 Google News 검색 RSS로 기사 제목, 간략 메타정보, 출처 URL만 수집. 본문 무단 전재/스크래핑 없음.
- Reddit RSS는 접근 제한될 수 있으며, 실패한 출처는 `data/latest.json`의 `collection.errors`에 남습니다.
- 해외 뉴스가 번역되지 않았으면 해당 사실을 명시. 기사 내용을 추정하여 사실로 보완하지 않음.
- 블리자드 1차 자료와 제3자 기사/커뮤니티를 구별. 미확정 출시일을 확정으로 표시하지 않음.
- 제목 분류와 Classic 차단은 규칙 기반이므로 오분류 가능. 링크의 원문을 확인.
- Google News RSS URL은 원문 URL이 아닌 뉴스 경유 링크일 수 있음.
- 저작권, robots.txt, API 조건, 속도 제한을 존중해야 함.
- `OPENAI_API_KEY` 입력 시 API 사용량에 따른 비용 발생.

## v0.4.2 — 한밤 시즌 전체 기간 역할별 DPS 비교
- MythicStats 한밤 시즌 1 (Period 1056~1075), 시즌 2 (1076~1090) 총 35개 검증 주차 관리
- 초기 백필에서 1077~1090 14개 주차 / 40개 전문화 수집. 과거 21주차는 원본이 해당 기간 대신 최신 Period를 반환해 미수집
- 딜러 27개, 탱커 6개, 힐러 7개 역할 분리 및 전문화별 Avg DPS 범위 그래프
- 최대 6개 전문화 비교, Avg/Top 5% 전환, 주차 최저 Avg와 Top 5% 명확히 구분
- 전체 주차 히트맵·수치 매트릭스 및 CSV 내보내기
- 미수집 주차는 숫자를 생성하지 않고 빈칸으로 표시
- MythicStats Top은 개별 최고치가 아닌 상위 5% 평균, Avg는 전체 던전 시간 기준
- 주차별 단수 범위 차이와 최신 주차 표본 수에 유의
- GitHub Collect 경합 방지 및 개발 히스토리 V0.4.2 PDF/PPTX 등록

## v0.4.1 — MythicStats 전문화별 DPS 주간 추이
- 왼쪽 메뉴에 **DPS 주간 추이** 탭. 직업/공격 전문화 선택과 Avg DPS/Top 5% 전환 그래프, 순위·Runs 표 제공
- 데이터 원문: https://mythicstats.com/dps (Warcraft Logs 집계, 쐐기 16~24단, 전체 던전 시간 기준)
- 매주 데이터 수집에서 최신 Period 통계 숫자만 `data/dps/period-N.json`에 별도 저장
- 최초 수집에서 원본에 실재하는 과거 7개 Period까지 제한적으로 보관 (총 8주)
- 오른쪽 **주간 히스토리**에도 DPS 기간별 JSON 다운로드 링크 추가
- 개발 히스토리 V0.4.1 PDF/PPTX 문서 자동 생성
- 주간 시작 시 데이터가 불안정하며 시즌 변경이나 원본 범위 차이로 단순한 DPS 수치 비교가 부정확할 수 있음
- 서버 호출/출처 파싱에 실패하면 숫자를 채워넣지 않고 이전 데이터 보존
- 외부 서비스의 이용 제한을 준수하고 원문 소유자의 자료라는 표시 유지

## v0.4 — 뉴스·My Watch·한국 쐐기 정보
- Reddit 직접 RSS의 404/429 문제를 줄이기 위해 Google News Reddit 색인 쿼리 사용. 수집되지 않은 토론이 있을 수 있으며 실시간 Reddit API가 아님
- 해외 뉴스 AI 요약은 **기사 원문 전체가 아닌 제목 및 RSS 요약 메타정보**를 근거로만 생성. `OPENAI_API_KEY` 미등록 시 원문 및 '미번역' 표시
- 이전 실행의 번역 결과 재사용. 수집 1회에 신규 번역 최대 40건, 8건 배치
- My Watch는 직업 단위에서 전문화 선택으로 확장. 기사 제목 키워드 매칭 방식이며 DPS/HPS 데이터는 아님
- 한국 쐐기 개별 기록은 `data/kr_runs.json`에 API 결과를 검증하여 저장. 결과 없거나 오류면 `unavailable` 표기하고 가짜 순위 없음
- GitHub 동시 변경으로 수집 데이터 push가 실패하는 문제 해결을 위해 rebase 후 재시도
- V0.4 히스토리 PDF/PPT 자동 생성
- 한국 지역 정밀 직업 메타와 Warcraft Logs 연동은 검증된 API 권한 확보 후 개발 예정

## v0.3.1 — 오른쪽 옵션 메뉴
- 메인 메뉴는 종합 현황 / 뉴스 / 직업 / 쐐기 / 한국 쐐기 / 시즌 로드맵으로 정리
- **My Watch / 주간 히스토리 / 개발 히스토리**는 오른쪽 보조 메뉴로 이동
- 태블릿과 모바일에서는 가로형 옵션 메뉴로 표시
- 기존 기록, 다운로드, 관심 직업 저장 및 뉴스 자동 수집 유지

## v0.3 — My Watch · KR Mythic+ · Feed Health
- 관심 직업 13종 선택 후 관련 기사 필터링 (현재 브라우저의 localStorage에만 저장)
- **한국 쐐기** 메뉴에서 Raider.IO 공개 API의 한국 지역(kr) 쐐기 주간 속성 표시
- API 오류 시 임의 랭킹/속성을 만들지 않고 미수집 상태 표시
- `data/kr_mplus.json`을 매주 자동 수집하여 뉴스와 함께 기록
- Reddit RSS 경로 수정; Reddit 측 429 등은 별도로 추적
- 수집 소스별 성공 상태(feed_results) JSON 기록
- 개발 버전 V0.3 PDF/PPTX 요약 추가
- 해외 뉴스 한국어 AI 번역은 **OPENAI_API_KEY 설정 시**에만 활성화됨
- 아직 한국 서버 쐐기 **랭킹·메타 통계**는 미구현이며 후속 계획

## v0.2.1 버전 히스토리 센터
- 새 메뉴 **개발 히스토리**에서 사이트 개발 버전 V0.1 / V0.2 / V0.2.1의 변경사항 열람
- 버전별 PDF 및 PPTX 요약 보고서를 GitHub Pages 배포 과정에서 자동 생성
- 버전별 GitHub 커밋 링크 제공, 주간 뉴스 아카이브와 개발 이력 분리
- 개발 버전 기록은 `data/releases.json`에 수동으로 관리하며 매 버전 업데이트 시 항목을 추가
- PDF/PPT는 변경사항을 요약한 자료이며 버전 전체 소스의 백업이 아님

## v0.2 변경 내용
- 클래식/포에버/무관한 게시판 등 본섭 외 결과 필터 강화 (제목 기반이므로 한계 있음)
- 새로운 주와 이전 주의 기사 ID 비교, NEW 레이블, 수집 품질 보드
- 번역 여부 명시 및 해외 기사 원제 토글
- `tests/test_retail.py` 단위 테스트로 주요 분류 사례 검사
- Google News 경유 URL은 경유 링크로 명시하며 원문 직링크로 단정하지 않음
- 외부 RSS의 429·404 등 수집 오류는 API 안정화 작업이 필요함
- 영어 기사 자동 한국어 변환은 여전히 `OPENAI_API_KEY` 연결이 필요함

## 다음 개발 단계
v0.2: 통계/주별 비교, 원문 URL 해석 및 사이트별 정확도 향상, 원문/한국어 병렬 보기.
v0.3: 한국 지역 쐐기/레이드 순위 (Raider.IO API), 클래스별 My Watch, 데이터 품질 보드.
v0.4: Warcraft Logs 공식 API, 직업별 성능 추이, 유저별 관찰 목록 및 주간 변경점.

본 프로젝트는 비공식 팬 프로젝트이며 Blizzard Entertainment, Wowhead, Inven, Reddit 및 Raider.IO와 제휴/승인 관계가 없습니다.
