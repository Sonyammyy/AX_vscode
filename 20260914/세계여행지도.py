import os
import re
import base64
from pathlib import Path
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# -------------------------------------------------------------
# 0. 로컬(VSCode) 환경 변수 로드 (.env 탐색)
# -------------------------------------------------------------
current_dir = Path(__file__).resolve().parent
parent_env_path = current_dir.parent / ".env"

if parent_env_path.exists():
    load_dotenv(dotenv_path=parent_env_path)
else:
    load_dotenv(find_dotenv())

st.set_page_config(page_title="세계 여행 대시보드", layout="wide", page_icon="✈️")

# -------------------------------------------------------------
# 0-1. 프리텐다드 폰트 및 라벤더 테마 CSS
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
# 1. API 키 로드 (VSCode .env 우선, 배포 환경 Streamlit Secrets 차순위)
# -------------------------------------------------------------
def get_secret(key_name):
    # 1. VSCode 로컬 환경 (.env 파일) 우선 확인
    env_val = os.getenv(key_name, "").strip()
    if env_val:
        return env_val
    # 2. 배포 환경 (Streamlit Cloud Secrets) 확인
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
    except Exception:
        pass
    return ""

EXCHANGERATE_API_KEY = get_secret("EXCHANGERATE_API_KEY")
OPENWEATHER_API_KEY = get_secret("OPENWEATHER_API_KEY")
KAKAO_MAP_API_KEY = get_secret("KAKAO_MAP_API_KEY")

# -------------------------------------------------------------
# 2. 해외 대표 도시 사전
# -------------------------------------------------------------
OVERSEAS_CITY_DB = [
    {"ko": "모스크바", "en": "Moscow", "country": "RU", "currency": "RUB", "lat": 55.7558, "lng": 37.6173, "desc": "러시아 수도 (붉은 광장)"},
    {"ko": "상트페테르부르크", "en": "Saint Petersburg", "country": "RU", "currency": "RUB", "lat": 59.9343, "lng": 30.3351, "desc": "에르미타주와 운하"},
    {"ko": "도쿄", "en": "Tokyo", "country": "JP", "currency": "JPY", "lat": 35.6762, "lng": 139.6503, "desc": "일본 수도"},
    {"ko": "오사카", "en": "Osaka", "country": "JP", "currency": "JPY", "lat": 34.6937, "lng": 135.5023, "desc": "도톤보리와 미식"},
    {"ko": "파리", "en": "Paris", "country": "FR", "currency": "EUR", "lat": 48.8566, "lng": 2.3522, "desc": "에펠탑과 예술"},
    {"ko": "런던", "en": "London", "country": "GB", "currency": "GBP", "lat": 51.5074, "lng": -0.1278, "desc": "빅벤과 템스강"},
    {"ko": "뉴욕", "en": "New York", "country": "US", "currency": "USD", "lat": 40.7128, "lng": -74.0060, "desc": "맨해튼 타임스퀘어"},
    {"ko": "시드니", "en": "Sydney", "country": "AU", "currency": "AUD", "lat": -33.8688, "lng": 151.2093, "desc": "오페라하우스와 하버"},
]

OVERSEAS_PLACES_DB = {
    "모스크바": [
        {"name": "화이트 래빗 (White Rabbit)", "category": "레스토랑", "lat": 55.7482, "lng": 37.5835, "desc": "글래스 돔에서 시내를 내려다보는 파인다이닝"},
        {"name": "카페 푸시킨 (Кафе Пушкинъ)", "category": "레스토랑", "lat": 55.7645, "lng": 37.6045, "desc": "19세기 귀족 저택 분위기의 비프 스트로가노프"},
        {"name": "스톨로바야 57 (Столовая 57)", "category": "레스토랑", "lat": 55.7548, "lng": 37.6215, "desc": "굼(GUM) 백화점 내 소련식 뷔페 식당"},
        {"name": "더블비 커피 (Double B)", "category": "카페", "lat": 55.7505, "lng": 37.5925, "desc": "러시아 대표 감성 스페셜티 카페"},
        {"name": "코페마니아 (Coffeomania)", "category": "카페", "lat": 55.7602, "lng": 37.6185, "desc": "부드러운 시그니처 라프 커피(Raf)"}
    ],
    "상트페테르부르크": [
        {"name": "문학 카페 (Литературное кафе)", "category": "레스토랑", "lat": 59.9362, "lng": 30.3185, "desc": "푸시킨의 단골 러시아 정통 레스토랑"},
        {"name": "테레목 (Теремок)", "category": "레스토랑", "lat": 59.9345, "lng": 30.3342, "desc": "연어와 캐비어를 넣은 즉석 팬케이크(블리니)"}
    ],
    "도쿄": [
        {"name": "스시 다이와 (도요스)", "category": "레스토랑", "lat": 35.6454, "lng": 139.7915, "desc": "수산시장 직송 제철 오마카세 스시"},
        {"name": "이치란 라멘 (시부야점)", "category": "레스토랑", "lat": 35.6612, "lng": 139.7008, "desc": "진한 돈코츠 라멘"},
        {"name": "푸글렌 도쿄 (아사쿠사)", "category": "카페", "lat": 35.7145, "lng": 139.7942, "desc": "북유럽 감성의 빈티지 카페"}
    ],
    "파리": [
        {"name": "르 불롱제 (Le Bouillon Chartier)", "category": "레스토랑", "lat": 48.8718, "lng": 2.3432, "desc": "100년 역사의 프랑스 전통 가정식"},
        {"name": "카페 드 플로르 (Café de Flore)", "category": "카페", "lat": 48.8542, "lng": 2.3325, "desc": "사르트르와 카뮈의 문학 카페"}
    ]
}

# -------------------------------------------------------------
# 3. 국내 위치 검색 함수 (카카오 API)
# -------------------------------------------------------------
def search_korea_location(query_text):
    q = query_text.strip()
    if not q or not KAKAO_MAP_API_KEY:
        return []
    
    headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
    results = []

    # 1차 키워드 검색
    try:
        url_kw = "https://dapi.kakao.com/v2/local/search/keyword.json"
        res_kw = requests.get(url_kw, headers=headers, params={"query": q, "size": 5}, timeout=4)
        if res_kw.status_code == 200:
            for d in res_kw.json().get("documents", []):
                p_name = d.get("place_name")
                addr = d.get("road_address_name") or d.get("address_name") or ""
                results.append({
                    "label": f"🇰🇷 {p_name} ({addr})",
                    "display_name": p_name,
                    "lat": float(d.get("y")),
                    "lng": float(d.get("x")),
                    "is_korea": True,
                    "currency": "KRW"
                })
    except Exception:
        pass

    # 2차 주소 검색 (지번, 행정동 보완)
    if not results:
        try:
            url_addr = "https://dapi.kakao.com/v2/local/search/address.json"
            res_addr = requests.get(url_addr, headers=headers, params={"query": q, "size": 5}, timeout=4)
            if res_addr.status_code == 200:
                for d in res_addr.json().get("documents", []):
                    addr_name = d.get("address_name")
                    results.append({
                        "label": f"🇰🇷 {q} ({addr_name})",
                        "display_name": q,
                        "lat": float(d.get("y")),
                        "lng": float(d.get("x")),
                        "is_korea": True,
                        "currency": "KRW"
                    })
        except Exception:
            pass

    return results

def search_overseas_places(query_text):
    q = query_text.strip()
    if not q:
        q = "모스크바"
    
    matches = []
    for item in OVERSEAS_CITY_DB:
        if q.lower() in item["ko"].lower() or q.lower() in item["en"].lower():
            matches.append({
                "label": f"✈️ {item['ko']} ({item['en']}, {item['country']})",
                "display_name": item["ko"],
                "currency": item["currency"],
                "lat": item["lat"],
                "lng": item["lng"],
                "is_korea": False
            })
            if len(matches) >= 5:
                return matches

    if OPENWEATHER_API_KEY:
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=5&appid={OPENWEATHER_API_KEY}"
        try:
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                for item in res.json():
                    ko_name = item.get("local_names", {}).get("ko")
                    eng_name = item.get("name", "")
                    country = item.get("country", "")
                    curr_map = {"RU": "RUB", "JP": "JPY", "CN": "CNY", "US": "USD", "FR": "EUR", "GB": "GBP", "AU": "AUD"}
                    matches.append({
                        "label": f"✈️ {ko_name or eng_name} ({country})",
                        "display_name": ko_name or eng_name,
                        "currency": curr_map.get(country, "USD"),
                        "lat": float(item["lat"]),
                        "lng": float(item["lon"]),
                        "is_korea": False
                    })
        except Exception:
            pass

    if not matches:
        first = OVERSEAS_CITY_DB[0]
        matches.append({
            "label": f"✈️ {first['ko']} ({first['desc']})",
            "display_name": first["ko"],
            "currency": first["currency"],
            "lat": first["lat"],
            "lng": first["lng"],
            "is_korea": False
        })
    return matches

# -------------------------------------------------------------
# 4. 사이드바 구성
# -------------------------------------------------------------
st.sidebar.markdown("## 🧭 여행 모드 선택")
travel_mode = st.sidebar.radio("범위를 선택하세요:", ["🇰🇷 국내 여행", "✈️ 해외 여행"], horizontal=True)

place_info = None

if travel_mode == "🇰🇷 국내 여행":
    st.sidebar.markdown("### 🔍 국내 동네/지역 검색")
    korea_query = st.sidebar.text_input(
        "동네명 또는 도로명을 입력하세요:",
        value="서울",
        help="예: 울산 무거동, 연남동, 성수동, 해운대, 서면, 판교 등"
    ).strip()

    suggestions = search_korea_location(korea_query)
    
    if suggestions:
        st.sidebar.markdown("👇 **검색 결과 선택:**")
        labels = [s["label"] for s in suggestions]
        chosen_label = st.sidebar.radio("지역 목록:", labels, index=0, label_visibility="collapsed")
        place_info = next(s for s in suggestions if s["label"] == chosen_label)
    else:
        st.sidebar.warning("검색 결과가 없어 서울로 기본 설정됩니다.")
        place_info = {
            "label": "🇰🇷 서울특별시청", "display_name": "서울", "lat": 37.5665, "lng": 126.9780,
            "is_korea": True, "currency": "KRW"
        }

else:
    st.sidebar.markdown("### 🔍 해외 도시 검색")
    overseas_query = st.sidebar.text_input("도시명을 입력하세요:", value="모스크바").strip()
    suggestions = search_overseas_places(overseas_query)
    labels = [s["label"] for s in suggestions]
    chosen_label = st.sidebar.radio("도시 목록:", labels, index=0, label_visibility="collapsed")
    place_info = next(s for s in suggestions if s["label"] == chosen_label)
    
    final_curr = st.sidebar.text_input("적용 통화:", value=place_info["currency"]).strip().upper()
    place_info["currency"] = final_curr if final_curr else place_info["currency"]

# -------------------------------------------------------------
# 5. 좌표 기반 주변 음식점/카페 반경 수신 함수
# -------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_direct_nearby_places(lat, lng, category_type="restaurant", size=3):
    if not KAKAO_MAP_API_KEY:
        return [], "KAKAO_MAP_API_KEY가 로드되지 않았습니다. .env 파일의 키 설정을 확인하세요."
    
    cat_code = "FD6" if category_type == "restaurant" else "CE7"
    label_text = "레스토랑" if category_type == "restaurant" else "카페"
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
    
    for r in [2000, 5000, 15000]:
        params = {
            "category_group_code": cat_code,
            "x": str(lng),
            "y": str(lat),
            "radius": r,
            "size": size
        }
        try:
            res = requests.get(url, headers=headers, params=params, timeout=5)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                if docs:
                    places = []
                    for d in docs:
                        places.append({
                            "name": d.get("place_name"),
                            "category": label_text,
                            "lat": float(d.get("y")),
                            "lng": float(d.get("x")),
                            "desc": f"📍 {d.get('road_address_name') or d.get('address_name')} | 📞 {d.get('phone') or '전화번호 미등록'}",
                            "url": d.get("place_url")
                        })
                    return places, None
            elif res.status_code in [401, 403]:
                return [], f"카카오 API 키 인증 오류 (Status Code: {res.status_code})."
        except Exception as e:
            return [], f"카카오 API 통신 오류: {str(e)}"
            
    return [], "해당 위치 주변에 등록된 장소가 없습니다."

@st.cache_data(ttl=600)
def fetch_weather(lat, lng):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url, timeout=4)
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
# 6. 지도 및 레스토랑 3개, 카페 3개 출력
# -------------------------------------------------------------
st.title(f"📍 {place_info['label']}")

lat = place_info["lat"]
lng = place_info["lng"]
clean_title = place_info["display_name"]

st.markdown("##### 🗺️ 위치 지도 & 🍽️ 주변 레스토랑 3개 / 카페 3개")

selected_places = []
api_error_msg = None

if place_info.get("is_korea"):
    rests, err1 = fetch_direct_nearby_places(lat, lng, "restaurant", size=3)
    if rests:
        selected_places.extend(rests)
    elif err1:
        api_error_msg = err1

    cafes, err2 = fetch_direct_nearby_places(lat, lng, "cafe", size=3)
    if cafes:
        selected_places.extend(cafes)
    elif err2 and not api_error_msg:
        api_error_msg = err2
else:
    matched_overseas = None
    for k in OVERSEAS_PLACES_DB.keys():
        if k in clean_title or k in place_info["label"]:
            matched_overseas = k
            break
    if matched_overseas:
        selected_places = OVERSEAS_PLACES_DB[matched_overseas]

# 지도 데이터프레임 구성
map_rows = [{"lat": lat, "lon": lng}]
for p in selected_places:
    map_rows.append({"lat": p["lat"], "lon": p["lng"]})

st.map(pd.DataFrame(map_rows), zoom=14 if place_info.get("is_korea") else 12)

# 장소 카드 출력
if selected_places:
    st.markdown(f"**🌟 {clean_title} 주변 추천 장소 ({len(selected_places)}곳):**")
    
    res_list = [p for p in selected_places if p["category"] == "레스토랑"]
    if res_list:
        st.markdown("##### 🍽️ 주변 레스토랑 (3곳)")
        r_cols = st.columns(len(res_list))
        for idx, pl in enumerate(res_list):
            with r_cols[idx]:
                st.markdown(f"**{pl['name']}**")
                st.write(pl.get("desc", ""))
                if pl.get("url"):
                    st.markdown(f"[🔗 카카오맵 길찾기]({pl['url']})")
                else:
                    st.markdown(f"[🔗 구글 지도 길찾기](https://www.google.com/maps/search/{pl['name']})")

    cafe_list = [p for p in selected_places if p["category"] == "카페"]
    if cafe_list:
        st.markdown("##### ☕ 주변 카페 (3곳)")
        c_cols = st.columns(len(cafe_list))
        for idx, pl in enumerate(cafe_list):
            with c_cols[idx]:
                st.markdown(f"**{pl['name']}**")
                st.write(pl.get("desc", ""))
                if pl.get("url"):
                    st.markdown(f"[🔗 카카오맵 길찾기]({pl['url']})")
                else:
                    st.markdown(f"[🔗 구글 지도 길찾기](https://www.google.com/maps/search/{pl['name']})")
else:
    if api_error_msg:
        st.error(f"⚠️ {api_error_msg}")
    else:
        st.info(f"ℹ️ {clean_title} 주변에 등록된 레스토랑/카페 데이터가 없습니다.")

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

target_curr = place_info["currency"]
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
        st.info("선택하신 지역은 대한민국(KRW)으로 환율이 1:1로 고정됩니다.")
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
# 9. 바로가기 링크 버튼
# -------------------------------------------------------------
st.markdown("---")
st.markdown("##### 🔍 더 알아보기 (실시간 정보 바로가기)")
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.link_button("📍 구글 지도에서 명소/맛집 보기", f"https://www.google.com/maps/search/{clean_title}+맛집")
with b_col2:
    st.link_button("🏨 아고다 숙소 최저가 검색", f"https://www.agoda.com/search?city={clean_title}")
with b_col3:
    st.link_button("✈️ 트립어드바이저 여행 후기", f"https://www.tripadvisor.com/Search?q={clean_title}")