# 날씨 API 실습
# OpenWeatherMap 현재 날씨 API 로 특정 도시의 날씨를 가져와 출력한다.
# 사전준비: OpenWeatherMap 회원가입 후 API 발급
# pip install requests python-dotenv
# .env 파일을 생성하고 이곳에 OPENWEATHER_API_KEY=발급받은_API_키       Git에 올라가지 않는다.
# .env.example 에 OPENWEATHER_API_KEY=your_key      Git에 올라간다.
# 이걸 받고, .env 로 이름 바꿔서 your_key 에 진짜 내 key를 적는다.



import os
from pathlib import Path
import requests
import streamlit as st
from dotenv import load_dotenv

# 1. 환경 변수 로드 (상위 폴더의 .env)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
EXCHANGE_API_KEY = os.getenv('EXCHANGERATE_API_KEY')

# 2. Streamlit 페이지 설정
st.set_page_config(page_title="도시별 날씨 & 현지 통화 환율", page_icon="🌐", layout="wide")
st.title("🌐 도시별 실시간 날씨 및 환율 대시보드")

if not WEATHER_API_KEY:
    st.error("상위 폴더의 `.env` 파일에 `OPENWEATHER_API_KEY`를 설정해주세요.")
    st.stop()

if not EXCHANGE_API_KEY:
    st.error("상위 폴더의 `.env` 파일에 `EXCHANGERATE_API_KEY`를 설정해주세요.")
    st.stop()

# -------------------------------------------------------------
# 도시 정보 매핑 (영문명, 통화코드, 통화 표시 라벨, 환산 단위)
# -------------------------------------------------------------
CITY_INFO = {
    "서울": {"city_en": "Seoul", "currency": "KRW", "label": "대한민국 (KRW)", "unit": 1},
    "부산": {"city_en": "Busan", "currency": "KRW", "label": "대한민국 (KRW)", "unit": 1},
    "제주": {"city_en": "Jeju", "currency": "KRW", "label": "대한민국 (KRW)", "unit": 1},
    "도쿄": {"city_en": "Tokyo", "currency": "JPY", "label": "일본 (JPY 100엔)", "unit": 100},
    "런던": {"city_en": "London", "currency": "GBP", "label": "영국 (GBP)", "unit": 1},
    "파리": {"city_en": "Paris", "currency": "EUR", "label": "유럽 (EUR)", "unit": 1},
    "뉴욕": {"city_en": "New York", "currency": "USD", "label": "미국 (USD)", "unit": 1},
    "시드니": {"city_en": "Sydney", "currency": "AUD", "label": "호주 (AUD)", "unit": 1},
}

# 사이드바 필터
st.sidebar.header("⚙️ 도시 필터")
selected_cities = st.sidebar.multiselect(
    "조회할 도시를 선택하세요:",
    options=list(CITY_INFO.keys()),
    default=["서울", "도쿄", "런던"]
)

# -------------------------------------------------------------
# [PART 1] 날씨 섹션
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_weather(city_en):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return None
    except requests.exceptions.RequestException:
        return None

st.subheader("🌤️ 도시별 현재 날씨")

if not selected_cities:
    st.info("👈 사이드바에서 도시를 하나 이상 선택해주세요.")
else:
    columns_per_row = 3
    cols = st.columns(columns_per_row)

    for idx, city_ko in enumerate(selected_cities):
        city_en = CITY_INFO[city_ko]["city_en"]
        weather_data = fetch_weather(city_en)
        col = cols[idx % columns_per_row]

        with col:
            with st.container(border=True):
                if weather_data:
                    temp = weather_data["main"]["temp"]
                    feels_like = weather_data["main"]["feels_like"]
                    desc = weather_data["weather"][0]["description"]
                    icon_code = weather_data["weather"][0]["icon"]
                    humidity = weather_data["main"]["humidity"]
                    wind = weather_data["wind"]["speed"]
                    icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

                    st.subheader(f"📍 {city_ko} ({weather_data['name']})")
                    
                    icon_col, temp_col = st.columns([1, 1.2])
                    with icon_col:
                        st.image(icon_url, width=80)
                    with temp_col:
                        st.metric(label="현재 기온", value=f"{temp:.1f}°C", delta=f"체감 {feels_like:.1f}°C")

                    st.caption(f"상태: **{desc.capitalize()}**")
                    st.divider()

                    sub_col1, sub_col2 = st.columns(2)
                    sub_col1.caption(f"💧 습도: `{humidity}%`")
                    sub_col2.caption(f"💨 풍속: `{wind}m/s`")
                else:
                    st.subheader(f"📍 {city_ko}")
                    st.error("날씨 데이터를 불러오지 못했습니다.")

# -------------------------------------------------------------
# [PART 2] 선택한 도시의 해당 국가 환율 섹션
# -------------------------------------------------------------
st.markdown("---")
st.subheader("💱 선택한 도시의 현지 통화 환율 (KRW 기준)")

@st.cache_data(ttl=600)
def fetch_exchange_rates(api_key):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/KRW"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return None
    except requests.exceptions.RequestException:
        return None

# 선택된 도시들의 고유 외화 통화 목록 추출 (KRW 제외 및 중복 제거)
target_currencies = {}
for city in selected_cities:
    info = CITY_INFO[city]
    curr = info["currency"]
    if curr != "KRW" and curr not in target_currencies:
        target_currencies[curr] = {
            "label": info["label"],
            "unit": info["unit"]
        }

if not target_currencies:
    st.caption("선택한 도시에 외화 환율 정보가 필요한 해외 도시가 없습니다.")
else:
    exchange_data = fetch_exchange_rates(EXCHANGE_API_KEY)
    
    if exchange_data and exchange_data.get("result") == "success":
        rates = exchange_data.get("conversion_rates", {})
        
        # col1, col2 2열로 깔끔하게 배치
        col1, col2 = st.columns(2)

        for idx, (curr_code, meta) in enumerate(target_currencies.items()):
            if curr_code in rates:
                # KRW 기준 외화 환산: (1 / rates[curr_code]) * unit
                rate_value = (1 / rates[curr_code]) * meta["unit"]
                target_col = col1 if idx % 2 == 0 else col2
                with target_col:
                    target_col.metric(label=meta["label"], value=f"{rate_value:,.2f} 원")

        last_update = exchange_data.get("time_last_update_utc", "")
        if last_update:
            st.caption(f"🕒 기준 일시 (UTC): {last_update}")
    else:
        st.error("환율 정보를 불러오는 데 실패했습니다.")
# -------------------------------------------------------------
# [PART 3] 접이식 실시간 환전 계산기
# -------------------------------------------------------------
with st.expander("🧮 실시간 환전 계산기 열기 / 닫기", expanded=False):
    if not target_currencies:
        st.info("사이드바에서 해외 도시를 먼저 선택하시면 해당 국가 통화로 계산할 수 있습니다.")
    elif exchange_data and exchange_data.get("result") == "success":
        rates = exchange_data.get("conversion_rates", {})
        
        # 계산기 레이아웃 (3열 배치)
        calc_col1, calc_col2, calc_col3 = st.columns([1.5, 1.2, 1.5])
        
        with calc_col1:
            # 환전 방향 선택
            convert_direction = st.radio(
                "환전 방향",
                ["외화 ➔ 원화(KRW)", "원화(KRW) ➔ 외화"],
                horizontal=True
            )
        
        with calc_col2:
            # 선택된 도시들의 통화 중 선택
            currency_choices = list(target_currencies.keys())
            selected_calc_curr = st.selectbox(
                "환전 통화 선택",
                options=currency_choices,
                format_func=lambda code: f"{target_currencies[code]['label']} ({code})"
            )
            
        # 1 외화당 KRW 기본 단가 계산
        raw_unit_krw = 1 / rates[selected_calc_curr]
        
        with calc_col3:
            if convert_direction == "외화 ➔ 원화(KRW)":
                input_amount = st.number_input(
                    f"금액 입력 ({selected_calc_curr})",
                    min_value=0.0,
                    value=100.0,
                    step=10.0
                )
                converted_result = input_amount * raw_unit_krw
                result_text = f"{converted_result:,.0f} KRW"
                result_label = f"{input_amount:,.2f} {selected_calc_curr} ➔ 원화 환전액"
            else:
                input_amount = st.number_input(
                    "금액 입력 (KRW)",
                    min_value=0.0,
                    value=100000.0,
                    step=10000.0
                )
                converted_result = input_amount / raw_unit_krw
                result_text = f"{converted_result:,.2f} {selected_calc_curr}"
                result_label = f"{input_amount:,.0f} KRW ➔ 외화 환전액"

        # 계산 결과 출력
        st.divider()
        res_col1, res_col2 = st.columns([2, 1])
        with res_col1:
            st.metric(label=result_label, value=result_text)
        with res_col2:
            st.caption("📌 실시간 매매기준율 기준 (수수료 미포함)")
            st.caption(f"적용 환율: 1 {selected_calc_curr} = {raw_unit_krw:,.2f} 원")