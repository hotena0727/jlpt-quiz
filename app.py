import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="JLPT 10문제 퀴즈")

# -------------------------
# 0) 비밀번호(Secrets)
# -------------------------
APP_TOKEN = st.secrets.get("APP_TOKEN")
if not APP_TOKEN:
    st.error("관리자 설정 필요: Streamlit Cloud의 Secrets에 APP_TOKEN을 추가하세요.")
    st.stop()

# -------------------------
# 1) 잠금 상태
# -------------------------
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if not st.session_state.unlocked:
    st.title("🔒 비밀번호가 필요합니다")
    token = st.text_input("접속 비밀번호", type="password")
    if st.button("입장"):
        if token == APP_TOKEN:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# 로그인 후 화면
col1, col2 = st.columns([1, 1])
with col1:
    st.title("JLPT 10문제 퀴즈")
with col2:
    if st.button("로그아웃"):
        st.session_state.unlocked = False
        # 선택/점수 상태도 초기화하고 싶으면 아래 2줄도 켜기
        st.session_state.pop("quiz_ids", None)
        st.session_state.pop("submitted", None)
        st.rerun()

st.subheader("응시자 정보")

colA, colB = st.columns(2)
with colA:
    real_name = st.text_input("이름", key="real_name")
with colB:
    nickname = st.text_input("닉네임", key="nickname")

if not real_name.strip() or not nickname.strip():
    st.info("이름과 닉네임을 입력하면 퀴즈를 시작할 수 있어요.")
    st.stop()

# -------------------------
# 2) 문제 데이터
# -------------------------
QUESTIONS = [
    {"id": 1, "prompt": "（　）に入るものは？", "sentence": "今日は時間が（　）、勉強できませんでした。", "choices": ["あって", "なくて", "よくて", "こわくて"], "answer_index": 1, "explanation": "「時間がなくて」= 시간이 없어서."},
    {"id": 2, "prompt": "（　）に入るものは？", "sentence": "雨が降っている（　）、出かけません。", "choices": ["ので", "のに", "からこそ", "までに"], "answer_index": 0, "explanation": "「ので」= 이유/원인."},
    {"id": 3, "prompt": "（　）に入るものは？", "sentence": "説明を聞いた（　）、よく分かりません。", "choices": ["のに", "ので", "から", "まで"], "answer_index": 0, "explanation": "「のに」= 했는데도."},
    {"id": 4, "prompt": "（　）に入るものは？", "sentence": "駅まで歩く（　）、10分ぐらいです。", "choices": ["と", "なら", "ので", "のに"], "answer_index": 0, "explanation": "「～と」= 조건(일반적 결과)."},
    {"id": 5, "prompt": "（　）に入るものは？", "sentence": "疲れている（　）、今日は早く寝ます。", "choices": ["から", "のに", "まで", "より"], "answer_index": 0, "explanation": "「から」= 이유."},
    {"id": 6, "prompt": "（　）に入るものは？", "sentence": "この店は安い（　）、料理もおいしい。", "choices": ["し", "ので", "のに", "まで"], "answer_index": 0, "explanation": "「し」= 이유/나열."},
    {"id": 7, "prompt": "（　）に入るものは？", "sentence": "急いで（　）と、間に合いません。", "choices": ["いく", "いかない", "いけば", "いった"], "answer_index": 1, "explanation": "「～ないと」= ~하지 않으면."},
    {"id": 8, "prompt": "（　）に入るものは？", "sentence": "電車が遅れた（　）、遅刻しました。", "choices": ["ため", "ところ", "ほど", "でも"], "answer_index": 0, "explanation": "「ため」= ~때문에."},
    {"id": 9, "prompt": "（　）に入るものは？", "sentence": "日本に行ったら、富士山を（　）みたいです。", "choices": ["みて", "みる", "みた", "みよう"], "answer_index": 1, "explanation": "「V辞書形＋みたい」= ~하고 싶다."},
    {"id": 10, "prompt": "（　）に入るものは？", "sentence": "この本は思ったより（　）。", "choices": ["むずかしい", "むずかしく", "むずかしかった", "むずかしさ"], "answer_index": 0, "explanation": "서술형은 형용사 기본형."},
    {"id": 11, "prompt": "（　）に入るものは？", "sentence": "彼は約束を（　）人だ。", "choices": ["やぶる", "やぶって", "やぶった", "やぶり"], "answer_index": 0, "explanation": "「約束を破る」= 약속을 어기다."},
    {"id": 12, "prompt": "（　）に入るものは？", "sentence": "この仕事は今日中に（　）必要があります。", "choices": ["おわって", "おわらせる", "おわらせた", "おわり"], "answer_index": 1, "explanation": "「終わらせる」= 끝내다(타동)."},
]

# -------------------------
# 3) 10문제 세트 고정
# -------------------------
if "quiz_ids" not in st.session_state:
    st.session_state.quiz_ids = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if st.button("새 10문제 시작"):
    st.session_state.quiz_ids = random.sample([q["id"] for q in QUESTIONS], 10)
    st.session_state.submitted = False
    st.session_state.saved_once = False
    # 라디오 선택값 리셋(이전 선택이 남는 걸 방지)
    for q in QUESTIONS:
        st.session_state.pop(f"pick_{q['id']}", None)
    st.rerun()

if st.session_state.quiz_ids is None:
    st.info("버튼을 눌러 10문제를 시작하세요.")
    st.stop()

id_to_q = {q["id"]: q for q in QUESTIONS}
quiz = [id_to_q[qid] for qid in st.session_state.quiz_ids]

# -------------------------
# 4) 문제 표시 + 제출
# -------------------------
with st.form("quiz_form"):
    user_answers = {}

    for i, q in enumerate(quiz, start=1):
        st.markdown(f"### Q{i}")
        st.write(q["prompt"])
        st.write(q["sentence"])
        user_answers[q["id"]] = st.radio(
            "선택",
            q["choices"],
            index=None,
            key=f"pick_{q['id']}",
        )
        st.divider()

    submitted = st.form_submit_button("제출 & 채점")

# -------------------------
# 5) 채점
# -------------------------
if submitted:
    st.session_state.submitted = True

if st.session_state.submitted:
    # 선택 안 한 문제 체크
    if any(ans is None for ans in user_answers.values()):
        st.warning("선택하지 않은 문제가 있습니다. 모두 선택한 뒤 제출해 주세요.")
        st.stop()

    score = 0
    st.subheader("결과")

    for i, q in enumerate(quiz, start=1):
        correct = q["choices"][q["answer_index"]]
        picked = user_answers[q["id"]]

        if picked == correct:
            score += 1
            st.success(f"Q{i} 정답 ✅ ({picked})")
        else:
            st.error(f"Q{i} 오답 ❌ (내 답: {picked} / 정답: {correct})")

        st.caption("해설: " + q["explanation"])

    st.write(f"## 점수: {score} / 10")
import os
import pandas as pd

# ---- 결과 저장 (CSV) ----
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

row = {
    "timestamp": timestamp,
    "real_name": real_name.strip(),
    "nickname": nickname.strip(),
    "score": score,
    "total": 10,
}

csv_path = "results.csv"

# 중복 저장 방지: 같은 세트에서 재실행/새로고침해도 한 번만 저장
if "saved_once" not in st.session_state:
    st.session_state.saved_once = False

if not st.session_state.saved_once:
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    st.session_state.saved_once = True
    st.success("✅ 결과가 저장되었습니다 (results.csv)")
else:
    st.info("이미 저장된 결과입니다.")

