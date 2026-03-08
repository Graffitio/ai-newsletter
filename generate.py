#!/usr/bin/env python3
"""
4lynx AI Daily Briefing — 자동 뉴스레터 생성기

매일 아침 실행되어:
1. Anthropic API (web search) 로 최신 AI 뉴스 수집
2. 4lynx 브랜드 HTML 뉴스레터 생성
3. docs/ 폴더에 저장 (GitHub Pages 자동 배포)
4. 아카이브 인덱스 페이지 업데이트
5. Google Chat 웹훅으로 링크 발송
"""

import anthropic
import json
import os
import re
import base64
import glob
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── 환경 변수 ────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CHAT_WEBHOOK = os.environ["GOOGLE_CHAT_WEBHOOK"]
PAGES_BASE_URL = os.environ.get("PAGES_BASE_URL", "https://4lynx.github.io/ai-newsletter")

# ─── 날짜 설정 (KST) ─────────────────────────────────
KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
DATE_STR = now.strftime("%Y년 %m월 %d일")
DATE_DAY = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"][now.weekday()]
DATE_FILE = now.strftime("%Y-%m-%d")
ISSUE_NUM = (now - datetime(2026, 3, 9, tzinfo=KST)).days + 1

# ─── 경로 설정 ────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DOCS_DIR = PROJECT_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)


def fetch_ai_news() -> dict:
    """Anthropic API로 오늘의 AI 뉴스를 수집하고 구조화된 JSON으로 반환"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ── STEP 1: 웹 검색으로 뉴스 수집 ──
    search_prompt = f"오늘은 {DATE_STR}입니다. 오늘과 어제의 AI 관련 주요 뉴스를 웹에서 검색해서 최대한 많이 알려주세요. 각 뉴스의 제목, 출처, 핵심 내용을 정리해주세요."

    search_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": search_prompt}],
    )

    # 검색 결과 텍스트 추출
    search_text = ""
    for block in search_response.content:
        if hasattr(block, 'text') and block.text:
            search_text += block.text + "\n"

    print(f"   📝 검색 결과: {len(search_text)}자")

    # ── STEP 2: 검색 결과를 JSON으로 변환 (웹 검색 없이) ──
    json_prompt = f"""아래는 오늘({DATE_STR} {DATE_DAY})의 AI 뉴스 검색 결과입니다.

<news>
{search_text}
</news>

위 뉴스를 아래 JSON 형식으로 변환하세요.
반드시 유효한 JSON만 출력하세요. JSON 앞뒤에 어떤 텍스트도 넣지 마세요.
```json 같은 마크다운도 넣지 마세요.

{{"main_stories":[{{"tag":"카테고리","tag_emoji":"이모지","source":"출처","title":"제목","body":"요약"}}],"quick_bites":["한줄뉴스"],"insight":"인사이트","glossary":[{{"term":"용어","en":"영문","definition":"설명"}}]}}

규칙:
- main_stories 정확히 6개 (첫번째가 TOP STORY)
- quick_bites 정확히 5개 (핵심 키워드는 <strong> 태그)
- glossary 정확히 3개 (오늘 뉴스에 등장한 용어)
- insight는 4~5문장 (핵심 키워드는 <strong> 태그)
- tag는 반도체/모델/정책/연구/에이전트/기업/투자 중 택1
- 모든 내용은 한국어"""

    json_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[{"role": "user", "content": json_prompt}],
    )

    # JSON 추출
    full_text = ""
    for block in json_response.content:
        if hasattr(block, 'text') and block.text:
            full_text += block.text

    print(f"   📝 JSON 응답: {len(full_text)}자")

    # 정리
    clean = full_text.strip()
    clean = re.sub(r"```json\s*", "", clean)
    clean = re.sub(r"```\s*", "", clean)

    # { } 블록 추출
    brace_depth = 0
    start_idx = None
    for i, c in enumerate(clean):
        if c == '{':
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif c == '}':
            brace_depth -= 1
            if brace_depth == 0 and start_idx is not None:
                json_str = clean[start_idx:i+1]
                try:
                    result = json.loads(json_str)
                    if "main_stories" in result:
                        print(f"   ✅ JSON 파싱 성공!")
                        return result
                except json.JSONDecodeError:
                    continue

    raise ValueError(f"JSON 파싱 실패. 응답 앞부분:\n{clean[:500]}")


def build_html(news: dict) -> str:
    """뉴스 데이터를 4lynx 브랜드 HTML 뉴스레터로 변환"""
    logo_path = PROJECT_DIR / "templates" / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        logo_uri = f"data:image/png;base64,{logo_b64}"
    else:
        logo_uri = ""

    logo_img = f'<img src="{logo_uri}" class="logo-img" alt="4lynx">' if logo_uri else '<span style="font-weight:900;color:#1B1464;font-size:18px;">4lynx</span>'
    footer_logo = f'<img src="{logo_uri}" class="footer-logo" alt="4lynx"><br>' if logo_uri else ''

    tag_styles = {
        "반도체": ("FFF7ED", "C2410C"), "모델": ("E0EAFC", "1B1464"),
        "정책": ("EDE9FE", "5B21B6"), "연구": ("D1FAE5", "047857"),
        "에이전트": ("E0F2FE", "0369A1"), "기업": ("FEF3C7", "B45309"),
        "투자": ("FCE7F3", "DB2777"),
    }

    story_cards = ""
    for i, s in enumerate(news["main_stories"][:6]):
        is_top = (i == 0)
        bg, fg = tag_styles.get(s["tag"], ("F5F5F5", "333333"))
        if is_top:
            tag_html = f'<span class="story-tag" style="background:#1B1464;color:#FFF;">{s["tag_emoji"]} TOP STORY</span>'
            card_class = "story-card top"
        else:
            tag_html = f'<span class="story-tag" style="background:#{bg};color:#{fg};">{s["tag_emoji"]} {s["tag"]}</span>'
            card_class = "story-card"
        story_cards += f'''
    <article class="{card_class}" onclick="toggleStory(this)">
      {tag_html}<span class="story-source">{s["source"]}</span>
      <div class="story-title">{s["title"]}</div>
      <div class="story-body"><p>{s["body"]}</p></div>
      <div class="story-toggle">▼ 자세히 보기</div>
    </article>'''

    bites_html = "\n".join(
        f'    <div class="bite"><span class="bite-num">{i+1:02d}</span><span class="bite-text">{b}</span></div>'
        for i, b in enumerate(news["quick_bites"][:5])
    )

    glossary_html = "\n".join(
        f'''    <div class="glossary-item">
      <div class="glossary-term">{g["term"]}</div>
      <div class="glossary-en">{g["en"]}</div>
      <div class="glossary-def">{g["definition"]}</div>
    </div>''' for g in news["glossary"][:3]
    )

    # 전체 HTML 템플릿
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>오늘의 AI 브리핑 — {DATE_STR}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{--navy:#1B1464;--blue:#3569B8;--blue-lt:#8ECAE6;--blue-pale:#C2E2F5;--bg:#F4F7FB;--surface:#FFF;--text-pri:#1B1464;--text-sec:#3D3A6B;--text-muted:#8B8AAF;--border:#D8DFEC;--border-lt:#E8EDF5}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Noto Sans KR',sans-serif;background:var(--bg);color:var(--text-pri);line-height:1.7;-webkit-font-smoothing:antialiased}}
  .container{{max-width:680px;margin:0 auto;padding:0 20px}}
  header{{background:linear-gradient(135deg,#FFF 0%,#E8EEF9 40%,#D4E0F5 100%);padding:0 20px;position:relative}}
  header::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--navy),var(--blue),var(--blue-lt),var(--blue-pale))}}
  header .container{{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;padding-top:24px;padding-bottom:28px}}
  .header-left{{flex:1;min-width:260px}}
  .logo-area{{display:flex;align-items:center;gap:12px;margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid var(--border-lt)}}
  .logo-img{{height:32px;width:auto}}.logo-div{{color:var(--border);font-size:20px;font-weight:300;margin:0 2px}}
  .logo-label{{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:500;color:var(--blue);letter-spacing:.06em;text-transform:uppercase}}
  .issue-meta{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--blue);letter-spacing:.12em;text-transform:uppercase;font-weight:600;margin-bottom:8px}}
  .header-title{{font-size:32px;font-weight:900;color:var(--navy);letter-spacing:-.03em;line-height:1.2}}
  .header-sub{{font-size:14px;color:var(--text-sec);margin-top:6px;font-weight:300}}
  .header-author{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-muted);margin-top:8px;font-weight:400;letter-spacing:.03em}}
  .header-date{{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--text-muted);text-align:right;padding-top:50px;line-height:1.5}}
  .section-label{{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;display:flex;align-items:center;gap:10px;margin-bottom:16px;color:var(--navy)}}
  .section-label::after{{content:'';flex:1;height:1px;background:var(--border)}}
  .section-label.blue{{color:var(--blue)}}
  .stories{{margin-top:28px}}
  .story-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 22px;margin-bottom:12px;cursor:pointer;transition:box-shadow .2s,border-color .2s}}
  .story-card:hover{{box-shadow:0 4px 24px rgba(27,20,100,.07);border-color:#B0BCDA}}
  .story-card.top{{border-left:4px solid var(--navy);background:linear-gradient(135deg,#F5F3FF,#FFF)}}
  .story-tag{{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;letter-spacing:.08em;padding:3px 8px;border-radius:4px;text-transform:uppercase}}
  .story-source{{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-muted)}}
  .story-title{{font-size:17px;font-weight:700;line-height:1.5;color:var(--text-pri);margin:6px 0 0}}
  .story-card.top .story-title{{font-size:19px}}
  .story-body{{max-height:0;overflow:hidden;transition:max-height .4s ease,opacity .3s;opacity:0}}
  .story-body.open{{max-height:400px;opacity:1}}
  .story-body p{{font-size:14px;line-height:1.8;color:var(--text-sec);margin-top:12px}}
  .story-toggle{{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-muted);margin-top:8px}}
  .quick-bites{{margin-top:28px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 22px}}
  .bite{{display:flex;gap:14px;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--border-lt)}}
  .bite:last-child{{border-bottom:none}}
  .bite-num{{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--blue);font-weight:600;min-width:20px;padding-top:3px}}
  .bite-text{{font-size:13.5px;line-height:1.7;color:var(--text-sec)}}
  .insight-box{{margin-top:28px;background:linear-gradient(135deg,#EDF1FA,#E0EAFC);border:1px solid #B0C4E8;border-radius:10px;padding:22px 24px}}
  .insight-box .section-label{{color:#2A2082}}
  .insight-box p{{font-size:14px;line-height:1.85;color:var(--navy)}}
  .insight-box strong{{font-weight:700}}
  .glossary{{margin-top:28px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:22px 24px}}
  .glossary .section-label{{color:var(--blue)}}
  .glossary-item{{padding:14px 0;border-bottom:1px solid var(--border-lt)}}
  .glossary-item:last-child{{border-bottom:none}}
  .glossary-term{{font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:600;color:var(--navy);margin-bottom:4px}}
  .glossary-en{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-muted);margin-bottom:6px}}
  .glossary-def{{font-size:13.5px;line-height:1.75;color:var(--text-sec)}}
  footer{{margin-top:32px;padding:20px 0 36px;text-align:center;position:relative}}
  footer::before{{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:100%;max-width:680px;height:3px;background:linear-gradient(90deg,var(--navy),var(--blue),var(--blue-lt),var(--blue-pale))}}
  .footer-logo{{height:20px;width:auto;margin-bottom:8px;opacity:.5}}
  .footer-brand{{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--text-muted);letter-spacing:.12em}}
  .footer-note{{font-size:12px;color:var(--text-muted);margin-top:6px}}
  .archive-link{{display:inline-block;margin-top:8px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--blue);text-decoration:none;letter-spacing:.05em}}
  .archive-link:hover{{text-decoration:underline}}
  @media(max-width:480px){{.header-title{{font-size:26px}}.story-card{{padding:16px 18px}}.container{{padding:0 16px}}.header-date{{padding-top:0}}}}
  @media print{{body{{background:#fff}}.story-body{{max-height:none!important;opacity:1!important}}.story-toggle{{display:none}}}}
</style>
</head>
<body>
<header>
  <div class="container">
    <div class="header-left">
      <div class="logo-area">
        {logo_img}
        <span class="logo-div">|</span>
        <span class="logo-label">AI Daily Briefing</span>
      </div>
      <div class="issue-meta">Vol.1 — Issue #{ISSUE_NUM:03d}</div>
      <h1 class="header-title">오늘의 AI 브리핑</h1>
      <p class="header-sub">매일 아침, AI 업계에서 가장 중요한 소식만 골라 전해 드립니다.</p>
      <p class="header-author">by Ian Jung</p>
    </div>
    <div class="header-date">{DATE_STR}<br>{DATE_DAY}</div>
  </div>
</header>
<main class="container">
  <section class="stories">
    <div class="section-label">📰 주요 뉴스 6선</div>
{story_cards}
  </section>
  <section class="quick-bites">
    <div class="section-label blue">⚡ 한 줄 뉴스</div>
{bites_html}
  </section>
  <section class="insight-box">
    <div class="section-label">💡 오늘의 인사이트</div>
    <p>{news["insight"]}</p>
  </section>
  <section class="glossary">
    <div class="section-label">📖 오늘의 AI 용어</div>
{glossary_html}
  </section>
</main>
<footer>
  <div class="container">
    {footer_logo}
    <div class="footer-brand">AI DAILY BRIEFING</div>
    <div class="footer-note">내일도 아침에 만나요 ☕</div>
    <a href="./index.html" class="archive-link">📂 지난 호 보기 →</a>
  </div>
</footer>
<script>
function toggleStory(card){{
  const body=card.querySelector('.story-body');
  const toggle=card.querySelector('.story-toggle');
  const isOpen=body&&body.classList.contains('open');
  document.querySelectorAll('.story-body.open').forEach(el=>{{
    el.classList.remove('open');
    const t=el.closest('.story-card').querySelector('.story-toggle');
    if(t)t.textContent='▼ 자세히 보기';
  }});
  if(!isOpen&&body){{body.classList.add('open');if(toggle)toggle.textContent='▲ 접기';}}
}}
</script>
</body>
</html>'''


def build_index():
    """docs/ 폴더의 모든 뉴스레터를 나열하는 아카이브 인덱스 생성"""
    logo_path = PROJECT_DIR / "templates" / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        logo_uri = f"data:image/png;base64,{logo_b64}"
        logo_img = f'<img src="{logo_uri}" style="height:28px;width:auto" alt="4lynx">'
    else:
        logo_img = '<span style="font-weight:900;color:#1B1464;">4lynx</span>'

    files = sorted(glob.glob(str(DOCS_DIR / "*.html")), reverse=True)
    items = ""
    for f in files:
        fname = Path(f).name
        if fname == "index.html":
            continue
        # 파일명에서 날짜 추출: 2026-03-08.html
        date_part = fname.replace(".html", "")
        try:
            d = datetime.strptime(date_part, "%Y-%m-%d")
            label = d.strftime("%Y년 %m월 %d일") + " " + ["월","화","수","목","금","토","일"][d.weekday()] + "요일"
        except ValueError:
            label = fname
        items += f'      <a href="{fname}" class="issue-link"><span class="issue-date">{label}</span><span class="arrow">→</span></a>\n'

    if not items:
        items = '      <p style="color:#8B8AAF;font-size:13px;">아직 발행된 호가 없습니다.</p>\n'

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>4lynx AI Daily Briefing — Archive</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Noto Sans KR',sans-serif;background:#F4F7FB;color:#1B1464;line-height:1.7}}
  .container{{max-width:680px;margin:0 auto;padding:40px 20px}}
  .logo-area{{display:flex;align-items:center;gap:12px;margin-bottom:32px;padding-bottom:16px;border-bottom:1px solid #E8EDF5}}
  .logo-div{{color:#D8DFEC;font-size:20px;font-weight:300}}
  .logo-label{{font-family:'JetBrains Mono',monospace;font-size:11px;color:#3569B8;letter-spacing:.06em;text-transform:uppercase}}
  h1{{font-size:24px;font-weight:900;color:#1B1464;margin-bottom:6px}}
  .subtitle{{font-size:13px;color:#3D3A6B;margin-bottom:28px;font-weight:300}}
  .issue-link{{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;background:#FFF;border:1px solid #D8DFEC;border-radius:8px;margin-bottom:8px;text-decoration:none;color:#1B1464;transition:box-shadow .2s,border-color .2s}}
  .issue-link:hover{{box-shadow:0 4px 20px rgba(27,20,100,.06);border-color:#B0BCDA}}
  .issue-date{{font-size:14px;font-weight:500}}
  .arrow{{font-family:'JetBrains Mono',monospace;font-size:14px;color:#3569B8}}
</style>
</head>
<body>
  <div class="container">
    <div class="logo-area">
      {logo_img}
      <span class="logo-div">|</span>
      <span class="logo-label">Archive</span>
    </div>
    <h1>지난 호 보기</h1>
    <p class="subtitle">매일 아침 발행되는 AI 뉴스레터 아카이브입니다.</p>
    <div class="issues">
{items}    </div>
  </div>
</body>
</html>'''


def send_to_google_chat(page_url: str):
    """Google Chat 웹훅으로 뉴스레터 링크 발송"""
    import urllib.request

    card = {
        "cardsV2": [{
            "cardId": "ai-briefing",
            "card": {
                "header": {
                    "title": f"📰 오늘의 AI 브리핑",
                    "subtitle": f"{DATE_STR} {DATE_DAY} · Issue #{ISSUE_NUM:03d}",
                },
                "sections": [{
                    "widgets": [
                        {
                            "textParagraph": {
                                "text": "오늘의 AI 뉴스레터가 준비되었습니다!"
                            }
                        },
                        {
                            "buttonList": {
                                "buttons": [
                                    {
                                        "text": "📰 뉴스레터 읽기",
                                        "onClick": {"openLink": {"url": page_url}}
                                    },
                                    {
                                        "text": "📂 지난 호 보기",
                                        "onClick": {"openLink": {"url": f"{PAGES_BASE_URL}/index.html"}}
                                    }
                                ]
                            }
                        }
                    ]
                }]
            }
        }]
    }

    data = json.dumps(card).encode("utf-8")
    req = urllib.request.Request(
        GOOGLE_CHAT_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print(f"✅ Google Chat 알림 발송 완료 (HTTP {resp.status})")


def main():
    print(f"🚀 4lynx AI Daily Briefing — {DATE_STR} {DATE_DAY}")
    print("=" * 50)

    # 1. 뉴스 수집
    print("\n📡 AI 뉴스 수집 중...")
    news = fetch_ai_news()
    print(f"   ✅ 메인 {len(news['main_stories'])}건, 한줄 {len(news['quick_bites'])}건, 용어 {len(news['glossary'])}건")

    # 2. HTML 생성 → docs/ 에 저장
    print("\n🎨 HTML 생성 중...")
    html = build_html(news)
    filename = f"{DATE_FILE}.html"
    (DOCS_DIR / filename).write_text(html, encoding="utf-8")
    print(f"   ✅ docs/{filename}")

    # 3. 아카이브 인덱스 업데이트
    print("\n📂 아카이브 인덱스 업데이트...")
    index_html = build_index()
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("   ✅ docs/index.html")

    # 4. Google Chat 알림
    page_url = f"{PAGES_BASE_URL}/{filename}"
    print(f"\n💬 Google Chat 알림 발송... ({page_url})")
    send_to_google_chat(page_url)

    print("\n" + "=" * 50)
    print(f"✅ 완료! {page_url}")


if __name__ == "__main__":
    main()
