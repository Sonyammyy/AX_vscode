import os
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# 1. 환경 변수 로드 (상위 폴더의 .env)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
EXCHANGE_API_KEY = os.getenv('EXCHANGERATE_API_KEY')

st.set_page_config(page_title="글로벌 여행 올인원 대시보드", page_icon="✈️", layout="wide")
st.title("✈️ 스마트 여행 올인원 대시보드")

if not WEATHER_API_KEY or not EXCHANGE_API_KEY:
    st.error("상위 폴더의 `.env` 파일에 `OPENWEATHER_API_KEY`와 `EXCHANGERATE_API_KEY`를 모두 등록해주세요.")
    st.stop()

# 2. 여행 도시 마스터 데이터
TRAVEL_CITIES = {
    "도쿄 (일본)": {
        "city_en": "Tokyo", "currency": "JPY", "curr_name": "엔화", "unit": 100,
        "timezone": "Asia/Tokyo", "flag": "🇯🇵",
        "attractions": ["시부야 스카이", "센소지", "도쿄 타워", "신주쿠 교엔"],
        "tip": "대중교통 이용 시 스이카(Suica) 모바일 패스 등록을 추천합니다."
    },
    "오사카 (일본)": {
        "city_en": "Osaka", "currency": "JPY", "curr_name": "엔화", "unit": 100,
        "timezone": "Asia/Tokyo", "flag": "🇯🇵",
        "attractions": ["도톤보리", "유니버설 스튜디오 재팬", "오사카성"],
        "tip": "주유패스를 활용하면 주요 관광지 무료입장 및 지하철 무제한 이용이 가능합니다."
    },
    "파리 (프랑스)": {
        "city_en": "Paris", "currency": "EUR", "curr_name": "유로", "unit": 1,
        "timezone": "Europe/Paris", "flag": "🇫🇷",
        "attractions": ["에펠탑", "루브르 박물관", "몽마르트르 언덕", "개선문"],
        "tip": "소매치기가 잦은 랜드마크 주변에서는 가방을 앞으로 매는 것이 안전합니다."
    },
    "런던 (영국)": {
        "city_en": "London", "currency": "GBP", "curr_name": "파운드", "unit": 1,
        "timezone": "Europe/London", "flag": "🇬🇧",
        "attractions": ["빅벤 & 국회의사당", "대영박물관", "타워브릿지", "런던아이"],
        "tip": "교통카드(오이스터) 없이 컨택리스 지원 한국 신용카드로 지하철 바로 탑승 가능합니다."
    },
    "뉴욕 (미국)": {
        "city_en": "New York", "currency": "USD", "curr_name": "달러", "unit": 1,
        "timezone": "America/New_York", "flag": "🇺🇸",
        "attractions": ["타임스스퀘어", "센트럴파크", "자유의 여신상", "브루클린 브릿지"],
        "tip": "식당 이용 시 결제 금액의 18~20% 팁이 통상 권장됩니다."
    },
    "방콕 (태국)": {
        "city_en": "Bangkok", "currency": "THB", "curr_name": "바트", "unit": 1,
        "timezone": "Asia/Bangkok", "flag": "🇹🇭",
        "attractions": ["왓 아룬", "짜뚜짝 주말시장", "아이콘시암", "카오산로드"],
        "tip": "사원 방문 시 민소매와 짧은 바지는 입장이 제한되므로 긴 옷을 준비하세요."
    },
    "다낭 (베트남)": {
        "city_en": "Da Nang", "currency": "VND", "curr_name": "동", "unit": 100,
        "timezone": "Asia/Ho_Chi_Minh", "flag": "🇻🇳",
        "attractions": ["미케 비치", "바나힐", "호이안 올드타운", "용다리"],
        "tip": "그랩(Grab) 앱을 한국에서 미리 카드 등록 후 설치해 가면 이동이 매우 편리합니다."
    },
    "시드니 (호주)": {
        "city_en": "Sydney", "currency": "AUD", "curr_name": "호주달러", "unit": 1,
        "timezone": "Australia/Sydney", "flag": "🇦🇺",
        "attractions": ["오페라하우스", "하버브릿지", "본다이 비치", "블루마운틴"],
        "tip": "자외선 지수가 매우 높으므로 선크림과 선글라스 지참을 권장합니다."
    }
}

# 3. 사이드바 여행지 선택
st.sidebar.header("🗺️ 여행지 선택")
selected_city_name = st.sidebar.selectbox(
    "떠나고 싶은 도시를 선택하세요:",
    options=list(TRAVEL_CITIES.keys()),
    index=0
)

city_data = TRAVEL_CITIES[selected_city_name]

# 4. API 데이터 수집 함수 (캐싱 적용)
@st.cache_data(ttl=600)
def fetch_weather(city_en):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_en}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=600)
def fetch_exchange():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/KRW"
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

@st.cache_data(ttl=3600)
def fetch_historical_rates(currency_code, days=30):
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={currency_code}&to=KRW"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            rates_history = data.get("rates", {})
            records = [{"날짜": d, "환율(KRW)": val.get("KRW")} for d, val in rates_history.items()]
            df = pd.DataFrame(records)
            if not df.empty:
                df["날짜"] = pd.to_datetime(df["날짜"])
                df = df.sort_values("날짜").set_index("날짜")
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

weather = fetch_weather(city_data["city_en"])
exchange = fetch_exchange()

# -------------------------------------------------------------
# [섹션 1] 도시명 & 시차 / 실시간 시각
# -------------------------------------------------------------
kst_now = datetime.now(ZoneInfo("Asia/Seoul"))
local_now = datetime.now(ZoneInfo(city_data["timezone"]))

time_diff = (local_now.utcoffset() - kst_now.utcoffset()).total_seconds() / 3600
time_diff_str = f"한국보다 {abs(int(time_diff))}시간 느림" if time_diff < 0 else (
    f"한국보다 {int(time_diff)}시간 빠름" if time_diff > 0 else "한국과 시차 없음"
)

st.header(f"{city_data['flag']} {selected_city_name}")

header_col1, header_col2 = st.columns(2)
with header_col1:
    st.metric("⏰ 현지 현재 시각", local_now.strftime("%m월 %d일 %H:%M"), delta=time_diff_str)
with header_col2:
    st.metric("🇰🇷 서울 기준 시각", kst_now.strftime("%m월 %d일 %H:%M"))

st.markdown("---")

# -------------------------------------------------------------
# [섹션 2] 날씨 상세 정보
# -------------------------------------------------------------
st.subheader("🌤️ 현지 실시간 날씨")

if weather and weather.get("main"):
    temp = weather["main"]["temp"]
    feels_like = weather["main"]["feels_like"]
    desc = weather["weather"][0]["description"]
    icon_code = weather["weather"][0]["icon"]
    humidity = weather["main"]["humidity"]
    wind = weather["wind"]["speed"]
    icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

    with st.container(border=True):
        col_icon, col_temp, col_detail1, col_detail2 = st.columns([1, 1.5, 1.2, 1.2])
        
        with col_icon:
            st.image(icon_url, width=90)
            st.caption(f"**{desc.capitalize()}**")

        with col_temp:
            st.metric(label="현재 기온", value=f"{temp:.1f} °C", delta=f"체감 {feels_like:.1f} °C")

        with col_detail1:
            st.metric(label="💧 습도", value=f"{humidity}%")

        with col_detail2:
            st.metric(label="💨 풍속", value=f"{wind} m/s")
else:
    st.warning("현재 날씨 정보를 불러오지 못했습니다.")

st.markdown("---")

# -------------------------------------------------------------
# [섹션 3] 환율, 계산기, 변동 그래프 및 명소 탭
# -------------------------------------------------------------
tab1, tab2 = st.tabs(["💰 실시간 환율 & 환전 계산기", "📍 추천 명소 & 여행 꿀팁"])

with tab1:
    if exchange and exchange.get("result") == "success":
        rates = exchange.get("conversion_rates", {})
        curr_code = city_data["currency"]
        unit = city_data["unit"]
        
        base_rate = (1 / rates[curr_code]) * unit
        spread_rate = 0.0175  # 은행 마진율 1.75%
        spread_won = base_rate * spread_rate

        cash_buy_raw = base_rate + spread_won
        cash_sell_raw = base_rate - spread_won

        # 상단 3개 메트릭
        c1, c2, c3 = st.columns(3)
        unit_label = f"1 {curr_code}" if unit == 1 else f"{unit} {curr_code}"
        c1.metric(f"📊 매매기준율 ({unit_label})", f"{base_rate:,.2f} 원")
        c2.metric("🔴 현찰 살 때 (기본)", f"{cash_buy_raw:,.2f} 원")
        c3.metric("🔵 현찰 팔 때 (기본)", f"{cash_sell_raw:,.2f} 원")

        # 1) 접이식 계산기 (아코디언)
        with st.expander("🧮 환전 우대율(스프레드) 적용 계산기 열기", expanded=True):
            calc_col1, calc_col2 = st.columns([1, 1.2])

            with calc_col1:
                direction = st.radio(
                    "환전 목적",
                    ["외화 사기 (원화 ➔ 외화 현찰)", "외화 팔기 (남은 외화 ➔ 원화)"],
                    horizontal=True
                )
                
                prefer_rate = st.slider(
                    "환율 우대율 (쿠폰 / 주거래 은행)",
                    min_value=0,
                    max_value=100,
                    value=80,
                    step=5,
                    format="%d%%"
                )

                discounted_spread = spread_won * (1 - (prefer_rate / 100))
                
                if "외화 사기" in direction:
                    applied_rate = base_rate + discounted_spread
                    input_val = st.number_input(f"환전할 외화 금액 ({curr_code})", min_value=10.0, value=500.0, step=50.0)
                    needed_krw = (input_val / unit) * applied_rate
                    raw_needed_krw = (input_val / unit) * cash_buy_raw
                    saved_krw = raw_needed_krw - needed_krw
                else:
                    applied_rate = base_rate - discounted_spread
                    input_val = st.number_input(f"되팔 외화 금액 ({curr_code})", min_value=10.0, value=100.0, step=10.0)
                    needed_krw = (input_val / unit) * applied_rate
                    raw_needed_krw = (input_val / unit) * cash_sell_raw
                    saved_krw = needed_krw - raw_needed_krw

            with calc_col2:
                with st.container(border=True):
                    st.markdown("#### 🧾 최종 계산 결과")
                    st.write(f"• **적용 환율:** `{unit_label} = {applied_rate:,.2f} 원`")
                    
                    if "외화 사기" in direction:
                        st.metric(label="필요한 원화(KRW)", value=f"{needed_krw:,.0f} 원")
                        st.success(f"🎉 기본 환율 대비 약 **{saved_krw:,.0f}원** 우대 절약!")
                    else:
                        st.metric(label="받게 되는 원화(KRW)", value=f"{needed_krw:,.0f} 원")
                        st.info(f"🎉 기본 매도 대비 약 **{saved_krw:,.0f}원** 더 환급!")

                    st.caption("※ 기준 마진율 1.75% 기준이며 은행별 고시 환율에 따라 다를 수 있습니다.")

        # 2) 환율 변동 추이 꺾은선 그래프
        st.markdown("---")
        st.subheader(f"📈 최근 30일 {curr_code} 환율 변동 추이")
        
        hist_df = fetch_historical_rates(curr_code, days=30)
        if not hist_df.empty:
            plot_df = hist_df.copy()
            if unit > 1:
                plot_df["환율(KRW)"] = plot_df["환율(KRW)"] * unit
            
            st.line_chart(plot_df["환율(KRW)"], use_container_width=True)

            min_val = plot_df["환율(KRW)"].min()
            max_val = plot_df["환율(KRW)"].max()
            latest_val = plot_df["환율(KRW)"].iloc[-1]
            first_val = plot_df["환율(KRW)"].iloc[0]
            diff_val = latest_val - first_val

            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("30일 최저 환율", f"{min_val:,.2f} 원")
            m_col2.metric("30일 최고 환율", f"{max_val:,.2f} 원")
            m_col3.metric("30일 전 대비 변동", f"{latest_val:,.2f} 원", delta=f"{diff_val:+,.2f} 원")
        else:
            st.info(f"'{curr_code}' 통화의 과거 시계열 데이터(30일)를 불러오는 중이거나 지원되지 않는 통화입니다.")
    else:
        st.error("환율 정보를 불러올 수 없습니다.")

with tab2:
    st.subheader(f"📍 {selected_city_name} 여행 체크포인트")
    
    col_attr, col_tip = st.columns([1.2, 1])
    with col_attr:
        st.markdown("##### 🏛️ 대표 인기 명소")
        for item in city_data["attractions"]:
            st.markdown(f"- 🚩 **{item}**")
            
    with col_tip:
        st.markdown("##### 💡 현지 여행자 꿀팁")
        st.info(city_data["tip"])