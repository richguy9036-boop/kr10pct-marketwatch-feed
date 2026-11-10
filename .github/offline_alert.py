"""장중 맥북 오프라인 카톡 알림(2026-11-10 사용자 요청 '4번') — GitHub Actions에서 10분마다.

맥북(vi_quick)은 장중 1분마다 이 저장소에 data/out.json을 push한다(평소 최대 간격 약 10분).
KRX 개장일 09:20~15:30 KST에 마지막 커밋이 20분 넘게 없으면 '맥북 오프라인 추정' 카톡을 보낸다.
같은 공백(같은 마지막 커밋)엔 한 번만 — 워크플로가 actions/cache 키 alerted-<커밋>으로 중복을 막는다.
비밀값(KAKAO_CLIENT_SECRET·KAKAO_REFRESH_TOKEN)은 사용자가 scripts/set_offline_alert_secret.sh로 넣는다.
출력(GITHUB_OUTPUT): stale=1/0, sha, msg. --send 면 카톡 발송.
"""
import datetime as dt
import json
import os
import subprocess
import sys

KST = dt.timezone(dt.timedelta(hours=9))
GAP_MIN = 20
CLIENT_ID = "1a6a31af72c94c72db653a38c6ceac35"
LINK = "https://claude.ai/code/artifact/9ba272e0-a40b-4428-bacf-f0369a0d6210"
NOT_CLOSED = ("노동절", "제헌절")  # 공휴일이지만 KRX 개장(scripts/daily_imminent_scan.py와 같음)


def krx_open(d: dt.date) -> bool:
    import holidays
    if d.weekday() >= 5 or (d.month == 12 and d.day == 31):  # 연말 휴장
        return False
    name = holidays.KR(years=[d.year]).get(d)
    return name is None or any(x in name for x in NOT_CLOSED)


def out(**kv):
    p = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if p:
        with open(p, "a") as f:
            f.write(lines)
    print(lines, end="")


def check() -> None:
    now = dt.datetime.now(KST)
    sha, ts = subprocess.run(["git", "log", "-1", "--format=%H %ct"], capture_output=True, text=True,
                             check=True).stdout.split()
    last = dt.datetime.fromtimestamp(int(ts), KST)
    gap = (now - last).total_seconds() / 60
    in_hours = dt.time(9, 20) <= now.time() <= dt.time(15, 30)
    stale = krx_open(now.date()) and in_hours and gap >= GAP_MIN
    since = max(last, now.replace(hour=9, minute=0, second=0, microsecond=0))
    msg = (f"[맥북 오프라인?] {since:%H:%M}부터 {(now - since).total_seconds() / 60:.0f}분째 앱 갱신 없음"
           f" — 상승 VI·체결강도·상한가 확률 멈춤. 맥북 잠자기·인터넷 끊김 확인해 주세요")
    print(f"지금 {now:%Y-%m-%d %H:%M} · 마지막 커밋 {last:%m-%d %H:%M}({gap:.0f}분 전) · 장중 {in_hours} · 알림 {stale}")
    out(stale=int(stale), sha=sha, msg=msg.replace("\n", " "))


def send(text: str) -> None:
    import requests
    r = requests.post("https://kauth.kakao.com/oauth/token", timeout=15, data={
        "grant_type": "refresh_token", "client_id": CLIENT_ID,
        "client_secret": os.environ["KAKAO_CLIENT_SECRET"], "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"]})
    if r.status_code != 200:
        sys.exit(f"카카오 토큰 갱신 실패 {r.status_code} — set_offline_alert_secret.sh 다시 실행 필요")
    tok = r.json()["access_token"]
    t = {"object_type": "text", "text": text, "link": {"web_url": LINK, "mobile_web_url": LINK}}
    s = requests.post("https://kapi.kakao.com/v2/api/talk/memo/default/send", timeout=15,
                      headers={"Authorization": f"Bearer {tok}"}, data={"template_object": json.dumps(t, ensure_ascii=False)})
    if s.status_code != 200:
        sys.exit(f"카톡 발송 실패 {s.status_code}")
    print("카톡 발송 완료")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--send":
        send(os.environ["MSG"])
    else:
        check()
