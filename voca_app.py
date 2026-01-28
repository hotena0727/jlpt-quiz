import streamlit as st
import random
import os
import pandas as pd
from datetime import datetime
from collections import Counter

# =========================
# 설정
# =========================
PUBLIC_MODE = True  # ✅ True면 비번 없이 공개 / False면 비번 필요
RESULT_CSV = "vocab_results.csv"  # ✅ 단어퀴즈 전용 결과 파일(기존 앱과 분리)

st.set_page_config(page_title="JLPT 단어 퀴즈", page_icon="🧠", layout="centered")

# =========================
# 0) Secrets (선택)
# =========================
APP_TOKEN = st.secrets.get("APP_TOKEN")     # PUBLIC_MODE=False 일 때 사용
ADMIN_KEY = st.secrets.get("ADMIN_KEY")     # 선생님 전용 다운로드 URL키(선택)

# =========================
# 1) 잠금(선택)
# =========================
if not PUBLIC_MODE:
    if not APP_TOKEN:
        st.error("관리자 설정 필요: Secrets에 APP_TOKEN을 추가하세요.")
        st.stop()

    if "vocab_unlocked" not in st.session_state:
        st.session_state.vocab_unlocked = False

    if not st.session_state.vocab_unlocked:
        st.title("🔒 비밀번호가 필요합니다")
        token = st.text_input("접속 비밀번호", type="password")
        if st.button("입장"):
            if token == APP_TOKEN:
                st.session_state.vocab_unlocked = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
        st.stop()

# =========================
# 2) 헤더
# =========================
st.title("🧠 JLPT 레벨별 단어 퀴즈")
st.caption("레벨 선택 → 새 10문제 시작 → 제출 & 채점 → (리포트: 총평/오답노트)")

# =========================
# 3) (선택) 선생님 전용: URL 파라미터로만 관리자 모드 활성화
#     예) https://...streamlit.app/?admin=senwoo_admin_2026
# =========================
admin_mode = False
try:
    qs = st.query_params
    admin_value = qs.get("admin", "")
    if isinstance(admin_value, list):
        admin_value = admin_value[0] if admin_value else ""
    if ADMIN_KEY and admin_value and admin_value == ADMIN_KEY:
        admin_mode = True
except Exception:
    admin_mode = False

if admin_mode:
    st.divider()
    st.caption("※ 선생님 전용(관리자 모드)")
    if os.path.exists(RESULT_CSV):
        with open(RESULT_CSV, "rb") as f:
            st.download_button(
                "📥 결과 다운로드 (CSV)",
                f,
                file_name=RESULT_CSV,
                mime="text/csv",
            )
    else:
        st.info(f"아직 저장된 결과가 없습니다 ({RESULT_CSV} 없음).")
    st.divider()

# =========================
# 4) 응시자 정보
# =========================
st.subheader("응시자 정보")
a, b = st.columns(2)
with a:
    real_name = st.text_input("이름", key="vocab_real_name")
with b:
    nickname = st.text_input("닉네임", key="vocab_nickname")

if not real_name.strip() or not nickname.strip():
    st.info("이름과 닉네임을 입력하면 퀴즈를 시작할 수 있어요.")
    st.stop()

# =========================
# 5) 단어 데이터 (레벨별)
# - quiz_type: "meaning" (뜻 고르기), "reading"(읽기 고르기)
# - tag: (선택) 분야/테마. 총평에서 약점 분석에 사용
# =========================
VOCAB_SETS = {
    "N5": [
        {"id": 5001, "word": "学校", "reading": "がっこう", "meaning_ko": "학교", "quiz_type": "meaning", "tag": "학교/교육",
         "choices": ["학교", "회사", "병원", "공원"], "answer_index": 0},
        {"id": 5002, "word": "先生", "reading": "せんせい", "meaning_ko": "선생님", "quiz_type": "meaning", "tag": "학교/교육",
         "choices": ["학생", "선생님", "의사", "직원"], "answer_index": 1},
        {"id": 5003, "word": "電車", "reading": "でんしゃ", "meaning_ko": "전철", "quiz_type": "meaning", "tag": "교통",
         "choices": ["버스", "전철", "택시", "자전거"], "answer_index": 1},
        {"id": 5004, "word": "飲む", "reading": "のむ", "meaning_ko": "마시다", "quiz_type": "meaning", "tag": "행동",
         "choices": ["먹다", "마시다", "자다", "가다"], "answer_index": 1},
        {"id": 5005, "word": "高い", "reading": "たかい", "meaning_ko": "비싸다/높다", "quiz_type": "meaning", "tag": "형용사",
         "choices": ["싸다", "넓다", "비싸다/높다", "느리다"], "answer_index": 2},
        {"id": 5006, "word": "食べる", "reading": "たべる", "meaning_ko": "먹다", "quiz_type": "meaning", "tag": "행동",
         "choices": ["먹다", "사다", "보다", "타다"], "answer_index": 0},
        {"id": 5007, "word": "友達", "reading": "ともだち", "meaning_ko": "친구", "quiz_type": "meaning", "tag": "사람/관계",
         "choices": ["가족", "친구", "동료", "손님"], "answer_index": 1},
        {"id": 5008, "word": "見る", "reading": "みる", "meaning_ko": "보다", "quiz_type": "meaning", "tag": "행동",
         "choices": ["보다", "듣다", "말하다", "쓰다"], "answer_index": 0},
        {"id": 5009, "word": "小さい", "reading": "ちいさい", "meaning_ko": "작다", "quiz_type": "meaning", "tag": "형용사",
         "choices": ["가깝다", "작다", "뜨겁다", "늦다"], "answer_index": 1},
        {"id": 5010, "word": "早い", "reading": "はやい", "meaning_ko": "빠르다/이르다", "quiz_type": "meaning", "tag": "형용사",
         "choices": ["늦다", "빠르다/이르다", "무겁다", "약하다"], "answer_index": 1},
        {"id": 5011, "word": "大丈夫", "reading": "だいじょうぶ", "meaning_ko": "괜찮다", "quiz_type": "meaning", "tag": "감정/상태",
         "choices": ["괜찮다", "위험하다", "불편하다", "복잡하다"], "answer_index": 0},
        {"id": 5012, "word": "会社", "reading": "かいしゃ", "meaning_ko": "회사", "quiz_type": "meaning", "tag": "일/사회",
         "choices": ["학교", "회사", "은행", "병원"], "answer_index": 1},

        # ✅ (읽기 문제 예시 몇 개) - 필요 없으면 삭제 가능
        {"id": 5101, "word": "日本", "reading": "にほん", "meaning_ko": "일본", "quiz_type": "reading", "tag": "기본",
         "choices": ["にほん", "にっぽん", "にちほん", "にほんご"], "answer_index": 0},
        {"id": 5102, "word": "学生", "reading": "がくせい", "meaning_ko": "학생", "quiz_type": "reading", "tag": "학교/교육",
         "choices": ["がくせい", "がっせい", "がくぜい", "がっけい"], "answer_index": 0},
    ],
    "N4": [
        {"id": 4001, "word": "経験", "reading": "けいけん", "meaning_ko": "경험", "quiz_type": "meaning", "tag": "일/사회",
         "choices": ["경험", "기회", "계획", "기억"], "answer_index": 0},
        {"id": 4002, "word": "必要", "reading": "ひつよう", "meaning_ko": "필요", "quiz_type": "meaning", "tag": "기본",
         "choices": ["필요", "가능", "유명", "특별"], "answer_index": 0},
        {"id": 4003, "word": "確認", "reading": "かくにん", "meaning_ko": "확인", "quiz_type": "meaning", "tag": "업무/커뮤니케이션",
         "choices": ["예약", "확인", "연락", "상담"], "answer_index": 1},
        {"id": 4004, "word": "連絡", "reading": "れんらく", "meaning_ko": "연락", "quiz_type": "meaning", "tag": "업무/커뮤니케이션",
         "choices": ["연락", "연습", "연장", "연구"], "answer_index": 0},
        {"id": 4005, "word": "案内", "reading": "あんない", "meaning_ko": "안내", "quiz_type": "meaning", "tag": "업무/커뮤니케이션",
         "choices": ["안내", "설명", "약속", "응원"], "answer_index": 0},
        {"id": 4006, "word": "準備", "reading": "じゅんび", "meaning_ko": "준비", "quiz_type": "meaning", "tag": "행동",
         "choices": ["준비", "정리", "청소", "이동"], "answer_index": 0},
        {"id": 4007, "word": "簡単", "reading": "かんたん", "meaning_ko": "간단", "quiz_type": "meaning", "tag": "형용사",
         "choices": ["복잡", "간단", "곤란", "불안"], "answer_index": 1},
        {"id": 4008, "word": "安心", "reading": "あんしん", "meaning_ko": "안심", "quiz_type": "meaning", "tag": "감정/상태",
         "choices": ["긴장", "안심", "의심", "불만"], "answer_index": 1},
        {"id": 4009, "word": "心配", "reading": "しんぱい", "meaning_ko": "걱정", "quiz_type": "meaning", "tag": "감정/상태",
         "choices": ["걱정", "기대", "감동", "노력"], "answer_index": 0},
        {"id": 4010, "word": "大切", "reading": "たいせつ", "meaning_ko": "소중함/중요", "quiz_type": "meaning", "tag": "형용사",
         "choices": ["유명", "특별", "소중함/중요", "자유"], "answer_index": 2},
        {"id": 4011, "word": "予定", "reading": "よてい", "meaning_ko": "예정", "quiz_type": "meaning", "tag": "일정",
         "choices": ["예약", "예정", "요금", "요리"], "answer_index": 1},
        {"id": 4012, "word": "久しぶり", "reading": "ひさしぶり", "meaning_ko": "오랜만", "quiz_type": "meaning", "tag": "일상",
         "choices": ["처음", "자주", "오랜만", "급히"], "answer_index": 2},

        {"id": 4101, "word": "連絡", "reading": "れんらく", "meaning_ko": "연락", "quiz_type": "reading", "tag": "업무/커뮤니케이션",
         "choices": ["れんらく", "れんらっく", "れんらくう", "れんら"], "answer_index": 0},
        {"id": 4102, "word": "必要", "reading": "ひつよう", "meaning_ko": "필요", "quiz_type": "reading", "tag": "기본",
         "choices": ["ひつよう", "ひっよう", "ひつよ", "ひつおう"], "answer_index": 0},
    ],
    "N3(맛보기)": [
        {"id": 3001, "word": "改善", "reading": "かいぜん", "meaning_ko": "개선", "quiz_type": "meaning", "tag": "비즈니스",
         "choices": ["확대", "개선", "감소", "중단"], "answer_index": 1},
        {"id": 3002, "word": "影響", "reading": "えいきょう", "meaning_ko": "영향", "quiz_type": "meaning", "tag": "사회/시사",
         "choices": ["영향", "인상", "예상", "현상"], "answer_index": 0},
        {"id": 3003, "word": "判断", "reading": "はんだん", "meaning_ko": "판단", "quiz_type": "meaning", "tag": "비즈니스",
         "choices": ["상담", "판단", "분담", "부담"], "answer_index": 1},
        {"id": 3004, "word": "維持", "reading": "いじ", "meaning_ko": "유지", "quiz_type": "meaning", "tag": "비즈니스",
         "choices": ["유지", "위기", "의지", "유리"], "answer_index": 0},
        {"id": 3005, "word": "確認する", "reading": "かくにんする", "meaning_ko": "확인하다", "quiz_type": "meaning", "tag": "업무/커뮤니케이션",
         "choices": ["예약하다", "확인하다", "준비하다", "연습하다"], "answer_index": 1},
        {"id": 3006, "word": "増える", "reading": "ふえる", "meaning_ko": "늘다", "quiz_type": "meaning", "tag": "변화",
         "choices": ["줄다", "늘다", "끊다", "바꾸다"], "answer_index": 1},
        {"id": 3007, "word": "減る", "reading": "へる", "meaning_ko": "줄다", "quiz_type": "meaning", "tag": "변화",
         "choices": ["줄다", "늘다", "피하다", "지키다"], "answer_index": 0},
        {"id": 3008, "word": "間に合う", "reading": "まにあう", "meaning_ko": "시간에 맞다", "quiz_type": "meaning", "tag": "일정",
         "choices": ["늦다", "시간에 맞다", "미루다", "기다리다"], "answer_index": 1},
        {"id": 3009, "word": "見直す", "reading": "みなおす", "meaning_ko": "재검토하다", "quiz_type": "meaning", "tag": "비즈니스",
         "choices": ["재검토하다", "계속하다", "중단하다", "확정하다"], "answer_index": 0},
        {"id": 3010, "word": "結果", "reading": "けっか", "meaning_ko": "결과", "quiz_type": "meaning", "tag": "기본",
         "choices": ["경과", "효과", "결과", "변화"], "answer_index": 2},
        {"id": 3011, "word": "対策", "reading": "たいさく", "meaning_ko": "대책", "quiz_type": "meaning", "tag": "사회/시사",
         "choices": ["대책", "대상", "대기", "대우"], "answer_index": 0},
        {"id": 3012, "word": "提出", "reading": "ていしゅつ", "meaning_ko": "제출", "quiz_type": "meaning", "tag": "업무/커뮤니케이션",
         "choices": ["제안", "제출", "제한", "제작"], "answer_index": 1},

        {"id": 3101, "word": "改善", "reading": "かいぜん", "meaning_ko": "개선", "quiz_type": "reading", "tag": "비즈니스",
         "choices": ["かいぜん", "かいせん", "がいぜん", "かいぜい"], "answer_index": 0},
        {"id": 3102, "word": "影響", "reading": "えいきょう", "meaning_ko": "영향", "quiz_type": "reading", "tag": "사회/시사",
         "choices": ["えいきょう", "えいきゅう", "えいぎょう", "えいきょ"], "answer_index": 0},
    ],
}

# =========================
# 6) 레벨 선택
# =========================
st.subheader("레벨 선택")
level = st.selectbox("풀 레벨을 선택하세요", list(VOCAB_SETS.keys()), key="vocab_level")
VOCABS = VOCAB_SETS[level]

if len(VOCABS) < 10:
    st.warning("선택한 레벨의 문제가 10개 미만입니다. 단어를 더 추가해 주세요.")
    st.stop()

# =========================
# 7) 10문제 세트 고정
# =========================
if "vocab_quiz_ids" not in st.session_state:
    st.session_state.vocab_quiz_ids = None
if "vocab_submitted" not in st.session_state:
    st.session_state.vocab_submitted = False
if "vocab_saved_once" not in st.session_state:
    st.session_state.vocab_saved_once = False

if st.button("새 10문제 시작", key="vocab_start"):
    st.session_state.vocab_quiz_ids = random.sample([q["id"] for q in VOCABS], 10)
    st.session_state.vocab_submitted = False
    st.session_state.vocab_saved_once = False

    # 라디오 선택값 리셋
    for q in VOCABS:
        st.session_state.pop(f"vocab_pick_{q['id']}", None)

    st.rerun()

if st.session_state.vocab_quiz_ids is None:
    st.info("버튼을 눌러 10문제를 시작하세요.")
    st.stop()

id_to_q = {q["id"]: q for q in VOCABS}
quiz = [id_to_q[qid] for qid in st.session_state.vocab_quiz_ids]

# =========================
# 8) 문제 표시 + 제출
# =========================
with st.form("vocab_form"):
    user_answers = {}

    for i, q in enumerate(quiz, start=1):
        st.markdown(f"### Q{i}")

        if q.get("quiz_type") == "reading":
            question_text = f"**{q['word']}** 의 읽기는?"
            choices = q["choices"]
        else:
            question_text = f"**{q['word']}（{q['reading']}）** 의 뜻은?"
            choices = q["choices"]

        st.write(question_text)

        user_answers[q["id"]] = st.radio(
            "선택",
            choices,
            index=None,
            key=f"vocab_pick_{q['id']}",
        )
        st.divider()

    submitted = st.form_submit_button("제출 & 채점")

# =========================
# 9) 채점 + 리포트 + 저장
# =========================
if submitted:
    st.session_state.vocab_submitted = True

if st.session_state.vocab_submitted:
    if any(ans is None for ans in user_answers.values()):
        st.warning("선택하지 않은 문제가 있습니다. 모두 선택한 뒤 제출해 주세요.")
        st.stop()

    score = 0
    wrong_items = []     # 오답노트용(상세)
    wrong_words = []     # 저장용(간단)
    wrong_types = []     # 총평용(meaning/reading)
    wrong_tags = []      # 총평용(tag)

    st.subheader("결과")

    for i, q in enumerate(quiz, start=1):
        choices = q["choices"]
        correct = choices[q["answer_index"]]
        picked = user_answers[q["id"]]

        if picked == correct:
            score += 1
            st.success(f"Q{i} 정답 ✅ ({picked})")
        else:
            st.error(f"Q{i} 오답 ❌ (내 답: {picked} / 정답: {correct})")

            wrong_words.append(f"{q['word']}({q['reading']})")
            wrong_types.append(q.get("quiz_type", "meaning"))
            if q.get("tag"):
                wrong_tags.append(q["tag"])

            wrong_items.append({
                "no": i,
                "word": q["word"],
                "reading": q["reading"],
                "quiz_type": q.get("quiz_type", "meaning"),
                "tag": q.get("tag", ""),
                "picked": picked,
                "correct": correct,
                "meaning_ko": q.get("meaning_ko", ""),
            })

    st.write(f"## 점수: {score} / 10")

    # -------------------------
    # 학생용 리포트 1) 총평
    # -------------------------
    st.subheader("📌 총평")

    if score == 10:
        st.success("🎉 전부 정답입니다! 단어/읽기 감각이 아주 좋습니다. 다음 레벨로 넘어가도 좋아요.")
    else:
        # 1) 어떤 유형이 약한지(meaning vs reading)
        if wrong_types:
            type_counter = Counter(wrong_types)
            weak_type = type_counter.most_common(1)[0][0]
            if weak_type == "reading":
                type_msg = "읽기(読み) 유형"
                tip = "한자 단어는 '부수/음독·훈독 패턴'으로 묶어서 외우면 빨리 안정됩니다."
            else:
                type_msg = "뜻(의미) 유형"
                tip = "뜻은 '자주 붙는 동사/형용사(연어)'로 함께 외우면 기억이 오래 갑니다."
        else:
            type_msg = "전체"
            tip = "틀린 단어 위주로 3회전 복습(오늘/내일/일주일 후) 추천합니다."

        # 2) 태그 약점(있을 때만)
        tag_msg = ""
        if wrong_tags:
            tag_counter = Counter(wrong_tags)
            weak_tag = tag_counter.most_common(1)[0][0]
            tag_msg = f"특히 **{weak_tag}** 쪽이 조금 약해 보여요."

        st.info(
            f"이번 세트는 **{type_msg}**에서 오답이 더 나왔습니다. {tag_msg}\n\n"
            f"✅ 추천 복습: 틀린 단어만 오늘 3번 소리 내서 읽고, 내일 아침에 한 번 더 체크해 보세요.\n"
            f"💡 팁: {tip}"
        )

    # -------------------------
    # 학생용 리포트 2) 오답 노트
    # -------------------------
    st.subheader("📝 오답 노트")

    if not wrong_items:
        st.write("틀린 문제가 없습니다 👏")
    else:
        for item in wrong_items:
            st.markdown(f"**Q{item['no']}**")
            if item["quiz_type"] == "reading":
                st.write(f"- 문제: **{item['word']}** 의 읽기")
                st.write(f"- 정답: ✅ {item['correct']}")
                st.write(f"- 내 답: ❌ {item['picked']}")
                if item["meaning_ko"]:
                    st.caption(f"뜻: {item['meaning_ko']}")
            else:
                st.write(f"- 문제: **{item['word']}（{item['reading']}）** 의 뜻")
                st.write(f"- 정답: ✅ {item['correct']}")
                st.write(f"- 내 답: ❌ {item['picked']}")
                if item["meaning_ko"]:
                    st.caption(f"뜻: {item['meaning_ko']}")
            if item.get("tag"):
                st.caption(f"태그: {item['tag']}")
            st.divider()

    # -------------------------
    # 결과 저장(한 번만)
    # -------------------------
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
            "wrong_words": ", ".join(wrong_words),
            "wrong_count": len(wrong_words),
            "weak_type": Counter(wrong_types).most_common(1)[0][0] if wrong_types else "",
            "weak_tag": Counter(wrong_tags).most_common(1)[0][0] if wrong_tags else "",
        }

        if os.path.exists(RESULT_CSV):
            df = pd.read_csv(RESULT_CSV)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        else:
            df = pd.DataFrame([row])

        df.to_csv(RESULT_CSV, index=False, encoding="utf-8-sig")
        st.session_state.vocab_saved_once = True
        st.success(f"✅ 결과가 저장되었습니다 ({RESULT_CSV})")

    # -------------------------
    # 재도전 버튼
    # -------------------------
    if st.button("🔄 같은 문제 다시 풀기", key="vocab_retry"):
        for q in quiz:
            st.session_state.pop(f"vocab_pick_{q['id']}", None)
        st.session_state.vocab_submitted = False
        st.rerun()
