# kr10pct-marketwatch-feed

`kr-10pct-screener`(마켓워치/돌파워치 앱)의 로컬 일일 스캔 결과를 클라우드 발행
루틴에 전달하기 위한 데이터 피드 저장소입니다. 무거운 스캔은 전부 로컬
(launchd, `com.park.kr10pct.marketwatch`)에서 돌고, 이 저장소에는 결과
JSON만 매일 push됩니다.

`data/` 안 파일:
- `out.json` — 탭1 브레이크아웃 워치
- `imminent_today.json` — 탭2 임박 스캐너
- `volatility_today.json` — 탭3 변동성 패턴
- `chart_data.json` — 캔들차트 데이터(MA5/10/20/240)
- `meta.json` — 마지막 갱신 날짜/시각

클라우드 루틴(`stock-watchlist-daily-update`)이 이 저장소를 clone해서
`data/`의 4개 JSON을 읽어 Claude Artifact("브레이크아웃 워치")의 4개
`const` 블록을 교체하고 재발행합니다. 개인 계좌·재무 정보는 포함되지
않으며, 종목 코드/이름/가격/기술지표 같은 일반 스크리닝 결과만 담깁니다.
