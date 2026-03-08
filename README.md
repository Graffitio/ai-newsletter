# 4lynx AI Daily Briefing — 설정 가이드

> 매일 아침 7시, AI 뉴스레터가 자동으로 만들어져서 Google Chat에 도착합니다.
> 아래 순서대로 따라하면 끝!

---

## 이게 뭔가요?

매일 아침 이런 일이 **자동으로** 일어납니다:

1. AI가 그날의 최신 AI 뉴스를 검색합니다
2. 4lynx 브랜드 디자인의 뉴스레터 웹페이지를 만듭니다
3. 인터넷에 자동 게시합니다
4. Google Chat에 **"뉴스레터 읽기"** 버튼이 달린 알림이 옵니다
5. 버튼을 누르면 브라우저에서 바로 예쁜 뉴스레터가 열립니다

**월 비용: 약 $1.2 (나머지 전부 무료)**

---

## 준비물

시작하기 전에 아래 3개가 필요합니다:

| 준비물 | 어디서? | 비용 |
|--------|---------|------|
| GitHub 계정 | [github.com](https://github.com) | 무료 |
| Anthropic API 키 | [console.anthropic.com](https://console.anthropic.com) | 사용한 만큼 (~$1.2/월) |
| Google Chat 스페이스 | 사내 Google Chat | 무료 |

---

## 설정하기 (총 6단계)

### 1단계: Anthropic API 키 발급받기

이 키가 있어야 AI가 뉴스를 수집할 수 있습니다.

1. [console.anthropic.com](https://console.anthropic.com) 에 접속합니다
2. 회원가입 또는 로그인합니다
3. 왼쪽 메뉴에서 **API Keys** 를 클릭합니다
4. **Create Key** 버튼을 누릅니다
5. 이름을 입력합니다 (예: `ai-newsletter`)
6. 생성된 키를 **복사해서 어딘가에 저장**합니다
   - `sk-ant-` 로 시작하는 긴 문자열입니다
   - ⚠️ 이 키는 한 번만 보여주므로 꼭 저장하세요!

---

### 2단계: Google Chat 웹훅 만들기

이 웹훅이 있어야 뉴스레터 알림이 Chat으로 옵니다.

1. **Google Chat** 을 엽니다
2. 뉴스레터를 받을 **스페이스(그룹방)** 에 들어갑니다
   - 새로 만들어도 되고, 기존 스페이스를 써도 됩니다
   - 예: "AI 뉴스레터" 라는 이름으로 스페이스 생성
3. 스페이스 이름을 클릭합니다 (상단에 있는 스페이스명)
4. **앱 및 통합** 을 클릭합니다
5. **웹훅 관리** 를 클릭합니다
6. **웹훅 추가** 를 누릅니다
7. 이름에 `AI Daily Briefing` 입력 → **저장**
8. 생성된 URL을 **복사해서 저장**합니다
   - `https://chat.googleapis.com/v1/spaces/...` 로 시작하는 긴 URL입니다

---

### 3단계: GitHub에 저장소 만들기

1. [github.com](https://github.com) 에 로그인합니다
2. 오른쪽 상단 **+** 버튼 → **New repository** 클릭
3. 아래처럼 입력합니다:
   - **Repository name**: `ai-newsletter`
   - **Public** 선택 (GitHub Pages 무료 사용을 위해)
   - 나머지는 건드리지 않습니다
4. **Create repository** 클릭

---

### 4단계: 파일 업로드하기

1. 다운로드 받은 `4lynx-ai-newsletter.zip` 파일의 압축을 풉니다
2. 방금 만든 GitHub 저장소 페이지에서:
   - **uploading an existing file** 링크를 클릭합니다
   - 압축 푼 폴더 **안의 파일들을** 전부 드래그해서 올립니다:
     - `.github/` 폴더
     - `docs/` 폴더
     - `templates/` 폴더
     - `generate.py`
     - `requirements.txt`
     - `.gitignore`
     - `README.md`
   - 아래 **Commit changes** 버튼을 누릅니다

> 💡 **팁**: 파일 업로드가 어려우면, GitHub Desktop 앱을 설치하면 훨씬 쉽습니다.

---

### 5단계: 비밀 키 등록하기

API 키와 웹훅 URL을 GitHub에 안전하게 저장합니다.

1. 저장소 페이지에서 상단 **Settings** 탭을 클릭합니다
2. 왼쪽 메뉴에서 **Secrets and variables** → **Actions** 를 클릭합니다
3. **New repository secret** 버튼을 누릅니다
4. 첫 번째 시크릿 등록:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: 1단계에서 복사한 API 키 붙여넣기
   - **Add secret** 클릭
5. 다시 **New repository secret** 버튼을 누릅니다
6. 두 번째 시크릿 등록:
   - **Name**: `GOOGLE_CHAT_WEBHOOK`
   - **Secret**: 2단계에서 복사한 웹훅 URL 붙여넣기
   - **Add secret** 클릭

등록이 끝나면 이렇게 2개가 보여야 합니다:

```
ANTHROPIC_API_KEY      Updated just now
GOOGLE_CHAT_WEBHOOK    Updated just now
```

---

### 6단계: GitHub Pages 켜기

이걸 켜야 뉴스레터가 웹페이지로 보입니다.

1. 저장소 **Settings** 탭 (이미 들어가 있으면 그대로)
2. 왼쪽 메뉴에서 **Pages** 를 클릭합니다
3. **Source** 항목에서:
   - **Deploy from a branch** 선택
   - Branch: **gh-pages** 선택
   - 폴더: **/ (root)** 선택
   - **Save** 클릭

> ⚠️ `gh-pages` 브랜치가 아직 안 보일 수 있습니다.
> 그럴 경우 아래 "테스트 실행"을 먼저 한 번 하면 자동으로 생깁니다.
> 그 후 다시 이 단계로 돌아와서 설정하세요.

---

## 테스트 실행해 보기

설정이 다 됐으면 한 번 돌려봅시다!

1. 저장소 상단 **Actions** 탭을 클릭합니다
2. 왼쪽에서 **4lynx AI Daily Briefing** 을 클릭합니다
3. 오른쪽 **Run workflow** 버튼 → **Run workflow** 클릭
4. 1~2분 기다립니다
5. 초록색 체크 ✅ 가 뜨면 성공!

성공하면:
- Google Chat 스페이스에 알림 카드가 도착합니다
- **"뉴스레터 읽기"** 버튼을 누르면 브라우저에서 뉴스레터가 열립니다

---

## 잘 안 될 때

| 증상 | 해결 방법 |
|------|----------|
| Actions에 빨간 ❌ 가 뜸 | 클릭해서 에러 메시지 확인 → 보통 API 키가 잘못 입력된 경우 |
| Chat에 알림이 안 옴 | 웹훅 URL이 맞는지 확인 → 스페이스에서 웹훅을 다시 만들어보세요 |
| 링크 클릭해도 404 에러 | 6단계(GitHub Pages)를 다시 확인 → `gh-pages` 브랜치 선택 |
| `gh-pages` 브랜치가 안 보임 | 테스트 실행을 먼저 한 번 하면 자동으로 생깁니다 |

그래도 안 되면 Actions 탭에서 실패한 실행을 클릭 → 에러 로그를 캡처해서 공유해 주세요.

---

## 이후에는?

**아무것도 안 해도 됩니다!** 매일 아침 7시(한국시간)에 자동으로 돌아갑니다.

가끔 확인하면 좋은 것:
- [Anthropic Console](https://console.anthropic.com) 에서 API 사용량 확인 (월 $1~2 수준)
- Google Chat 스페이스에 매일 알림이 잘 오는지 확인

---

## 변경하고 싶을 때

| 바꾸고 싶은 것 | 어떻게 |
|---------------|--------|
| 발송 시간 변경 | `.github/workflows/daily-briefing.yml` 파일에서 `cron: '0 22 * * *'` 수정 |
| 주말에 안 보내기 | 위 cron을 `cron: '0 22 * * 0-4'` 로 변경 (월~금만) |
| 뉴스 주제 변경 | `generate.py` 안의 프롬프트 내용 수정 |

> **cron 시간 참고**: UTC 기준이라 한국시간에서 9시간을 빼야 합니다.
> 예: 한국 아침 7시 = UTC 22시(전날) = `0 22 * * *`
> 예: 한국 아침 8시 30분 = UTC 23시 30분(전날) = `30 23 * * *`

---

## 파일 구조 (참고용)

```
ai-newsletter/
├── .github/workflows/
│   └── daily-briefing.yml   ← 매일 자동 실행 설정
├── docs/                    ← 뉴스레터 웹페이지 (자동 생성됨)
│   ├── index.html           ← 지난 호 목록
│   └── 2026-03-08.html      ← 오늘 뉴스레터
├── templates/
│   └── logo.png             ← 4lynx 로고
├── generate.py              ← 뉴스레터 생성 프로그램
├── requirements.txt         ← 필요한 라이브러리 목록
└── README.md                ← 이 파일
```