PUBLIC_MODE = True  # ✅ True면 비번 없이 공개 / False면 비번 필요

import streamlit as st
import random
import os
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="JLPT 단어 퀴즈", page_icon="🧠")

# -------------------------
# (선택) 비밀번호 잠금: 기존 앱과 동일하게 쓰고 싶으면 ON
# - Secrets에 APP_TOKEN이 있으면 잠금 적용
# - 없으면(또는 끄고 싶으면) 아래 블록 통째로 주석 처리
# -------------------------
APP_TOKEN = st.secrets.get("APP_TOKEN")

if not PUBLIC_MODE:
    APP_TOKEN = st.secrets.get("APP_TOKEN")
    if not APP_TOKEN:
        st.error("관리자 설정 필요: Secrets에 APP_TOKEN을 추가하세요.")
        st.stop()

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
        
# -------------------------
# 1) 헤더 + 로그아웃(단어퀴즈만)
# -------------------------
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🧠 JLPT 레벨별 단어 퀴즈")
with col2:
    if APP_TOKEN and st.button("로그아웃"):
        st.session_state.vocab_unlocked = False
        st.session_state.pop("vocab_quiz_ids", None)
        st.session_state.pop("vocab_submitted", None)
        st.session_state.pop("vocab_saved_once", None)
        keys_to_remove = [k for k in st.session_state.keys() if str(k).startswith("vocab_pick_")]
        for k in keys_to_remove:
            st.session_state.pop(k, None)
        st.rerun()

# -------------------------
# 2) 응시자 정보
# -------------------------
st.subheader("응시자 정보")
a, b = st.columns(2)
with a:
    real_name = st.text_input("이름", key="vocab_real_name")
with b:
    nickname = st.text_input("닉네임", key="vocab_nickname")

if not real_name.strip() or not nickname.strip():
    st.info("이름과 닉네임을 입력하면 퀴즈를 시작할 수 있어요.")
    st.stop()

# -------------------------
# 3) 단어 데이터 (레벨별)
# - quiz_type: "meaning" (뜻 고르기), "reading"(읽기 고르기)
# -------------------------
VOCAB_SETS = {
    "N5": [
        {"id": 5001, "word": "学校", "reading": "がっこう", "meaning_ko": "학교", "quiz_type": "meaning",
         "choices": ["학교", "회사", "병원", "공원"], "answer_index": 0},
        {"id": 5002, "word": "先生", "reading": "せんせい", "meaning_ko": "선생님", "quiz_type": "meaning",
         "choices": ["학생", "선생님", "의사", "직원"], "answer_index": 1},
        {"id": 5003, "word": "電車", "reading": "でんしゃ", "meaning_ko": "전철", "quiz_type": "meaning",
         "choices": ["버스", "전철", "택시", "자전거"], "answer_index": 1},
        {"id": 5004, "word": "飲む", "reading": "のむ", "meaning_ko": "마시다", "quiz_type": "meaning",
         "choices": ["먹다", "마시다", "자다", "가다"], "answer_index": 1},
        {"id": 5005, "word": "高い", "reading": "たかい", "meaning_ko": "비싸다/높다", "quiz_type": "meaning",
         "choices": ["싸다", "넓다", "비싸다/높다", "느리다"], "answer_index": 2},
        {"id": 5006, "word": "食べる", "reading": "たべる", "meaning_ko": "먹다", "quiz_type": "meaning",
         "choices": ["먹다", "사다", "보다", "타다"], "answer_index": 0},
        {"id": 5007, "word": "友達", "reading": "ともだち", "meaning_ko": "친구", "quiz_type": "meaning",
         "choices": ["가족", "친구", "동료", "손님"], "answer_index": 1},
        {"id": 5008, "word": "見る", "reading": "みる", "meaning_ko": "보다", "quiz_type": "meaning",
         "choices": ["보다", "듣다", "말하다", "쓰다"], "answer_index": 0},
        {"id": 5009, "word": "小さい", "reading": "ちいさい", "meaning_ko": "작다", "quiz_type": "meaning",
         "choices": ["가깝다", "작다", "뜨겁다", "늦다"], "answer_index": 1},
        {"id": 5010, "word": "早い", "reading": "はやい", "meaning_ko": "빠르다/이르다", "quiz_type": "meaning",
         "choices": ["늦다", "빠르다/이르다", "무겁다", "약하다"], "answer_index": 1},
        {"id": 5011, "word": "大丈夫", "reading": "だいじょうぶ", "meaning_ko": "괜찮다", "quiz_type": "meaning",
         "choices": ["괜찮다", "위험하다", "불편하다", "복잡하다"], "answer_index": 0},
        {"id": 5012, "word": "会社", "reading": "かいしゃ", "meaning_ko": "회사", "quiz_type": "meaning",
         "choices": ["학교", "회사", "은행", "병원"], "answer_index": 1},
    ],
    "N4": [
        {"id": 4001, "word": "経験", "reading": "けいけん", "meaning_ko": "경험", "quiz_type": "meaning",
         "choices": ["경험", "기회", "계획", "기억"], "answer_index": 0},
        {"id": 4002, "word": "必要", "reading": "ひつよう", "meaning_ko": "필요", "quiz_type": "meaning",
         "choices": ["필요", "가능", "유명", "특별"], "answer_index": 0},
        {"id": 4003, "word": "確認", "reading": "かくにん", "meaning_ko": "확인", "quiz_type": "meaning",
         "choices": ["예약", "확인", "연락", "상담"], "answer_index": 1},
        {"id": 4004, "word": "連絡", "reading": "れんらく", "meaning_ko": "연락", "quiz_type": "meaning",
         "choices": ["연락", "연습", "연장", "연구"], "answer_index": 0},
        {"id": 4005, "word": "案内", "reading": "あんない", "meaning_ko": "안내", "quiz_type": "meaning",
         "choices": ["안내", "설명", "약속", "응원"], "answer_index": 0},
        {"id": 4006, "word": "準備", "reading": "じゅんび", "meaning_ko": "준비", "quiz_type": "meaning",
         "choices": ["준비", "정리", "청소", "이동"], "answer_index": 0},
        {"id": 4007, "word": "簡単", "reading": "かんたん", "meaning_ko": "간단", "quiz_type": "meaning",
         "choices": ["복잡", "간단", "곤란", "불안"], "answer_index": 1},
        {"id": 4008, "word": "安心", "reading": "あんしん", "meaning_ko": "안심", "quiz_type": "meaning",
         "choices": ["긴장", "안심", "의심", "불만"], "answer_index": 1},
        {"id": 4009, "word": "心配", "reading": "しんぱい", "meaning_ko": "걱정", "quiz_type": "meaning",
         "choices": ["걱정", "기대", "감동", "노력"], "answer_index": 0},
        {"id": 4010, "word": "大切", "reading": "たいせつ", "meaning_ko": "소중함/중요", "quiz_type": "meaning",
         "choices": ["유명", "특별", "소중함/중요", "자유"], "answer_index": 2},
        {"id": 4011, "word": "予定", "reading": "よてい", "meaning_ko": "예정", "quiz_type": "meaning",
         "choices": ["예약", "예정", "요금", "요리"], "answer_index": 1},
        {"id": 4012, "word": "久しぶり", "reading": "ひさしぶり", "meaning_ko": "오랜만", "quiz_type": "meaning",
         "choices": ["처음", "자주", "오랜만", "급히"], "answer_index": 2},
    ],
    "N3(맛보기)": [
        {"id": 3001, "word": "改善", "reading": "かいぜん", "meaning_ko": "개선", "quiz_type": "meaning",
         "choices": ["확대", "개선", "감소", "중단"], "answer_index": 1},
        {"id": 3002, "word": "影響", "reading": "えいきょう", "meaning_ko": "영향", "quiz_type": "meaning",
         "choices": ["영향", "인상", "예상", "현상"], "answer_index": 0},
        {"id": 3003, "word": "判断", "reading": "はんだん", "meaning_ko": "판단", "quiz_type": "meaning",
         "choices": ["상담", "판단", "분담", "부담"], "answer_index": 1},
        {"id": 3004, "word": "維持", "reading": "いじ", "meaning_ko": "유지", "quiz_type": "meaning",
         "choices": ["유지", "위기", "의지", "유리"], "answer_index": 0},
        {"id": 3005, "word": "確認する", "reading": "かくにんする", "meaning_ko": "확인하다", "quiz_type": "meaning",
         "choices": ["예약하다", "확인하다", "준비하다", "연습하다"], "answer_index": 1},
        {"id": 3006, "word": "増える", "reading": "ふえる", "meaning_ko": "늘다", "quiz_type": "meaning",
         "choices": ["줄다", "늘다", "끊다", "바꾸다"], "answer_index": 1},
        {"id": 3007, "word": "減る", "reading": "へる", "meaning_ko": "줄다", "quiz_type": "meaning",
         "choices": ["줄다", "늘다", "피하다", "지키다"], "answer_index": 0},
        {"id": 3008, "word": "間に合う", "reading": "まにあう", "meaning_ko": "시간에 맞다", "quiz_type": "meaning",
         "choices": ["늦다", "시간에 맞다", "미루다", "기다리다"], "answer_index": 1},
        {"id": 3009, "word": "見直す", "reading": "みなおす", "meaning_ko": "재검토하다", "quiz_type": "meaning",
         "choices": ["재검토하다", "계속하다", "중단하다", "확정하다"], "answer_index": 0},
        {"id": 3010, "word": "結果", "reading": "けっか", "meaning_ko": "결과", "quiz_type": "meaning",
         "choices": ["경과", "효과", "결과", "변화"], "answer_index": 2},
        {"id": 3011, "word": "対策", "reading": "たいさく", "meaning_ko": "대책", "quiz_type": "meaning",
         "choices": ["대책", "대상", "대기", "대우"], "answer_index": 0},
        {"id": 3012, "word": "提出", "reading": "ていしゅつ", "meaning_ko": "제출", "quiz_type": "meaning",
         "choices": ["제안", "제출", "제한", "제작"], "answer_index": 1},
    ],
}

# -------------------------
# 4) 레벨 선택
# -------------------------
st.subheader("레벨 선택")
level = st.selectbox("풀 레벨을 선택하세요", list(VOCAB_SETS.keys()), key="vocab_level")

VOCABS = VOCAB_SETS[level]

if len(VOCABS) < 10:
    st.warning("선택한 레벨의 문제가 10개 미만입니다. 데이터(단어)를 더 추가해 주세요.")
    st.stop()

# -------------------------
# 5) 10문제 세트 고정
# -------------------------
if "vocab_quiz_ids" not in st.session_state:
    st.session_state.vocab_quiz_ids = None
if "vocab_submitted" not in st.session_state:
    st.session_state.vocab_submitted = False
if "vocab_saved_once" not in st.session_state:
    st.session_state.vocab_saved_once = False

if st.button("새 10문제 시작", key="vocab_start_btn"):
    st.session_state.vocab_quiz_ids = random.sample([q["id"] for q in VOCABS], 10)
    st.session_state.vocab_submitted = False
    st.session_state.vocab_saved_once = False

    # 이전 선택값 제거
    for q in VOCABS:
        st.session_state.pop(f"vocab_pick_{q['id']}", None)

    st.rerun()

if st.session_state.vocab_quiz_ids is None:
    st.info("버튼을 눌러 10문제를 시작하세요.")
    st.stop()

id_to_q = {q["id"]: q for q in VOCABS}
quiz = [id_to_q[qid] for qid in st.session_state.vocab_quiz_ids]

# -------------------------
# 6) 문제 표시 + 제출
# -------------------------
with st.form("vocab_form"):
    user_answers = {}

    for i, q in enumerate(quiz, start=1):
        st.markdown(f"### Q{i}")

        if q.get("quiz_type") == "reading":
            question_text = f"**{q['word']}** 의 읽기는?"
            choices = q["choices"]
            correct = choices[q["answer_index"]]
        else:
            question_text = f"**{q['word']}（{q['reading']}）** 의 뜻은?"
            choices = q["choices"]
            correct = choices[q["answer_index"]]

        st.write(question_text)

        user_answers[q["id"]] = st.radio(
            "선택",
            choices,
            index=None,
            key=f"vocab_pick_{q['id']}",
        )
        st.divider()

    submitted = st.form_submit_button("제출 & 채점")

# -------------------------
# 7) 채점 + 저장
# -------------------------
if submitted:
    st.session_state.vocab_submitted = True

if st.session_state.vocab_submitted:
    if any(ans is None for ans in user_answers.values()):
        st.warning("선택하지 않은 문제가 있습니다. 모두 선택한 뒤 제출해 주세요.")
        st.stop()

    score = 0
    st.subheader("결과")

    wrong_list = []

    for i, q in enumerate(quiz, start=1):
        choices = q["choices"]
        correct = choices[q["answer_index"]]
        picked = user_answers[q["id"]]

        if picked == correct:
            score += 1
            st.success(f"Q{i} 정답 ✅ ({picked})")
        else:
            st.error(f"Q{i} 오답 ❌ (내 답: {picked} / 정답: {correct})")
            wrong_list.append(f"{q['word']}({q['reading']})")

    st.write(f"## 점수: {score} / 10")
    if wrong_list:
        st.info("📝 오답 단어: " + ", ".join(wrong_list))
    else:
        st.success("🎉 전부 정답! 아주 좋아요.")

    # 결과 저장(레벨 포함) - 한 번만
    if not st.session_state.vocab_saved_once:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "timestamp": timestamp,
            "type": "vocab",
            "level": level,
            "real_name": real_name.strip(),
            "nickname": nickname.strip(),
            "score": score,
            "total": 10,
            "wrong_words": ", ".join(wrong_list),
        }

        csv_path = "vocab_results.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        st.session_state.vocab_saved_once = True
        st.success("✅ 결과가 저장되었습니다 (vocab_results.csv)")

    if st.button("🔄 같은 문제 다시 풀기", key="vocab_retry"):
        for q in quiz:
            st.session_state.pop(f"vocab_pick_{q['id']}", None)
        st.session_state.vocab_submitted = False
        st.rerun()
