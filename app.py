import streamlit as st
import random

st.set_page_config(page_title="JLPT 10문제 퀴즈")

APP_TOKEN = st.secrets["APP_TOKEN"]

# 잠금 상태 초기화
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

# 🔒 잠금 화면
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

# ✅ 로그인(잠금 해제) 후에만 보이는 화면
if st.button("로그아웃"):
    st.session_state.unlocked = False
    st.rerun()

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

st.title("JLPT 10문제 퀴즈")

if "quiz_ids" not in st.session_state:
    st.session_state.quiz_ids = None

if st.button("새 10문제 시작"):
    st.session_state.quiz_ids = random.sample([q["id"] for q in QUESTIONS], 10)

if st.session_state.quiz_ids is None:
    st.info("버튼을 눌러 10문제를 시작하세요.")
    st.stop()

id_to_q = {q["id"]: q for q in QUESTIONS}
quiz = [id_to_q[qid] for qid in st.session_state.quiz_ids]

with st.form("quiz_form"):
    user_answers = {}
    for i, q in enumerate(quiz, start=1):
        st.markdown(f"### Q{i}")
        st.write