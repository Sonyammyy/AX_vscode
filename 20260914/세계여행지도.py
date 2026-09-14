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
# 0-1. 프리텐다드 레귤러 폰트 로드 & 아이콘 보호 CSS
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
# 2. 내장 지역/도시 데이터베이스 (국내 핫플 동네 & 전 세계 완비)
# -------------------------------------------------------------
COMPREHENSIVE_PLACES_DB = [
    # 국내 주요 도시 및 유명 동네
    {"name": "서울", "en": "Seoul", "currency": "KRW", "lat": 37.5665, "lng": 126.9780, "is_korea": True, "desc": "대한민국 수도"},
    {"name": "부산", "en": "Busan", "currency": "KRW", "lat": 35.1796, "lng": 129.0756, "is_korea": True, "desc": "해양 관광 도시"},
    {"name": "수원", "en": "Suwon", "currency": "KRW", "lat": 37.2636, "lng": 127.0286, "is_korea": True, "desc": "세계문화유산 화성의 도시"},
    {"name": "시흥", "en": "Siheung", "currency": "KRW", "lat": 37.3802, "lng": 126.8029, "is_korea": True, "desc": "갯골생태공원과 배곧신도시"},
    {"name": "제주", "en": "Jeju", "currency": "KRW", "lat": 33.4996, "lng": 126.5312, "is_korea": True, "desc": "에메랄드빛 섬"},
    {"name": "인천", "en": "Incheon", "currency": "KRW", "lat": 37.4563, "lng": 126.7052, "is_korea": True, "desc": "국제공항과 송도국제도시"},
    {"name": "전주", "en": "Jeonju", "currency": "KRW", "lat": 35.8242, "lng": 127.1480, "is_korea": True, "desc": "전통 한옥마을과 미식의 고향"},
    {"name": "강릉", "en": "Gangneung", "currency": "KRW", "lat": 37.7519, "lng": 128.8761, "is_korea": True, "desc": "커피거리와 동해바다"},
    {"name": "경주", "en": "Gyeongju", "currency": "KRW", "lat": 35.8562, "lng": 129.2247, "is_korea": True, "desc": "천년고도 황리단길"},
    
    # 서울/수도권 유명 동네
    {"name": "연남동", "en": "Seoul", "currency": "KRW", "lat": 37.5615, "lng": 126.9248, "is_korea": True, "desc": "경의선 숲길 감성 카페 골목"},
    {"name": "성수동", "en": "Seoul", "currency": "KRW", "lat": 37.5445, "lng": 127.0560, "is_korea": True, "desc": "트렌디 팝업스토어와 카페 성지"},
    {"name": "행궁동", "en": "Suwon", "currency": "KRW", "lat": 37.2855, "lng": 127.0142, "is_korea": True, "desc": "수원 화성 행리단길"},
    {"name": "해운대", "en": "Busan", "currency": "KRW", "lat": 35.1588, "lng": 129.1604, "is_korea": True, "desc": "오션뷰와 해변열차 명소"},
    {"name": "판교", "en": "Seongnam", "currency": "KRW", "lat": 37.3948, "lng": 127.1119, "is_korea": True, "desc": "테크노밸리와 아브뉴프랑"},
    
    # 러시아 (모스크바 & 상트페테르부르크)
    {"name": "모스크바", "en": "Moscow", "currency": "RUB", "lat": 55.7558, "lng": 37.6173, "is_korea": False, "desc": "러시아 수도 (붉은 광장)"},
    {"name": "상트페테르부르크", "en": "Saint Petersburg", "currency": "RUB", "lat": 59.9343, "lng": 30.3351, "is_korea": False, "desc": "에르미타주와 문화의 도시"},
    {"name": "블라디보스토크", "en": "Vladivostok", "currency": "RUB", "lat": 43.1155, "lng": 131.8855, "is_korea": False, "desc": "가장 가까운 유럽 항구도시"},
    
    # 아시아 & 유럽 & 미주
    {"name": "도쿄", "en": "Tokyo", "currency": "JPY", "lat": 35.6762, "lng": 139.6503, "is_korea": False, "desc": "일본 수도"},
    {"name": "오사카", "en": "Osaka", "currency": "JPY", "lat": 34.6937, "lng": 135.5023, "is_korea": False, "desc": "도톤보리와 미식의 천국"},
    {"name": "후쿠오카", "en": "Fukuoka", "currency": "JPY", "lat": 33.5904, "lng": 130.4017, "is_korea": False, "desc": "돈코츠 라멘의 본고장"},
    {"name": "삿포로", "en": "Sapporo", "currency": "JPY", "lat": 43.0618, "lng": 141.3545, "is_korea": False, "desc": "눈축제와 맥주의 도시"},
    {"name": "베이징", "en": "Beijing", "currency": "CNY", "lat": 39.9042, "lng": 116.4074, "is_korea": False, "desc": "자금성과 만리장성"},
    {"name": "상하이", "en": "Shanghai", "currency": "CNY", "lat": 31.2304, "lng": 121.4737, "is_korea": False, "desc": "와이탄 야경과 마천루"},
    {"name": "청도", "en": "Qingdao", "currency": "CNY", "lat": 36.0671, "lng": 120.3826, "is_korea": False, "desc": "칭다오 맥주와 해변"},
    {"name": "파리", "en": "Paris", "currency": "EUR", "lat": 48.8566, "lng": 2.3522, "is_korea": False, "desc": "에펠탑과 예술의 수도"},
    {"name": "런던", "en": "London", "currency": "GBP", "lat": 51.5074, "lng": -0.1278, "is_korea": False, "desc": "빅벤과 템스강"},
    {"name": "뉴욕", "en": "New York", "currency": "USD", "lat": 40.7128, "lng": -74.0060, "is_korea": False, "desc": "맨해튼과 타임스퀘어"},
    {"name": "시드니", "en": "Sydney", "currency": "AUD", "lat": -33.8688, "lng": 151.2093, "is_korea": False, "desc": "오페라하우스와 하버"},
]

# 해외 대표 맛집/카페 좌표 DB
OVERSEAS_PLACES_DB = {
    "모스크바": [
        {"name": "화이트 래빗 (White Rabbit)", "category": "레스토랑", "lat": 55.7482, "lng": 37.5835, "desc": "글래스 돔에서 시내를 내려다보는 월드 50 파인다이닝"},
        {"name": "카페 푸시킨 (Кафе Пушкинъ)", "category": "레스토랑", "lat": 55.7645, "lng": 37.6045, "desc": "19세기 귀족 저택 분위기에서 맛보는 최상급 비프 스트로가노프"},
        {"name": "스톨로바야 57 (Столовая 57)", "category": "레스토랑", "lat": 55.7548, "lng": 37.6215, "desc": "굼(GUM) 백화점 내 위치한 정겨운 소련식 뷔페 식당"},
        {"name": "더블비 커피 (Double B 아르바트)", "category": "카페", "lat": 55.7505, "lng": 37.5925, "desc": "바리스타 챔피언들이 내리는 스페셜티 커피"},
        {"name": "코페마니아 (Coffeomania)", "category": "카페", "lat": 55.7602, "lng": 37.6185, "desc": "시그니처 라프 커피(Raf)와 디저트 명소"}
    ],
    "상트페테르부르크": [
        {"name": "문학 카페 (Литературное кафе)", "category": "레스토랑", "lat": 59.9362, "lng": 30.3185, "desc": "푸시킨이 즐겨 찾았던 유서 깊은 러시아 정통 레스토랑"},
        {"name": "테레목 (Теремок)", "category": "레스토랑", "lat": 59.9345, "lng": 30.3342, "desc": "연어와 캐비어가 들어간 즉석 크레페(블리니)와 보르시"},
        {"name": "세베르 메트로폴", "category": "카페", "lat": 59.9348, "lng": 30.3325, "desc": "1903년 개업한 가장 오래된 고전 제과점"}
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
# 3. 절대 멈추지 않는 지능형 검색 함수 (내장 DB + 카카오 실시간 검색)
# -------------------------------------------------------------
def search_places_bulletproof(query_text):
    q = query_text.strip()
    if not q:
        q = "서울"
    
    matches = []
    
    # 1. 내장 DB에서 부분 일치 우선 검색 (무조건 1순위로 즉시 반환)
    for item in COMPREHENSIVE_PLACES_DB:
        if q.lower() in item["name"].lower() or q.lower() in item["en"].lower():
            label = f"{'🇰🇷' if item['is_korea'] else '✈️'} {item['name']} ({item['desc']})"
            matches.append({
                "label": label,
                "name": item["name"],
                "currency": item["currency"],
                "lat": item["lat"],
                "lng": item["lng"],
                "is_korea": item["is_korea"]
            })
            if len(matches) >= 6:
                return matches

    # 2. 내장 DB에 없는 세부 동네/지명인 경우 카카오 API로 실시간 검색
    if KAKAO_MAP_API_KEY:
        try:
            url = "https://dapi.kakao.com/v2/local/search/keyword.json"
            headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
            res = requests.get(url, headers=headers, params={"query": q, "size": 5}, timeout=3)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                for d in docs:
                    p_name = d.get("place_name")
                    addr = d.get("road_address_name") or d.get("address_name") or ""
                    matches.append({
                        "label": f"🇰🇷 {p_name} ({addr})",
                        "name": p_name,
                        "currency": "KRW",
                        "lat": float(d.get("y")),
                        "lng": float(d.get("x")),
                        "is_korea": True
                    })
                if matches:
                    return matches
        except Exception:
            pass

    # 3. 모든 통신 실패 시 서울 기본값 보장
    if not matches:
        first = COMPREHENSIVE_PLACES_DB[0]
        matches.append({
            "label": f"🇰🇷 {first['name']} ({first['desc']})",
            "name": first["name"],
            "currency": first["currency"],
            "lat": first["lat"],
            "lng": first["lng"],
            "is_korea": True
        })
        
    return matches

# -------------------------------------------------------------
# 4. 사이드바 구성
# -------------------------------------------------------------
st.sidebar.markdown("## 🔍 여행지/동네 검색")

user_input = st.sidebar.text_input(
    "떠나고 싶은 지역을 입력하세요:",
    value="서울",
    help="국내 모든 동네(시흥, 연남동, 성수동, 해운대 등)와 해외 도시(모스크바, 파리 등)를 검색해보세요."
).strip()

suggestions = search_places_bulletproof(user_input)

st.sidebar.markdown("👇 **검색된 지역 선택:**")
labels = [s["label"] for s in suggestions]
chosen_label = st.sidebar.radio("추천 목록:", labels, index=0, label_visibility="collapsed")

place_info = next(s for s in suggestions if s["label"] == chosen_label)
selected_place_name = place_info["label"]

final_curr = st.sidebar.text_input("통화 단위:", value=place_info["currency"]).strip().upper()
place_info["currency"] = final_curr if final_curr else place_info["currency"]

# -------------------------------------------------------------
# 5. 맛집/카페 검색 & 날씨/환율 함수
# -------------------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_wiki_image(query_name):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "generator": "search",
        "gsrsearch": query_name,
        "gsrlimit": 1,
        "pithumbsize": 600
    }
    headers = {"User-Agent": "TravelDashboardApp/1.0"}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=4)
        if res.status_code == 200:
            pages = res.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                if "thumbnail" in page:
                    return page["thumbnail"]["source"]
    except Exception:
        pass
    return "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=80"

@st.cache_data(ttl=1800)
def fetch_korea_local_places(lat, lng, query_keyword, category_type="restaurant", size=4):
    """국내 장소: 카카오 API를 통해 해당 동네/좌표 기준 랭킹 맛집/카페 실시간 호출"""
    if not KAKAO_MAP_API_KEY:
        return []
    
    cat_code = "FD6" if category_type == "restaurant" else "CE7"
    label_text = "레스토랑" if category_type == "restaurant" else "카페"
    keyword = f"{query_keyword} {'맛집' if category_type == 'restaurant' else '카페'}"

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
    
    # 1. 반경 5km 내 검색 시도
    params = {
        "query": keyword,
        "category_group_code": cat_code,
        "x": str(lng),
        "y": str(lat),
        "radius": 5000,
        "sort": "accuracy",
        "size": size
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=4)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if not docs:
                # 반경 해제 후 키워드 직접 검색
                res = requests.get(url, headers=headers, params={"query": keyword, "category_group_code": cat_code, "size": size}, timeout=4)
                docs = res.json().get("documents", []) if res.status_code == 200 else []
                
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
            return places
    except Exception:
        pass
    return []

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
# 6. 대시보드 상단 (지도 및 맛집/카페 렌더링)
# -------------------------------------------------------------
st.title(f"📍 {selected_place_name}")

lat = place_info["lat"]
lng = place_info["lng"]
clean_name = place_info["name"]

st.markdown("##### 🗺️ 위치 지도 & 🍽️ 주변 맛집/카페 탐색")

place_filter = st.radio(
    "지도에 표시할 장소 선택:",
    ["🏙️ 중심 위치만 보기", "🍽️ 레스토랑 랭킹 보기", "☕ 인기 카페 랭킹 보기", "✨ 전체 모아보기"],
    horizontal=True
)

selected_places = []

if place_filter != "🏙️ 중심 위치만 보기":
    if place_info.get("is_korea"):
        # 대한민국 모든 동네: 카카오 실시간 랭킹 검색
        if "레스토랑" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_korea_local_places(lat, lng, clean_name, "restaurant", size=3))
        if "카페" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_korea_local_places(lat, lng, clean_name, "cafe", size=3))
    else:
        # 해외 도시: OVERSEAS_PLACES_DB 매칭
        matched_overseas = None
        for k in OVERSEAS_PLACES_DB.keys():
            if k in clean_name or k in selected_place_name:
                matched_overseas = k
                break
        if matched_overseas:
            items = OVERSEAS_PLACES_DB[matched_overseas]
            if "레스토랑" in place_filter:
                selected_places = [p for p in items if p["category"] == "레스토랑"]
            elif "카페" in place_filter:
                selected_places = [p for p in items if p["category"] == "카페"]
            elif "전체" in place_filter:
                selected_places = items

# 지도 데이터프레임 구성
map_rows = [{"lat": lat, "lon": lng}]
for p in selected_places:
    map_rows.append({"lat": p["lat"], "lon": p["lng"]})

map_df = pd.DataFrame(map_rows)
st.map(map_df, zoom=13 if place_info.get("is_korea") else 12)

# 장소 카드 출력
if selected_places:
    title_suffix = "카카오맵 실시간 랭킹" if place_info.get("is_korea") else "대표 추천"
    st.markdown(f"**🌟 {clean_name} {title_suffix} 장소 ({len(selected_places)}곳):**")
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
                st.markdown(f"[🔗 구글 지도에서 위치 확인](https://www.google.com/maps/search/{pl['name']})")
elif place_filter != "🏙️ 중심 위치만 보기":
    st.info(f"ℹ️ {clean_name} 주변의 등록된 장소 데이터를 탐색 중입니다.")

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
# 9. 주요 도시별 심층 여행 가이드 데이터베이스
# -------------------------------------------------------------
TRAVEL_GUIDE_DB = {
    "모스크바": {
        "spots": [
            {"name": "Saint Basil's Cathedral", "kr_name": "붉은 광장 & 성 바실리 대성당", "desc": "러시아의 심장이자 알록달록한 동화 속 양파 돔 성당"},
            {"name": "Moscow Kremlin", "kr_name": "크렘린 궁전 & 무명용사의 묘", "desc": "황금빛 돔의 성당 군락과 영원의 불꽃이 타오르는 역사적 요새"},
            {"name": "GUM Department Store", "kr_name": "굼(GUM) 백화점 & 참새언덕", "desc": "유리 아케이드 건축미, 명물 아이스크림과 모스크바 전경 조망"}
        ],
        "stays": [
            {"area": "트베르스카야 대로", "type": "비즈니스 & 관광 중심", "desc": "붉은 광장까지 도보 이동 가능 및 대형 쇼핑가"},
            {"area": "아르바트 거리", "type": "문화 예술 보행자 거리", "desc": "빅토르 최 추모벽, 기념품점, 카페가 밀집한 활기찬 거리"}
        ],
        "foods": [
            {"name": "비프 스트로가노프", "desc": "부드러운 소고기를 사워크림 소스에 졸여 매시트포테이토와 즐기는 요리"},
            {"name": "펠메니 (러시아식 만두)", "desc": "다진 고기 소를 채워 빚은 후 스메타나를 곁들여 먹는 국민 음식"}
        ],
        "tips": [
            "모스크바 지하철역들은 '지하 궁전'처럼 꾸며져 있어 메트로 투어를 추천합니다.",
            "교통카드 '트로이카(Troika)'를 구매해 충전하면 매우 저렴합니다."
        ]
    },
    "상트페테르부르크": {
        "spots": [
            {"name": "Hermitage Museum", "kr_name": "에르미타주 미술관 (겨울궁전)", "desc": "세계 3대 박물관 중 하나이자 제정 러시아 궁전의 극치"},
            {"name": "Church of the Savior on Blood", "kr_name": "피의 구원 성당", "desc": "화려한 모자이크 벽화로 둘러싸인 성당"},
            {"name": "Nevsky Prospekt", "kr_name": "네프스키 대로 & 카잔 대성당", "desc": "로마 베드로 대성당을 본뜬 웅장한 건축"}
        ],
        "stays": [
            {"area": "네프스키 대로", "type": "관광 최적", "desc": "겨울궁전 및 운하 유람선 선착장 도보 이동"},
            {"area": "폰탄카 운하 주변", "type": "클래식 감성", "desc": "운하 뷰가 아름다운 유럽풍 호텔"}
        ],
        "foods": [
            {"name": "보르시", "desc": "비트를 넣은 붉은 수프와 사워크림"},
            {"name": "블리니", "desc": "연어와 캐비어를 싸 먹는 얇은 팬케이크"}
        ],
        "tips": [
            "백야 축제 기간(5월 말~7월) 네바강 도개교 행사는 필수 코스입니다."
        ]
    },
    "도쿄": {
        "spots": [
            {"name": "Sensō-ji", "kr_name": "센소지 & 아사쿠사", "desc": "도쿄 최고(最古)의 사찰과 전통 상점가 나카미세도리"},
            {"name": "Shibuya Sky", "kr_name": "시부야 스카이 & 스크램블", "desc": "도쿄 타워와 후지산까지 보이는 360도 파노라마 루프탑"}
        ],
        "stays": [
            {"area": "신주쿠 / 시부야", "type": "교통 & 번화가 중심", "desc": "쇼핑, 맛집, 근교 이동 최적"}
        ],
        "foods": [
            {"name": "츠케멘 & 라멘", "desc": "진한 육수에 면을 찍어 먹는 츠케멘"}
        ],
        "tips": [
            "도쿄 서브웨이 티켓으로 교통비를 대폭 절약할 수 있습니다."
        ]
    },
    "파리": {
        "spots": [
            {"name": "Eiffel Tower", "kr_name": "에펠탑 & 샹드마르스", "desc": "파리의 영원한 상징과 화이트 에펠 조명 쇼"},
            {"name": "Louvre Museum", "kr_name": "루브르 박물관", "desc": "모나리자를 비롯한 인류 예술의 보고"}
        ],
        "stays": [
            {"area": "1~8구 (중심가)", "type": "관광 최적", "desc": "도보 이동 편리 및 안전"}
        ],
        "foods": [
            {"name": "크루아상 & 바게트", "desc": "동네 불랑제리의 겉바속촉 빵"}
        ],
        "tips": [
            "박물관은 공식 웹사이트 사전 시간 예약이 필수입니다."
        ]
    },
    "서울": {
        "spots": [
            {"name": "Gyeongbokgung", "kr_name": "경복궁 & 북촌한옥마을", "desc": "조선의 정궁이자 고즈넉한 전통 한옥 골목과 카페 거리"},
            {"name": "N Seoul Tower", "kr_name": "N서울타워", "desc": "서울 360도 파노라마 야경 명소"}
        ],
        "stays": [
            {"area": "명동 / 을지로", "type": "환승 요충지", "desc": "지하철 2·3·4호선 접근성 최상"}
        ],
        "foods": [
            {"name": "K-바비큐 (숙성 삼겹살)", "desc": "숯불 불판에 구워 쌈채소와 즐기는 한국 대표 외식"}
        ],
        "tips": [
            "한복 착용 시 4대 궁궐 무료입장이 가능합니다."
        ]
    },
    "부산": {
        "spots": [
            {"name": "Haeundae Beach", "kr_name": "해운대 & 블루라인파크", "desc": "해변 열차와 스카이캡슐을 즐길 수 있는 오션뷰 핫플레이스"},
            {"name": "Gamcheon Culture Village", "kr_name": "감천문화마을", "desc": "알록달록한 계단식 주택과 어린왕자 포토존"}
        ],
        "stays": [
            {"area": "해운대 / 광안리", "type": "오션뷰 숙소", "desc": "바다 전망과 힐링 인프라"}
        ],
        "foods": [
            {"name": "부산 돼지국밥 & 밀면", "desc": "진한 사골 육수 국밥과 쫄깃한 밀면"}
        ],
        "tips": [
            "스카이캡슐은 주말 사전 예매가 필수입니다."
        ]
    }
}

# -------------------------------------------------------------
# 10. 화면 렌더링 (가이드 탭)
# -------------------------------------------------------------
st.markdown("---")
st.subheader(f"🪻 {clean_name} 핵심 가이드")

matched_guide_key = None
for key in TRAVEL_GUIDE_DB.keys():
    if key in clean_name or key in selected_place_name:
        matched_guide_key = key
        break

if matched_guide_key:
    guide = TRAVEL_GUIDE_DB[matched_guide_key]
    tab_spot, tab_stay, tab_food, tab_tip = st.tabs(["🏛️ 추천 명소", "🏨 추천 숙소", "🍜 대표 먹거리", "💡 여행 꿀팁"])
    
    with tab_spot:
        cols = st.columns(len(guide["spots"]))
        for idx, spot in enumerate(guide["spots"]):
            with cols[idx]:
                img_query = spot.get("name", spot.get("kr_name", ""))
                img_url = fetch_wiki_image(img_query)
                st.image(img_url, use_container_width=True)
                title = spot.get("kr_name", spot.get("name"))
                st.markdown(f"##### **{title}**")
                st.write(spot["desc"])
                
    with tab_stay:
        cols = st.columns(len(guide["stays"]))
        for idx, stay in enumerate(guide["stays"]):
            with cols[idx]:
                st.markdown(f"##### **{stay['area']}**")
                st.caption(f"추천 유형: {stay['type']}")
                st.write(stay["desc"])
                
    with tab_food:
        cols = st.columns(len(guide["foods"]))
        for idx, food in enumerate(guide["foods"]):
            with cols[idx]:
                st.markdown(f"##### **{food['name']}**")
                st.write(food["desc"])
                
    with tab_tip:
        for idx, tip in enumerate(guide["tips"], 1):
            st.info(f"**Tip {idx}:** {tip}")
else:
    st.info(f"선택하신 **{clean_name}**의 검증된 상세 가이드 및 외부 바로가기를 제공합니다.")

st.markdown("##### 🔍 더 알아보기 (실시간 정보 바로가기)")
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.link_button("📍 구글 지도에서 명소/맛집 보기", f"https://www.google.com/maps/search/{clean_name}+맛집")
with b_col2:
    st.link_button("🏨 아고다 숙소 최저가 검색", f"https://www.agoda.com/search?city={clean_name}")
with b_col3:
    st.link_button("✈️ 트립어드바이저 여행 후기", f"https://www.tripadvisor.com/Search?q={clean_name}")