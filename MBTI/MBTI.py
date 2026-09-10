import base64
import os
import streamlit as st

# -------------------------------------------------------------
# 1. 파일 경로 탐색 헬퍼 & 로컬 폰트 로드
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_file_path(filename):
  """MBTI.py가 있는 폴더 및 주요 하위 폴더에서 파일을 안전하게 탐색합니다."""
  name_without_ext = os.path.splitext(filename)[0]
  candidates = [
      filename,
      f"{name_without_ext}.PNG",
      f"{name_without_ext}.png.png",
      f"{name_without_ext}.jpg",
      f"{name_without_ext}.jpeg",
  ]

  search_folders = [
      BASE_DIR,
      os.path.join(BASE_DIR, "assets"),
      os.path.join(BASE_DIR, "assets", "characters"),
      os.getcwd(),
  ]

  for folder in search_folders:
    for cand in candidates:
      target_path = os.path.join(folder, cand)
      if os.path.exists(target_path):
        return target_path
  return None


def get_base64_data(file_path):
  """파일을 읽어 Base64 문자열로 변환합니다."""
  if file_path and os.path.exists(file_path):
    with open(file_path, "rb") as f:
      return base64.b64encode(f.read()).decode("utf-8")
  return None


font_path = find_file_path("Pretendard-Regular.otf")
font_b64 = get_base64_data(font_path)

if font_b64:
  font_face_rule = f"""
    @font-face {{
        font-family: 'Pretendard-Local';
        src: url('data:font/otf;charset=utf-8;base64,{font_b64}') format('opentype');
        font-weight: 400;
        font-style: normal;
    }}
    """
  font_family_name = "'Pretendard-Local', sans-serif"
else:
  font_face_rule = ""
  font_family_name = (
      "-apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif"
  )

# -------------------------------------------------------------
# 2. Streamlit 기본 설정 및 모바일 반응형 라벤더 테마 CSS
# -------------------------------------------------------------
st.set_page_config(
    page_title="Trade-MBTI | 나에게 딱 맞는 무역 직무 찾기",
    page_icon="🌏",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
    {font_face_rule}

    /* 전역 폰트 강제 적용 */
    html, body, [class*="css"], .stApp, button, input, select, textarea, * {{
        font-family: {font_family_name} !important;
        letter-spacing: -0.02em;
        word-break: keep-all;
    }}

    .stApp {{
        background-color: #F9F8FC;
        color: #2D2638;
    }}

    /* 메인 컨테이너 모바일 반응형 패딩 */
    .block-container {{
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 680px !important;
    }}

    /* 반응형 라벤더 카드 */
    .lavender-card {{
        background: #FFFFFF;
        border-radius: 20px;
        padding: 24px 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 24px rgba(139, 123, 184, 0.08);
        border: 1.5px solid #EFEBF7;
    }}

    /* 반응형 타이틀 */
    .main-title {{
        color: #5C4B82;
        font-weight: 800;
        font-size: clamp(1.8rem, 6vw, 2.3rem);
        text-align: center;
        margin-bottom: 4px;
    }}
    .sub-title {{
        color: #8B7BB8;
        font-size: clamp(0.95rem, 3.5vw, 1.1rem);
        font-weight: 600;
        text-align: center;
        margin-bottom: 20px;
    }}

    /* 질문 박스 */
    .q-box {{
        background-color: #F4F1FA;
        border-radius: 14px;
        padding: 16px 18px;
        font-weight: 700;
        color: #3C334A;
        font-size: clamp(0.95rem, 3.5vw, 1.05rem);
        margin-bottom: 12px;
        border-left: 5px solid #8B7BB8;
        line-height: 1.5;
    }}

    /* 라디오 버튼 선택지 */
    div[role="radiogroup"] > label {{
        background-color: #FFFFFF;
        border: 1.2px solid #E5DEF0;
        border-radius: 12px;
        padding: 12px 14px !important;
        margin-bottom: 8px;
        transition: all 0.2s ease;
        line-height: 1.45;
        font-size: clamp(0.88rem, 3.2vw, 0.98rem);
    }}
    div[role="radiogroup"] > label:hover {{
        border-color: #8B7BB8;
        background-color: #FAF8FD;
    }}

    /* 버튼 스타일 */
    .stButton>button {{
        background-color: #8B7BB8;
        color: #FFFFFF;
        font-weight: 700;
        border-radius: 12px;
        border: none;
        padding: 12px 20px;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(139, 123, 184, 0.25);
    }}
    .stButton>button:hover {{
        background-color: #7665A3;
        color: #FFFFFF;
        transform: translateY(-1px);
    }}

    /* 결과 카드 */
    .result-badge {{
        display: inline-block;
        background-color: #EFEBF7;
        color: #6C5A96;
        padding: 5px 16px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.9rem;
        letter-spacing: 1.2px;
        margin-bottom: 10px;
    }}
    .job-title {{
        color: #4D3C73;
        font-size: clamp(1.6rem, 5.5vw, 2.1rem);
        font-weight: 800;
        margin: 8px 0 4px 0;
    }}
    .job-tagline {{
        color: #7B68A6;
        font-size: clamp(0.95rem, 3.5vw, 1.1rem);
        font-weight: 600;
        margin-bottom: 15px;
    }}

    /* 캐릭터 이미지 반응형 컨테이너 */
    .character-container {{
        width: 100%;
        max-width: 320px;
        margin: 0 auto 20px auto;
        display: flex;
        justify-content: center;
    }}
    .character-container img {{
        border-radius: 18px;
        box-shadow: 0 8px 20px rgba(139, 123, 184, 0.15);
        width: 100%;
        height: auto;
    }}

    /* 지표 카드 */
    .metric-row {{
        background-color: #FAF8FD;
        border: 1px solid #ECE6F6;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }}

    @media (max-width: 480px) {{
        .lavender-card {{
            padding: 20px 14px;
        }}
        .q-box {{
            padding: 14px 14px;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 3. 질문 데이터셋 (20문항)
# -------------------------------------------------------------
QUESTIONS = [
    # [축 1: Front vs Back]
    {
        "id": 1,
        "axis": "FB",
        "question": "Q1. 새로운 프로젝트를 시작할 때 더 끌리는 방식은?",
        "options": [
            ("직접 발로 뛰며 해외 바이어나 파트너사를 만나는 일", "F"),
            (
                "사무실에서 데이터, 계약서 및 수출입 조건을 정밀하게 검토하는 일",
                "B",
            ),
        ],
    },
    {
        "id": 2,
        "axis": "FB",
        "question": "Q2. 해외 출장 기회가 주어졌을 때 나의 첫 반응은?",
        "options": [
            ("현지 시장을 직접 체험하고 사람들과 미팅할 생각에 설렌다.", "F"),
            (
                "일정 차질이나 서류 누락 걱정이 앞서 꼼꼼히 체크리스트를 짠다.",
                "B",
            ),
        ],
    },
    {
        "id": 3,
        "axis": "FB",
        "question": "Q3. 업무 중 가장 큰 성취감과 에너지를 얻는 순간은?",
        "options": [
            ("까다로운 바이어를 직접 설득해 대형 계약을 성사시켰을 때", "F"),
            (
                "복잡하게 꼬인 통관/선적 서류와 이슈를 완벽히 정리해 끝냈을 때",
                "B",
            ),
        ],
    },
    {
        "id": 4,
        "axis": "FB",
        "question": "Q4. 팀 내에서 내가 선호하는 포지션은?",
        "options": [
            ("최전선에서 새로운 거래 기회를 가져오는 공격수", "F"),
            ("후방에서 빈틈없이 운영과 리스크를 방어해주는 든든한 수비수", "B"),
        ],
    },
    {
        "id": 5,
        "axis": "FB",
        "question": "Q5. 거래처와의 관계를 맺을 때 내 스타일은?",
        "options": [
            ("사소한 안부나 일상적인 스몰토크도 적극적으로 주고받는다.", "F"),
            ("업무에 꼭 필요한 정제되고 명확한 커뮤니케이션을 선호한다.", "B"),
        ],
    },
    # [축 2: Action vs Plan]
    {
        "id": 6,
        "axis": "AP",
        "question": "Q6. 선적 지연이나 납기 문제가 긴급하게 터졌을 때 나는?",
        "options": [
            ("당장 활용 가능한 대체 선박이나 항공편부터 빠르게 수소문한다.", "A"),
            (
                "지연 원인과 계약 조건(Incoterms, 위약 조항)을 정확히 분석한 뒤 대처한다.",
                "P",
            ),
        ],
    },
    {
        "id": 7,
        "axis": "AP",
        "question": "Q7. 업무를 추진할 때 더 중요하다고 믿는 가치는?",
        "options": [
            ("타이밍을 놓치지 않는 빠른 결단력과 과감한 실행력", "A"),
            ("오차 0%를 지향하는 철저한 사전 검증과 정밀함", "P"),
        ],
    },
    {
        "id": 8,
        "axis": "AP",
        "question": "Q8. 일할 때 나를 더 답답하고 지치게 만드는 환경은?",
        "options": [
            ("절차와 규정이 너무 빡빡해서 속도가 나지 않을 때", "A"),
            ("명확한 가이드라인 없이 알아서 대충 처리하라고 할 때", "P"),
        ],
    },
    {
        "id": 9,
        "axis": "AP",
        "question": "Q9. 마감 직전, 제출 서류에서 사소한 오타 하나를 발견했다면?",
        "options": [
            ("전체 맥락상 지장 없다면 일단 제시간에 송부하고 다음을 챙긴다.", "A"),
            (
                "마감이 촉박하더라도 오타를 완벽히 바로잡은 뒤 제출해야 직성이 풀린다.",
                "P",
            ),
        ],
    },
    {
        "id": 10,
        "axis": "AP",
        "question": "Q10. 출근 후 하루 일과를 시작하는 내 모습은?",
        "options": [
            ("새벽 사이 온 긴급 메일이나 유동적인 변수에 맞춰 유연하게 움직인다.", "A"),
            ("우선순위에 따라 오늘 끝낼 업무 체크리스트를 시간순으로 계획한다.", "P"),
        ],
    },
    # [축 3: Relationship vs Data]
    {
        "id": 11,
        "axis": "RD",
        "question": "Q11. 협상 테이블에서 상대를 설득할 때 나의 가장 강력한 무기는?",
        "options": [
            ("상대의 심리와 니즈를 짚어내는 대화 기술과 라포(신뢰) 형성", "R"),
            ("객관적인 데이터, 원가 분석표, 시장 지표 근거 자료", "D"),
        ],
    },
    {
        "id": 12,
        "axis": "RD",
        "question": "Q12. 가격 네고(Negotiation)를 할 때 더 자신 있는 것은?",
        "options": [
            ("상대방의 반응을 살피며 밀고 당기는 심리전", "R"),
            ("환율 추이, 관세율, 운임 데이터를 바탕으로 손익분기점 따지기", "D"),
        ],
    },
    {
        "id": 13,
        "axis": "RD",
        "question": "Q13. 업무 관련 자료 중 더 흥미를 끄는 것은?",
        "options": [
            ("해외 바이어 성향 분석 및 글로벌 비즈니스 에티켓 보고서", "R"),
            ("국가별 관세율 개정안 및 HS Code 세부 품목 분류표", "D"),
        ],
    },
    {
        "id": 14,
        "axis": "RD",
        "question": "Q14. 거래처 담당자가 다소 무리한 부탁을 해올 때 나의 대응은?",
        "options": [
            ("관계 유지를 위해 어떻게든 가능한 대안을 만들어 맞춰주려 노력한다.", "R"),
            ("사내 규정이나 법적 기준에 어긋난다면 정중하지만 단호하게 선을 긋는다.", "D"),
        ],
    },
    {
        "id": 15,
        "axis": "RD",
        "question": "Q15. 보고서를 쓸 때 가장 공들이는 핵심 요소는?",
        "options": [
            ("의사결정권자가 직관적으로 공감하고 설득될 수 있는 스토리라인", "R"),
            ("한 치의 오차도 없는 정확한 수치와 공신력 있는 출처 검증", "D"),
        ],
    },
    # [축 4: Create vs Operate]
    {
        "id": 16,
        "axis": "CO",
        "question": "Q16. 두 가지 과제 중 더 가슴을 뛰게 하는 일은?",
        "options": [
            ("진출한 적 없는 미개척 신규 국가 시장 뚫기", "C"),
            ("이미 거래 중인 메인 바이어와의 프로세스를 안정적으로 굴리기", "O"),
        ],
    },
    {
        "id": 17,
        "axis": "CO",
        "question": "Q17. 해외 대형 박람회 참가 시 더 맡고 싶은 업무는?",
        "options": [
            ("부스 콘셉트 기획, 참신한 홍보물 제작 및 신규 관람객 유치", "C"),
            ("전시 샘플 운송/통관 일정 조율 및 현장 바이어 상담 일지 정리", "O"),
        ],
    },
    {
        "id": 18,
        "axis": "CO",
        "question": "Q18. 글로벌 신상품 트렌드를 접했을 때 드는 첫 생각은?",
        "options": [
            ("“이 아이템을 어느 나라 시장에 어떻게 런칭하면 잘 팔릴까?”", "C"),
            (
                "“이 제품을 실제 수입할 때 통관 규제나 인증 이슈가 없을까?”",
                "O",
            ),
        ],
    },
    {
        "id": 19,
        "axis": "CO",
        "question": "Q19. 반복되는 무역 루틴 업무를 마주할 때 나는?",
        "options": [
            ("지루함을 느껴 새로운 방식이나 자동화 개선안을 찾고 싶어진다.", "C"),
            ("손에 익을수록 실수가 줄어들고 안정감이 생겨 편안함을 느낀다.", "O"),
        ],
    },
    {
        "id": 20,
        "axis": "CO",
        "question": "Q20. 커리어에서 가장 값지다고 느끼는 순간은?",
        "options": [
            ("아무도 시도하지 않았던 새로운 시장과 판로를 내 손으로 열었을 때", "C"),
            ("복잡한 공급망과 수출입 사이클을 무결점으로 완벽하게 굴렸을 때", "O"),
        ],
    },
]

# -------------------------------------------------------------
# 4. 6개 무역 직무 프로필
# -------------------------------------------------------------
JOB_PROFILES = {
    "해외영업": {
        "english": "Overseas Sales",
        "code_desc": "글로벌 무대를 누비는 공격형 개척자",
        "image_file": "해외영업.png",
        "traits": [
            "새로운 해외 시장과 바이어 발굴에 주저함이 없는 적극성",
            "상대방의 니즈를 파악해 윈-윈(Win-Win) 딜을 이끌어내는 협상력",
            "국가별 비즈니스 문화 차이를 유연하게 넘나드는 글로벌 커뮤니케이션",
        ],
        "best_partner": "무역영업관리 (빈틈없는 계약 사후 관리와 선적 조율로 서포트)",
    },
    "해외마케팅": {
        "english": "Global Marketing",
        "code_desc": "트렌드를 읽고 시장의 수요를 창출하는 기획자",
        "image_file": "해외마케팅.png",
        "traits": [
            "글로벌 전시회 콘셉트 기획 및 매력적인 바이어 유입 전략 수립",
            "현지 시장조사 데이터를 바탕으로 한 제품 포지셔닝 및 브랜딩",
            "바이어의 호기심을 유발하고 상담으로 연결하는 스토리텔링 능력",
        ],
        "best_partner": "해외영업 (발굴된 마케팅 리드를 직접 매출로 연결해 줌)",
    },
    "포워딩/물류운영": {
        "english": "Freight Forwarding & Logistics",
        "code_desc": "글로벌 물류의 복잡한 퍼즐을 맞추는 해결사",
        "image_file": "포워딩.png",
        "traits": [
            "해상·항공 운송 스케줄 분석 및 최적의 운임 협상 능력",
            "선적 지연, 기상 악화 등 긴급 트러블 발생 시 번개 같은 임기응변",
            "선사, 항공사, 운송 파트너들과의 긴밀하고 즉각적인 조율",
        ],
        "best_partner": "무역영업관리 (정확한 선적 서류 전달로 통관 지연을 방지함)",
    },
    "글로벌 소싱/구매": {
        "english": "Global Sourcing & Procurement",
        "code_desc": "원가와 리스크를 완벽하게 통제하는 분석적 협상가",
        "image_file": "글로벌소싱.png",
        "traits": [
            "전 세계 유망 공급망(Supplier) 발굴 및 원가 구조 정밀 분석",
            "손익분기점과 환율 변동을 고려한 최적의 단가 협상",
            "품질 이슈, 공급망 불안정 등 잠재적 리스크에 대한 선제적 차단",
        ],
        "best_partner": "관세/통관 컴플라이언스 (소싱 품목의 수입 규제 및 관세 사전 확인)",
    },
    "관세/통관 컴플라이언스": {
        "english": "Trade Compliance & Customs",
        "code_desc": "법규와 정확성으로 무역 리스크 0%를 만드는 원칙주의자",
        "image_file": "관세컴플라이언스.png",
        "traits": [
            "정확한 HS Code 분류 및 FTA 원산지 증명 관리 능력",
            "대외무역법, 관세법 등 복잡한 무역 규제에 대한 완벽한 숙지",
            "세관 감사 및 통관 보류 등의 법적 리스크를 미연에 방지하는 꼼꼼함",
        ],
        "best_partner": "글로벌 소싱/구매 (소싱 품목의 적격성을 보증하고 관세 절감 지원)",
    },
    "무역영업관리": {
        "english": "Sales Administration",
        "code_desc": "수주부터 납품 완결까지 책임지는 백오피스 컨트롤타워",
        "image_file": "무역영업관리.png",
        "traits": [
            "수출입 서류(B/L, C/I, P/L, L/C) 작성 및 대금 결제 프로세스 완결",
            "수주 이후 생산, 출하, 선적까지 전 과정의 일정 오차 제로화",
            "영업팀과 물류팀, 바이어 사이에서 매끄러운 다리 역할을 하는 조율력",
        ],
        "best_partner": "해외영업 (수주된 계약을 안정적인 실제 납품과 매출로 마감 지음)",
    },
}


def calculate_result(scores):
    """4개 축 판정 및 가중치 합산 직무 매칭"""
    code_fb = "F" if scores["F"] >= scores["B"] else "B"
    code_ap = "A" if scores["A"] >= scores["P"] else "P"
    code_rd = "R" if scores["R"] >= scores["D"] else "D"
    code_co = "C" if scores["C"] >= scores["O"] else "O"
    mbti_code = f"{code_fb}{code_ap}{code_rd}{code_co}"

    job_scores = {job: 0 for job in JOB_PROFILES}

    # F vs B
    if code_fb == "F":
        job_scores["해외영업"] += 3
        job_scores["해외마케팅"] += 3
    else:
        job_scores["무역영업관리"] += 2
        job_scores["포워딩/물류운영"] += 2
        job_scores["글로벌 소싱/구매"] += 2
        job_scores["관세/통관 컴플라이언스"] += 3

    # A vs P
    if code_ap == "A":
        job_scores["해외영업"] += 2
        job_scores["포워딩/물류운영"] += 3
        job_scores["글로벌 소싱/구매"] += 2
    else:
        job_scores["관세/통관 컴플라이언스"] += 3
        job_scores["무역영업관리"] += 2
        job_scores["해외마케팅"] += 1

    # R vs D
    if code_rd == "R":
        job_scores["해외영업"] += 2
        job_scores["해외마케팅"] += 2
        job_scores["포워딩/물류운영"] += 1
    else:
        job_scores["관세/통관 컴플라이언스"] += 3
        job_scores["글로벌 소싱/구매"] += 2
        job_scores["무역영업관리"] += 1

    # C vs O
    if code_co == "C":
        job_scores["해외마케팅"] += 3
        job_scores["해외영업"] += 2
        job_scores["글로벌 소싱/구매"] += 1
    else:
        job_scores["무역영업관리"] += 3
        job_scores["포워딩/물류운영"] += 2
        job_scores["관세/통관 컴플라이언스"] += 2

    recommended_job = max(job_scores, key=job_scores.get)
    return mbti_code, recommended_job


# -------------------------------------------------------------
# 5. 세션 상태 관리
# -------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}


def restart_test():
    st.session_state.current_page = 0
    st.session_state.answers = {}


# -------------------------------------------------------------
# 6. 화면 라우팅
# -------------------------------------------------------------

# PAGE 0: 인트로 화면
if st.session_state.current_page == 0:
    st.markdown(
        '<div class="main-title">🌏 Trade-MBTI</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">나에게 딱 맞는 무역 직무 찾기</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lavender-card" style="text-align: center;">
            <h3 style="color: #4A4453; margin-top: 0; font-weight: 700; font-size: 1.15rem;">글로벌 무대에서 당신의 잠재력은 어디서 빛날까요?</h3>
            <p style="color: #6A6275; line-height: 1.75; font-size: 0.96rem;">
                해외영업, 무역영업관리, 포워딩, 글로벌 소싱, 관세 컴플라이언스, 해외마케팅까지!<br>
                무역 실무 프로세스를 담은 <b>20가지 밸런스 질문</b>을 통해<br>
                나의 업무 성향 코드와 딱 맞는 직무 캐릭터를 만나보세요.
            </p>
            <div style="background: #FAF8FD; padding: 14px 16px; border-radius: 14px; text-align: left; font-size: 0.88rem; border: 1px solid #ECE6F6; margin-top: 15px;">
                ✨ <b>진단 축:</b> 현장(F) vs 관리(B) · 속도(A) vs 원칙(P) · 관계(R) vs 데이터(D) · 개척(C) vs 운영(O)<br>
                ⏱️ <b>소요 시간:</b> 약 3분
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("🚀 무역 직무 성향 테스트 시작하기", use_container_width=True):
        st.session_state.current_page = 1
        st.rerun()

# PAGE 1 ~ 4: 5문항씩 순차 진행
elif 1 <= st.session_state.current_page <= 4:
    page = st.session_state.current_page
    start_idx = (page - 1) * 5
    end_idx = start_idx + 5
    page_questions = QUESTIONS[start_idx:end_idx]

    progress = (page - 1) / 4
    st.markdown(
        f'<div style="text-align: right; color: #8B7BB8; font-weight: 700; font-size: 0.9rem;">진행도 {page} / 4단계</div>',
        unsafe_allow_html=True,
    )
    st.progress(progress)
    st.write("")

    with st.form(key=f"question_form_page_{page}"):
        page_answers = {}

        for q in page_questions:
            q_id = q["id"]
            st.markdown(
                f'<div class="q-box">{q["question"]}</div>',
                unsafe_allow_html=True,
            )

            current_choice = st.session_state.answers.get(q_id, None)
            default_index = 0
            if current_choice:
                default_index = (
                    0 if current_choice == q["options"][0][1] else 1
                )

            selected_option = st.radio(
                label=f"q_{q_id}",
                options=[q["options"][0][0], q["options"][1][0]],
                index=default_index,
                label_visibility="collapsed",
                key=f"radio_{q_id}",
            )

            code = (
                q["options"][0][1]
                if selected_option == q["options"][0][0]
                else q["options"][1][1]
            )
            page_answers[q_id] = code
            st.write("")

        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            prev_btn = (
                st.form_submit_button("이전", use_container_width=True)
                if page > 1
                else False
            )
        with col_next:
            next_btn_text = (
                "다음 단계로" if page < 4 else "최종 결과 확인하기 🔮"
            )
            next_btn = st.form_submit_button(
                next_btn_text, use_container_width=True
            )

        if prev_btn:
            st.session_state.answers.update(page_answers)
            st.session_state.current_page -= 1
            st.rerun()

        if next_btn:
            st.session_state.answers.update(page_answers)
            if page < 4:
                st.session_state.current_page += 1
            else:
                st.session_state.current_page = 5
            st.rerun()

# PAGE 5: 결과 화면
elif st.session_state.current_page == 5:
    scores = {"F": 0, "B": 0, "A": 0, "P": 0, "R": 0, "D": 0, "C": 0, "O": 0}
    for q_id, choice in st.session_state.answers.items():
        if choice in scores:
            scores[choice] += 1

    mbti_code, job_name = calculate_result(scores)
    job_info = JOB_PROFILES[job_name]
    target_img_path = find_file_path(job_info["image_file"])

    # 상단 결과 카드
    st.markdown(
        f"""
        <div class="lavender-card" style="text-align: center;">
            <div class="result-badge">TRADE MBTI : {mbti_code}</div>
            <div class="job-tagline">"{job_info['code_desc']}"</div>
            <div class="job-title">🎯 추천 직무: {job_name}</div>
            <div style="color: #7B68A6; font-size: 0.95rem; font-weight: 600; margin-bottom: 18px;">({job_info['english']})</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # 반응형 캐릭터 이미지 출력
    if target_img_path:
        img_b64 = get_base64_data(target_img_path)
        st.markdown(
            f"""
            <div class="character-container">
                <img src="data:image/png;base64,{img_b64}" alt="{job_name}">
            </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.error(
            f"⚠️ 이미지 파일 '{job_info['image_file']}'을(를) 찾을 수 없습니다."
            f" MBTI.py와 같은 폴더에 '{job_info['image_file']}'이 있는지"
            " 확인해 주세요."
        )

    # 4대 성향 지표
    st.markdown("### 📊 나의 무역 성향 세부 지표")

    total_per_axis = 5

    # 1. Front vs Back
    f_pct = int((scores["F"] / total_per_axis) * 100)
    b_pct = 100 - f_pct
    st.markdown(
        f"""
        <div class="metric-row">
            <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">
                <span>대외 현장형 (Front) {f_pct}%</span>
                <span>{b_pct}% 백오피스형 (Back)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(scores["F"] / total_per_axis)

    # 2. Action vs Plan
    a_pct = int((scores["A"] / total_per_axis) * 100)
    p_pct = 100 - a_pct
    st.markdown(
        f"""
        <div class="metric-row">
            <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">
                <span>속도/임기응변 (Action) {a_pct}%</span>
                <span>{p_pct}% 원칙/정확도 (Plan)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(scores["A"] / total_per_axis)

    # 3. Relationship vs Data
    r_pct = int((scores["R"] / total_per_axis) * 100)
    d_pct = 100 - r_pct
    st.markdown(
        f"""
        <div class="metric-row">
            <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">
                <span>사람/협상 (Relationship) {r_pct}%</span>
                <span>{d_pct}% 수치/데이터 (Data)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(scores["R"] / total_per_axis)

    # 4. Create vs Operate
    c_pct = int((scores["C"] / total_per_axis) * 100)
    o_pct = 100 - c_pct
    st.markdown(
        f"""
        <div class="metric-row">
            <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">
                <span>기획/시장개척 (Create) {c_pct}%</span>
                <span>{o_pct}% 운영/안정 (Operate)</span>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.progress(scores["C"] / total_per_axis)

    # 직무 설명 카드
    st.write("")
    st.markdown(
        f"""
        <div class="lavender-card">
            <h3 style="color: #4D3C73; margin-top: 0; font-weight: 700; font-size: 1.15rem;">✨ {job_name} 직무가 어울리는 이유</h3>
            <ul style="color: #4A4453; line-height: 1.85; font-size: 0.96rem; margin-bottom: 18px; padding-left: 20px;">
                {"".join([f"<li>{trait}</li>" for trait in job_info['traits']])}
            </ul>
            <hr style="border: none; border-top: 1px dashed #D8D0E8; margin: 16px 0;">
            <div style="font-size: 0.92rem; color: #5C4B82; line-height: 1.55;">
                🤝 <b>환상의 파트너 직무:</b> {job_info['best_partner']}
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # 다시 검사하기 버튼
    if st.button("🔄 테스트 다시 하기", use_container_width=True):
        restart_test()
        st.rerun()