import os
import time
import re
from google import genai
from github import Github
from pathlib import Path

# ==========================================================
# 1. 환경 설정 및 초기화
# ==========================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")  # int 변환은 main 내부에서 안전하게 처리

# 분석 대상 확장자
TARGET_EXTENSIONS = ('.py', '.js', '.java', '.cpp', '.c', '.ts', '.go', '.rs', '.kt', '.swift')

client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================================
# 2. 스마트 모델 선택 (Dynamic Model Selection)
# ==========================================================
def get_latest_flash_model():
    """
    현재 API 키로 사용 가능한 모델 중 가장 최신의 'Flash' 모델을 자동으로 찾습니다.
    예: gemini-2.5-flash > gemini-2.0-flash > gemini-1.5-flash 순으로 우선순위
    """
    try:
        models = client.models.list()
        # 'flash'가 포함된 모델만 필터링
        flash_models = [m.name for m in models if 'flash' in m.name.lower()]

        if not flash_models:
            # Flash 모델이 없으면 Pro 모델이라도 사용
            print("⚠️ 'Flash' model not found. Falling back to default.")
            return "gemini-2.0-flash"  # Fallback (혹은 gemini-pro)

        # 버전 숫자가 높은 순서대로 정렬 (예: 2.5 -> 2.0 -> 1.5)
        # 모델명 예시: models/gemini-1.5-flash
        def version_key(name):
            match = re.search(r'(\d+\.\d+)', name)
            return float(match.group(1)) if match else 0.0

        latest_model = sorted(flash_models, key=version_key, reverse=True)[0]

        # 'models/' 접두사 제거 (generate_content 함수는 접두사 없이도 동작하지만 깔끔하게)
        if latest_model.startswith("models/"):
            latest_model = latest_model.replace("models/", "")

        print(f"✨ Auto-selected best model: {latest_model}")
        return latest_model

    except Exception as e:
        print(f"⚠️ Failed to auto-detect model: {e}. Using fallback.")
        return "gemini-2.0-flash"


# ==========================================================
# 3. 메인 로직
# ==========================================================
def main():
    if not GEMINI_API_KEY or not GITHUB_TOKEN:
        print("❌ Error: Missing API Keys (GEMINI_API_KEY or GITHUB_TOKEN).")
        return

    # 모델 자동 선택
    MODEL_NAME = get_latest_flash_model()

    # 2026년 기준, 최신 모델에 맞는 시스템 프롬프트
    system_instruction = """
    당신은 GitHub PR에 코멘트를 남기는 아주 친한 동료 개발자입니다 🐣
    말투는 귀엽고 말랑하지만, 코드가 틀렸다면 그건 분명하게 짚습니다.
    
    [기본 규칙]
    - 반드시 한글로 작성합니다 🇰🇷
    - PR 코멘트로 바로 써도 자연스러운 분량만 작성합니다.
    - 코드 보면서 든 감상 위주로 작성합니다.
    - '$'로 시작해서 '$'로 끝나는 표현은 절대 사용하지 않습니다 ❌
      - 단, 시간 복잡도의 경우 'O(logN)'과 같은 plain text로 표현합니다.
    
    [톤 & 분위기]
    - 전체적으로 귀엽고 편한 말투 ☁️
    - 잘한 부분은 먼저 짚어줍니다 ✨
    - 하지만 논리적으로 틀린 부분은 돌려 말하지 않고 바로 언급합니다.
    - “이 부분은 시간 초과가 발생할 수 있어요”, “여기서는 메모리 초과가 발생할 수 있어요” 처럼 부드럽지만 명확하게 말합니다.
    - 이모지는 적극적으로 사용합니다 🐥👍
    - 질문, 대화 유도 문장은 절대 사용하지 않습니다 🚫
    
    [틀린 코드 언급 규칙]
    - 결과가 틀리거나 접근이 잘못된 경우 반드시 언급합니다.
    - 감정적인 표현 없이, 사실 위주로 짧게 설명합니다.
    - 비난하지 않고, 코드 기준으로만 이야기합니다.
    
    [리뷰 흐름]
    1. 👍 잘 짠 부분이나 의도는 먼저 인정
    2. ❗ 핵심적으로 잘못된 부분 한 줄 요약
    3. 🔍 왜 문제가 되는지 짧게 설명
    4. 💬 전체 총평 (차분하게 마무리)
    
    [중요]
    - 현재 파일 하나만 기준으로 리뷰합니다.
    - 대화를 이어가려는 문장은 작성하지 않습니다.
    """

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction
    )

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pr = repo.get_pull(int(PR_NUMBER))

    print(f"🚀 Starting Review on {REPO_NAME} PR #{PR_NUMBER} using [{MODEL_NAME}]")

    files = pr.get_files()
    files_to_review = [f for f in files if f.filename.endswith(TARGET_EXTENSIONS) and f.status != "removed"]

    if not files_to_review:
        print("ℹ️ No reviewable code files found.")
        return

    for file in files_to_review:
        path_parts = Path(file.filename).parts
        site_name = path_parts[0].upper() if len(path_parts) > 1 else "알 수 없음"

        print(f"🔍 Analyzing: {file.filename} (Site: {site_name})...")

        try:
            # 파일 내용 로드
            content = repo.get_contents(file.filename, ref=pr.head.sha).decoded_content.decode('utf-8')

            prompt = f"""
            아래는 {site_name} 사이트의 알고리즘 문제 풀이 파일입니다 🧩
            이 코드를 처음 보는 동료 개발자라고 생각하고,
            PR에 남길 짧은 코멘트를 작성해주세요.
            
            사이트 정보:
            이 문제는 **{site_name}** 플랫폼의 문제입니다. (예: BOJ는 백준, PGS는 프로그래머스 등)
            
            파일명:
            {file.filename}
            
            파일 내용:
            ```{file.filename.split('.')[-1]}
            {content}
            ```
            
            작성 가이드:
            - 잘한 점이 있다면 먼저 언급하기 ✨
            - 코드가 문제의 의도와 맞지 않다면 반드시 짚기 ❗
            - 코드 기준으로 평가
            - 질문, 제안, 대화 유도 문장은 작성하지 말 것 🚫
            - 전체 분량은 가볍게 유지
            
            아래 형식을 꼭 지켜주세요 👇
            
            🧠 문제 핵심
            - (이 문제의 요지를 귀엽게 한 줄)
            - (이 문제가 의도한 알고리즘 또는 풀이 방식 한 줄)
            
            🚀 풀이 접근
            - (현재 코드가 어떤 방향으로 풀고 있는지, 어떤 알고리즘을 썼는지)
            
            !중요! 코드의 방향이 문제 의도와 명백히 다른 경우 아래 내용을 출력하지 않습니다.
            
            ✨ 구현 포인트
            - (보면서 “오 👀” 했던 부분)
            
            🤏 살짝 아쉬운 점
            - (있다면 가볍게 한 두 줄)
            
            !중요! 코드는 항상 문제를 해결한 코드입니다.  "코드의 결과값은 항상 반드시 문제의 답과 일치합니다. 즉 정확한 결과값을 도출합니다." 하지만 문제 의도와 코드 내용이 아예 다르다면 아래 내용을 출력합니다.
            
            ❗ 문제되는 부분
            - (틀리거나 위험한 핵심 포인트)
            
            💬 총평
            - (짧은 응원 멘트로 마무리)
            
            !중요! 이후에는 "절대로" 어떠한 것도 추가하지 않습니다.
            """

            # API 호출
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={'system_instruction': system_instruction}
            )

            # PR 코멘트 작성
            comment_body = f"## {file.filename.split('.')[0]}번 문제!\n\n{response.text}"
            pr.create_issue_comment(comment_body)
            print(f"✅ Posted comment for {file.filename}")

            # Rate Limit 관리 (Flash 모델도 안전하게 1초 대기)
            time.sleep(1)

        except Exception as e:
            print(f"❌ Error processing {file.filename}: {e}")


if __name__ == "__main__":
    main()
