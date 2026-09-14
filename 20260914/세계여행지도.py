import os
import re
import base64
from pathlib import Path
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# -------------------------------------------------------------
# 0. 상위 폴더의 .env 환경 변수 자동 탐색 및 로드
# -------------------------------------------------------------
current_dir = Path(__file__).resolve().parent
parent_env_path = current_dir.parent / ".env"

if parent_env_path.exists():
    load_dotenv(dotenv_path=parent_env_path)
else:
    load_dotenv(find_dotenv())

st.set_page_config(page_title="세계 여행 대시보드", layout="wide", page_icon="✈️")

# -------------------------------------------------------------
# 0-1. 프리텐다드 레귤러 폰트 로드 & 라벤더 감성 CSS
# -------------------------------------------------------------
def get_pretendard_font_css():
    font_extensions = [".woff2", ".woff", ".ttf", ".otf"]
    font_file = None
    
    search_paths = [current_dir, current_dir / "fonts", current_dir / "static"]
    for folder in search_paths:
        if folder.exists():
            for f in folder.iterdir():
                if f.is_file() and any(f.name.lower().endswith(ext) for ext in font_extensions):
                    if "pretendard" in f.name.lower():
                        font_file = f
                        break
            if font_file:
                break

    if font_file:
        ext = font_file.suffix.lower()
        fmt_map = {".woff2": "woff2", ".woff": "woff", ".ttf": "truetype", ".otf": "opentype"}
        fmt = fmt_map.get(ext, "woff2")
        with open(font_file, "rb") as bf:
            b64_font = base64.b64encode(bf.read()).decode()
        font_face_rule = f"""
        @font-face {{
            font-family: 'Pretendard-Regular';
            src: url(data:font/{fmt};charset=utf-8;base64,{b64_font}) format('{fmt}');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }}
        """
    else:
        font_face_rule = """
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
        """

    return f"""
    <style>
        {font_face_rule}

        html, body, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, input, button, select, textarea {{
            font-family: 'Pretendard-Regular', 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        [data-testid="stIcon"], [data-testid="stIcon"] *, [class*="material-symbols"], .material-symbols-rounded, [data-baseweb="icon"] {{
            font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        }}

        .stApp {{
            background: linear-gradient(135deg, #fbfaff 0%, #f4effa 50%, #eee8f8 100%);
            color: #2D2538;
        }}
        
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #f7f3fd 0%, #ede5f8 100%);
            border-right: 1px solid #dfd4f2;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #4C2882 !important;
            font-weight: 700;
        }}
        
        [data-testid="stMetric"] {{
            background: #ffffff;
            padding: 14px 18px;
            border-radius: 14px;
            border: 1px solid #e2d7f5;
            box-shadow: 0 4px 14px rgba(139, 92, 246, 0.08);
        }}
        [data-testid="stMetricLabel"] {{
            color: #6D4C94 !important;
            font-weight: 600;
        }}
        [data-testid="stMetricValue"] {{
            color: #4C2882 !important;
            font-size: 1.45rem !important;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: #ede5f7;
            padding: 6px;
            border-radius: 12px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 8px 18px;
            color: #5B407E;
            font-weight: 600;
            background-color: transparent;
            border: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #8B5CF6 !important;
            color: #ffffff !important;
        }}
        
        [data-testid="stExpander"] {{
            border: 1px solid #dfd3f3 !important;
            border-radius: 12px !important;
            background-color: #ffffff !important;
        }}
        .streamlit-expanderHeader {{
            background-color: #f7f2fc !important;
            border-radius: 10px !important;
            color: #4C2882 !important;
            font-weight: 600 !important;
        }}
        
        div[data-baseweb="slider"] div {{
            color: #7C3AED;
        }}

        div.stLinkButton > a {{
            background-color: #EDE9FE !important;
            color: #5B21B6 !important;
            border: 1px solid #DDD6FE !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease-in-out;
        }}
        div.stLinkButton > a:hover {{
            background-color: #8B5CF6 !important;
            color: #ffffff !important;
            border-color: #7C3AED !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.25);
        }}
        
        img {{
            border-radius: 12px;
        }}
    </style>
    """

st.markdown(get_pretendard_font_css(), unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. API 키 로드
# -------------------------------------------------------------
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "").strip()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
KAKAO_MAP_API_KEY = os.getenv("KAKAO_MAP_API_KEY", "").strip()

# -------------------------------------------------------------
# 2. 전 세계 기본 도시 DB
# -------------------------------------------------------------
GLOBAL_CITY_DB = [
    {"ko": "서울", "en": "Seoul", "country": "KR", "currency": "KRW", "lat": 37.5665, "lng": 126.9780, "is_korea": True},
    {"ko": "부산", "en": "Busan", "country": "KR", "currency": "KRW", "lat": 35.1796, "lng": 129.0756, "is_korea": True},
    {"ko": "수원", "en": "Suwon", "country": "KR", "currency": "KRW", "lat": 37.2636, "lng": 127.0286, "is_korea": True},
    {"ko": "시흥", "en": "Siheung", "country": "KR", "currency": "KRW", "lat": 37.3802, "lng": 126.8029, "is_korea": True},
    {"ko": "제주", "en": "Jeju", "country": "KR", "currency": "KRW", "lat": 33.4996, "lng": 126.5312, "is_korea": True},
    {"ko": "인천", "en": "Incheon", "country": "KR", "currency": "KRW", "lat": 37.4563, "lng": 126.7052, "is_korea": True},
    {"ko": "대구", "en": "Daegu", "country": "KR", "currency": "KRW", "lat": 35.8714, "lng": 128.6014, "is_korea": True},
    {"ko": "전주", "en": "Jeonju", "country": "KR", "currency": "KRW", "lat": 35.8242, "lng": 127.1480, "is_korea": True},

    # 러시아
    {"ko": "모스크바", "en": "Moscow", "country": "RU", "currency": "RUB", "lat": 55.7558, "lng": 37.6173, "is_korea": False},
    {"ko": "상트페테르부르크", "en": "Saint Petersburg", "country": "RU", "currency": "RUB", "lat": 59.9343, "lng": 30.3351, "is_korea": False},
    {"ko": "블라디보스토크", "en": "Vladivostok", "country": "RU", "currency": "RUB", "lat": 43.1155, "lng": 131.8855, "is_korea": False},

    # 해외 주요 도시
    {"ko": "베이징", "en": "Beijing", "country": "CN", "currency": "CNY", "lat": 39.9042, "lng": 116.4074},
    {"ko": "상하이", "en": "Shanghai", "country": "CN", "currency": "CNY", "lat": 31.2304, "lng": 121.4737},
    {"ko": "도쿄", "en": "Tokyo", "country": "JP", "currency": "JPY", "lat": 35.6762, "lng": 139.6503},
    {"ko": "오사카", "en": "Osaka", "country": "JP", "currency": "JPY", "lat": 34.6937, "lng": 135.5023},
    {"ko": "파리", "en": "Paris", "country": "FR", "currency": "EUR", "lat": 48.8566, "lng": 2.3522},
    {"ko": "런던", "en": "London", "country": "GB", "currency": "GBP", "lat": 51.5074, "lng": -0.1278},
    {"ko": "뉴욕", "en": "New York", "country": "US", "currency": "USD", "lat": 40.7128, "lng": -74.0060},
    {"ko": "시드니", "en": "Sydney", "country": "AU", "currency": "AUD", "lat": -33.8688, "lng": 151.2093},
]

# -------------------------------------------------------------
# 3. 실시간 통합 도시 검색
# -------------------------------------------------------------
def search_smart_cities(query_text):
    q = query_text.strip()
    if not q:
        return []
    
    matches = []
    # 1. 내장 DB 우선 확인
    for item in GLOBAL_CITY_DB:
        if q.lower() in item["ko"].lower() or q.lower() in item["en"].lower():
            label = f"✈️ {item['ko']} ({item['en']}, {item['country']})"
            matches.append({
                "label": label,
                "city_query": item["en"],
                "currency": item["currency"],
                "lat": item["lat"],
                "lng": item["lng"],
                "is_korea": item.get("is_korea", False),
                "clean_ko": item["ko"]
            })
            if len(matches) >= 5:
                return matches

    # 2. 한글 검색어인 경우 카카오 로컬 REST API로 국내 지명 자동 탐색
    has_korean = bool(re.search(r'[가-힣]', q))
    if has_korean and KAKAO_MAP_API_KEY:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
        params = {"query": q if "시" in q or "군" in q else f"{q}시청", "size": 3}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=4)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                for d in docs:
                    place_name = d.get("place_name", q)
                    clean_name = re.sub(r'[^가-힣]', '', place_name).replace("시청", "").replace("군청", "").strip()
                    label = f"✈️ {clean_name} ({d.get('address_name')})"
                    matches.append({
                        "label": label,
                        "city_query": "Seoul",
                        "currency": "KRW",
                        "lat": float(d.get("y")),
                        "lng": float(d.get("x")),
                        "is_korea": True,
                        "clean_ko": clean_name
                    })
                if matches:
                    return matches
        except Exception:
            pass

    # 3. 해외 도시인 경우 OpenWeather Geocoding
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=5&appid={OPENWEATHER_API_KEY}"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            for item in res.json():
                ko_name = item.get("local_names", {}).get("ko")
                eng_name = item.get("name", "")
                country = item.get("country", "")
                label = f"✈️ {ko_name} ({eng_name}, {country})" if ko_name else f"✈️ {eng_name} ({country})"
                matches.append({
                    "label": label,
                    "city_query": eng_name,
                    "currency": "USD" if country != "KR" else "KRW",
                    "lat": float(item["lat"]),
                    "lng": float(item["lon"]),
                    "is_korea": (country == "KR"),
                    "clean_ko": ko_name if ko_name else eng_name
                })
    except Exception:
        pass
    return matches

# -------------------------------------------------------------
# 4. 사이드바 구성 (디폴트: 서울)
# -------------------------------------------------------------
st.sidebar.markdown("## 🔍 여행지 검색")

user_input = st.sidebar.text_input(
    "떠나고 싶은 도시를 입력하세요:",
    value="서울",
    help="국내 모든 도시(서울, 부산, 수원, 시흥 등)와 전 세계 도시를 실시간으로 검색할 수 있습니다."
).strip()

suggestions = search_smart_cities(user_input)

if suggestions:
    st.sidebar.markdown("👇 **추천 여행지 (선택):**")
    labels = [s["label"] for s in suggestions]
    chosen_label = st.sidebar.radio("추천 목록:", labels, index=0, label_visibility="collapsed")
    
    city_info = next(s for s in suggestions if s["label"] == chosen_label)
    selected_city_name = city_info["label"].replace("✈️ ", "")
    
    final_curr = st.sidebar.text_input("통화 단위 (자동 연동):", value=city_info["currency"]).strip().upper()
    city_info["currency"] = final_curr if final_curr else city_info["currency"]
else:
    st.sidebar.warning("일치하는 도시가 없습니다.")
    city_info = GLOBAL_CITY_DB[0]
    selected_city_name = "서울 (Seoul, KR)"

# -------------------------------------------------------------
# 5. 카카오 로컬 REST 랭킹 검색 함수 (폴백 디폴트: 서울)
# -------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_kakao_top_ranking_places(search_name, category_type="restaurant", size=4):
    if not KAKAO_MAP_API_KEY:
        return []
    
    korean_part = search_name.split("(")[0]
    pure_city = re.sub(r'[^가-힣]', '', korean_part).strip()
    if not pure_city:
        pure_city = "서울"
    
    if category_type == "restaurant":
        query = f"{pure_city} 맛집"
        category_code = "FD6"
        label_text = "레스토랑"
    else:
        query = f"{pure_city} 카페"
        category_code = "CE7"
        label_text = "카페"
        
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
    params = {
        "query": query,
        "category_group_code": category_code,
        "sort": "accuracy",
        "size": size
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            places = []
            for d in docs:
                places.append({
                    "name": d.get("place_name"),
                    "category": label_text,
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                    "desc": f"📍 {d.get('road_address_name', d.get('address_name'))} | 📞 {d.get('phone') if d.get('phone') else '전화번호 미등록'}",
                    "url": d.get("place_url")
                })
            return places
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_weather(lat, lng):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {
        "main": {"temp": 20.0, "feels_like": 19.5, "humidity": 50},
        "weather": [{"description": "맑음", "icon": "01d"}],
        "wind": {"speed": 2.5},
    }

@st.cache_data(ttl=1800)
def fetch_exchange_rate(target_currency):
    if target_currency == "KRW":
        return 1.0
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/KRW"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("result") == "success":
            rate = data["conversion_rates"].get(target_currency)
            if rate and float(rate) > 0:
                return 1.0 / float(rate)
    except Exception:
        pass
    fallback = {"USD": 1335.0, "EUR": 1450.0, "JPY": 9.12, "RUB": 14.8, "CNY": 185.0}
    return fallback.get(target_currency, 1300.0)

# -------------------------------------------------------------
# 6. 지도 및 레스토랑/카페 렌더링
# -------------------------------------------------------------
st.title(f"✈️ {selected_city_name} 여행 대시보드")

lat = city_info["lat"]
lng = city_info["lng"]

st.markdown("##### 📍 여행지 위치 & 🍽️ 맛집/카페 지도 탐색")

place_filter = st.radio(
    "지도에 표시할 장소 선택:",
    ["🏙️ 도시 중심만 보기", "🍽️ 레스토랑 랭킹 보기", "☕ 인기 카페 랭킹 보기", "✨ 전체 모아보기"],
    horizontal=True
)

selected_places = []

if place_filter != "🏙️ 도시 중심만 보기":
    if city_info.get("is_korea"):
        target_name = city_info.get("clean_ko", selected_city_name)
        if "레스토랑" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(target_name, "restaurant", size=3))
        if "카페" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(target_name, "cafe", size=3))

# 지도 데이터프레임 구성
map_rows = [{"lat": lat, "lon": lng}]
for p in selected_places:
    map_rows.append({"lat": p["lat"], "lon": p["lng"]})

st.map(pd.DataFrame(map_rows), zoom=12)

# 랭킹 카드 출력
if selected_places:
    st.markdown(f"**🌟 카카오맵 랭킹 추천 장소 ({len(selected_places)}곳):**")
    p_cols = st.columns(min(len(selected_places), 3))
    for idx, pl in enumerate(selected_places):
        with p_cols[idx % 3]:
            icon = "🍽️" if pl["category"] == "레스토랑" else "☕"
            st.markdown(f"**{icon} {pl['name']}**")
            st.caption(f"분류: {pl['category']}")
            st.write(pl.get("desc", ""))
            if pl.get("url"):
                st.markdown(f"[🔗 카카오맵에서 길찾기 및 리뷰]({pl['url']})")
            else:
                st.markdown(f"[🔗 구글 지도에서 길찾기](https://www.google.com/maps/search/{pl['name']})")
elif place_filter != "🏙️ 도시 중심만 보기":
    st.info("ℹ️ 해당 도시의 실시간 랭킹 데이터를 수신 중이거나 등록된 매장이 없습니다.")

st.markdown("---")

# -------------------------------------------------------------
# 7. 날씨 및 환율 정보
# -------------------------------------------------------------
col_weather, col_rate = st.columns([1, 1])

with col_weather:
    st.subheader("🌤️ 현지 날씨")
    weather_data = fetch_weather(lat, lng)
    temp = weather_data["main"]["temp"]
    feels_like = weather_data["main"]["feels_like"]
    humidity = weather_data["main"]["humidity"]
    desc = weather_data["weather"][0]["description"]
    icon_code = weather_data["weather"][0].get("icon", "01d")

    w1, w2 = st.columns([1, 2])
    with w1:
        st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png", width=85)
    with w2:
        st.metric(label="현재 기온", value=f"{temp:.1f} °C", delta=f"체감 {feels_like:.1f} °C")

    st.write(f"- **날씨 상태:** {desc}")
    st.write(f"- **현재 습도:** {humidity}%")
    st.write(f"- **풍속:** {weather_data.get('wind', {}).get('speed', 0)} m/s")

target_curr = city_info["currency"]
base_rate = float(fetch_exchange_rate(target_curr))

if "spread_rate" not in st.session_state:
    st.session_state["spread_rate"] = 1.75
if "discount_rate" not in st.session_state:
    st.session_state["discount_rate"] = 80

if target_curr == "KRW":
    actual_spread_amount = 0.0
    cash_buy = 1.0
    cash_sell = 1.0
else:
    basic_spread = base_rate * (st.session_state["spread_rate"] / 100.0)
    actual_spread_amount = basic_spread * (1.0 - (st.session_state["discount_rate"] / 100.0))
    cash_buy = base_rate + actual_spread_amount
    cash_sell = base_rate - actual_spread_amount

with col_rate:
    st.subheader(f"💜 현지 환율 ({target_curr} / KRW)")
    if target_curr == "KRW":
        st.info("선택하신 국가는 대한민국(KRW)으로 환율이 1:1로 고정됩니다.")
        m1, m2, m3 = st.columns(3)
        m1.metric("매매기준율", "1.00원")
        m2.metric("사실 때", "1.00원")
        m3.metric("파실 때", "1.00원")
    else:
        fmt = "{:,.4f}원" if base_rate < 1.0 else "{:,.2f}원"
        m1, m2, m3 = st.columns(3)
        m1.metric("📊 매매기준율", fmt.format(base_rate))
        m2.metric("💵 사실 때 (우대)", fmt.format(cash_buy))
        m3.metric("💴 파실 때 (우대)", fmt.format(cash_sell))

        st.caption(
            f"스프레드 **{st.session_state['spread_rate']}%** | "
            f"우대율 **{st.session_state['discount_rate']}%** 적용 | "
            f"실제 마진: 1 {target_curr}당 {fmt.format(actual_spread_amount)}"
        )

# -------------------------------------------------------------
# 8. 접이식 환율 계산기 (Expander)
# -------------------------------------------------------------
with st.expander(f"환율 계산기 & 은행 우대율 설정 ({target_curr})", expanded=True):
    st.markdown("##### ⚙️ 환율 상세 옵션")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        new_spread = st.slider("스프레드율 (%)", min_value=0.5, max_value=4.0, value=float(st.session_state["spread_rate"]), step=0.05, key="slider_spread")
        st.session_state["spread_rate"] = new_spread
    with s_col2:
        new_discount = st.slider("은행 우대율 (%)", min_value=0, max_value=100, value=int(st.session_state["discount_rate"]), step=5, key="slider_discount")
        st.session_state["discount_rate"] = new_discount

    if target_curr != "KRW":
        basic_spread = base_rate * (st.session_state["spread_rate"] / 100.0)
        actual_spread_amount = basic_spread * (1.0 - (st.session_state["discount_rate"] / 100.0))
        cash_buy = base_rate + actual_spread_amount
        cash_sell = base_rate - actual_spread_amount

    st.markdown("---")
    st.markdown("##### 💵 금액 환전 계산")

    calc_direction = st.radio("환전 방식 선택:", [f"원화(KRW) ➡️ 현지 통화({target_curr}) [사실 때 환율 적용]", f"현지 통화({target_curr}) ➡️ 원화(KRW) [파실 때 환율 적용]"])
    is_krw_to_foreign = "원화(KRW) ➡️" in calc_direction
    amount_input = st.number_input("환전할 금액 입력:", min_value=0.0, value=100000.0 if is_krw_to_foreign else 100.0, step=10.0)

    fmt = "{:,.4f}원" if base_rate < 1.0 else "{:,.2f}원"
    if is_krw_to_foreign:
        converted_result = float(amount_input / cash_buy) if cash_buy > 0 else 0.0
        st.success(f"💜 **{amount_input:,.0f} KRW** ➡️ **{converted_result:,.2f} {target_curr}** (적용 환율: 1 {target_curr} = {fmt.format(cash_buy)})")
    else:
        converted_result = float(amount_input * cash_sell)
        st.success(f"💜 **{amount_input:,.2f} {target_curr}** ➡️ **{converted_result:,.0f} KRW** (적용 환율: 1 {target_curr} = {fmt.format(cash_sell)})")

# -------------------------------------------------------------
# 9. 더 알아보기 (실시간 정보 바로가기)
# -------------------------------------------------------------
st.markdown("---")
st.markdown("##### 🔍 더 알아보기 (실시간 정보 바로가기)")
search_target = city_info.get("clean_ko", selected_city_name)
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.link_button("📍 구글 지도에서 명소/맛집 보기", f"https://www.google.com/maps/search/{search_target}+맛집")
with b_col2:
    st.link_button("🏨 아고다 숙소 최저가 검색", f"https://www.agoda.com/search?city={search_target}")
with b_col3:
    st.link_button("✈️ 트립어드바이저 여행 후기", f"https://www.tripadvisor.com/Search?q={search_target}")