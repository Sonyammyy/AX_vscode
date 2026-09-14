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
    # 대한민국
    {"ko": "서울", "en": "Seoul", "country": "KR", "currency": "KRW", "lat": 37.5665, "lng": 126.9780, "is_korea": True},
    {"ko": "부산", "en": "Busan", "country": "KR", "currency": "KRW", "lat": 35.1796, "lng": 129.0756, "is_korea": True},
    {"ko": "수원", "en": "Suwon", "country": "KR", "currency": "KRW", "lat": 37.2636, "lng": 127.0286, "is_korea": True},
    {"ko": "시흥", "en": "Siheung", "country": "KR", "currency": "KRW", "lat": 37.3802, "lng": 126.8029, "is_korea": True},
    {"ko": "제주", "en": "Jeju", "country": "KR", "currency": "KRW", "lat": 33.4996, "lng": 126.5312, "is_korea": True},
    {"ko": "인천", "en": "Incheon", "country": "KR", "currency": "KRW", "lat": 37.4563, "lng": 126.7052, "is_korea": True},
    {"ko": "대구", "en": "Daegu", "country": "KR", "currency": "KRW", "lat": 35.8714, "lng": 128.6014, "is_korea": True},
    {"ko": "전주", "en": "Jeonju", "country": "KR", "currency": "KRW", "lat": 35.8242, "lng": 127.1480, "is_korea": True},

    # 러시아 (모스크바 포함)
    {"ko": "모스크바", "en": "Moscow", "country": "RU", "currency": "RUB", "lat": 55.7558, "lng": 37.6173, "is_korea": False},
    {"ko": "상트페테르부르크", "en": "Saint Petersburg", "country": "RU", "currency": "RUB", "lat": 59.9343, "lng": 30.3351, "is_korea": False},
    {"ko": "블라디보스토크", "en": "Vladivostok", "country": "RU", "currency": "RUB", "lat": 43.1155, "lng": 131.8855, "is_korea": False},

    # 아시아 & 미주 & 유럽
    {"ko": "도쿄", "en": "Tokyo", "country": "JP", "currency": "JPY", "lat": 35.6762, "lng": 139.6503, "is_korea": False},
    {"ko": "오사카", "en": "Osaka", "country": "JP", "currency": "JPY", "lat": 34.6937, "lng": 135.5023, "is_korea": False},
    {"ko": "후쿠오카", "en": "Fukuoka", "country": "JP", "currency": "JPY", "lat": 33.5904, "lng": 130.4017, "is_korea": False},
    {"ko": "삿포로", "en": "Sapporo", "country": "JP", "currency": "JPY", "lat": 43.0618, "lng": 141.3545, "is_korea": False},
    {"ko": "베이징", "en": "Beijing", "country": "CN", "currency": "CNY", "lat": 39.9042, "lng": 116.4074, "is_korea": False},
    {"ko": "상하이", "en": "Shanghai", "country": "CN", "currency": "CNY", "lat": 31.2304, "lng": 121.4737, "is_korea": False},
    {"ko": "청도", "en": "Qingdao", "country": "CN", "currency": "CNY", "lat": 36.0671, "lng": 120.3826, "is_korea": False},
    {"ko": "파리", "en": "Paris", "country": "FR", "currency": "EUR", "lat": 48.8566, "lng": 2.3522, "is_korea": False},
    {"ko": "런던", "en": "London", "country": "GB", "currency": "GBP", "lat": 51.5074, "lng": -0.1278, "is_korea": False},
    {"ko": "뉴욕", "en": "New York", "country": "US", "currency": "USD", "lat": 40.7128, "lng": -74.0060, "is_korea": False},
    {"ko": "로스앤젤레스", "en": "Los Angeles", "country": "US", "currency": "USD", "lat": 34.0522, "lng": -118.2437, "is_korea": False},
    {"ko": "시드니", "en": "Sydney", "country": "AU", "currency": "AUD", "lat": -33.8688, "lng": 151.2093, "is_korea": False},
]

# -------------------------------------------------------------
# 2-1. 해외 대표 도시별 맛집 & 카페 큐레이션 DB
# -------------------------------------------------------------
OVERSEAS_PLACES_DB = {
    "모스크바": [
        {"name": "카페 푸시킨 (Кафе Пушкинъ)", "category": "레스토랑", "lat": 55.7645, "lng": 37.6045, "desc": "19세기 귀족 저택 서재 분위기에서 맛보는 최상급 비프 스트로가노프"},
        {"name": "화이트 래빗 (White Rabbit)", "category": "레스토랑", "lat": 55.7482, "lng": 37.5835, "desc": "모스크바 시내 파노라마 뷰가 펼쳐지는 글래스 돔의 월드 50 레스토랑"},
        {"name": "스톨로바야 57 (Столовая 57)", "category": "레스토랑", "lat": 55.7548, "lng": 37.6215, "desc": "굼(GUM) 백화점 내 위치한 소련식 뷔페 식당이자 가성비 명소"},
        {"name": "더블비 커피 (Double B 아르바트)", "category": "카페", "lat": 55.7505, "lng": 37.5925, "desc": "러시아 바리스타 챔피언들이 창업한 대표적인 감성 스페셜티 커피 체인"},
        {"name": "코페마니아 (Coffeomania 볼쇼이)", "category": "카페", "lat": 55.7602, "lng": 37.6185, "desc": "부드러운 시그니처 라프 커피(Raf)와 섬세한 수제 디저트 명소"}
    ],
    "상트페테르부르크": [
        {"name": "문학 카페 (Литературное кафе)", "category": "레스토랑", "lat": 59.9362, "lng": 30.3185, "desc": "푸시킨이 마지막 결투 전 들렀던 역사적인 러시아 정통 레스토랑"},
        {"name": "테레목 (Теремок 네프스키점)", "category": "레스토랑", "lat": 59.9345, "lng": 30.3342, "desc": "연어와 캐비어가 들어간 즉석 크레페(블리니)와 따뜻한 보르시 맛집"},
        {"name": "세베르 메트로폴 (Север-Метрополь)", "category": "카페", "lat": 59.9348, "lng": 30.3325, "desc": "1903년 문을 연 상트페테르부르크에서 가장 유서 깊은 고전 제과점"},
        {"name": "신치치 커피 (Bolshecoffee)", "category": "카페", "lat": 59.9548, "lng": 30.3142, "desc": "동굴 같은 아늑한 벽돌 인테리어에서 즐기는 고소한 로스터리 커피"}
    ],
    "도쿄": [
        {"name": "스시 다이와 (도요스 시장)", "category": "레스토랑", "lat": 35.6454, "lng": 139.7915, "desc": "수산시장 직송 제철 생선으로 쥐어주는 오마카세 스시 명가"},
        {"name": "이치란 라멘 (시부야점)", "category": "레스토랑", "lat": 35.6612, "lng": 139.7008, "desc": "개인 좌석에서 나만의 커스텀으로 즐기는 진한 돈코츠 라멘"},
        {"name": "푸글렌 도쿄 (Fuglen 아사쿠사)", "category": "카페", "lat": 35.7145, "lng": 139.7942, "desc": "노르웨이 오슬로 발상의 빈티지 북유럽 인테리어와 감성 커피"},
        {"name": "카페 드 랑브르 (긴자)", "category": "카페", "lat": 35.6698, "lng": 139.7625, "desc": "1948년부터 긴자를 지켜온 융드립 커피의 전설적인 노포 킷사텐"}
    ],
    "오사카": [
        {"name": "다루마 쿠시카츠 (도톤보리)", "category": "레스토랑", "lat": 34.6687, "lng": 135.5015, "desc": "바삭바삭 갓 튀겨낸 원조 꼬치튀김 전문점"},
        {"name": "미즈노 (Mizuno 오코노미야키)", "category": "레스토랑", "lat": 34.6682, "lng": 135.5028, "desc": "참마 100% 반죽의 부드러운 오사카 대표 오코노미야키"},
        {"name": "모토커피 (MOTO COFFEE)", "category": "카페", "lat": 34.6922, "lng": 135.5085, "desc": "나카노시마 강변 테라스에서 리버뷰와 함께 즐기는 푸딩과 라떼"}
    ],
    "파리": [
        {"name": "르 불롱제 (Le Bouillon Chartier)", "category": "레스토랑", "lat": 48.8718, "lng": 2.3432, "desc": "100년 역사의 벨 에포크 홀에서 맛보는 프랑스 전통 가정식"},
        {"name": "레 콕 (Les Cocottes 에펠탑)", "category": "레스토랑", "lat": 48.8578, "lng": 2.3025, "desc": "주물 냄비에 정성껏 졸여낸 비프 부르기뇽과 에스카르고 맛집"},
        {"name": "카페 드 플로르 (Café de Flore)", "category": "카페", "lat": 48.8542, "lng": 2.3325, "desc": "사르트르와 카뮈가 사랑했던 생제르맹 데프레의 문학 카페"},
        {"name": "레 되 마고 (Les Deux Magots)", "category": "카페", "lat": 48.8540, "lng": 2.3332, "desc": "진한 핫초콜릿과 크루아상을 즐기는 파리지앵 테라스"}
    ],
    "베이징": [
        {"name": "전취덕 (왕푸징 본점)", "category": "레스토랑", "lat": 39.9142, "lng": 116.4115, "desc": "150년 역사를 자랑하는 정통 베이징 카오야(북경오리) 전문점"},
        {"name": "동래순 (왕푸징 훠궈)", "category": "레스토랑", "lat": 39.9125, "lng": 116.4102, "desc": "구리 냄비에 숯불로 양고기를 데쳐 먹는 100년 전통의 훠궈 명가"},
        {"name": "메탈핸즈 (Metal Hands)", "category": "카페", "lat": 39.9385, "lng": 116.4124, "desc": "베이징 전통 골목(호퉁) 속 감각적인 스페셜티 에스프레소 바"}
    ],
    "뉴욕": [
        {"name": "피터 루거 스테이크 (Peter Luger)", "category": "레스토랑", "lat": 40.7098, "lng": -73.9625, "desc": "1887년 개업한 뉴욕 최고의 드라이에이징 포터하우스 스테이크 성지"},
        {"name": "조스 피자 (Joe's Pizza)", "category": "레스토랑", "lat": 40.7305, "lng": -74.0021, "desc": "바삭한 도우와 치즈가 일품인 정통 뉴욕식 조각 피자"},
        {"name": "에싸 베이글 (Ess-a-Bagel)", "category": "카페", "lat": 40.7565, "lng": -73.9712, "desc": "훈제 연어와 두툼한 크림치즈의 정통 뉴욕 베이글 카페"}
    ],
    "시드니": [
        {"name": "허리케인 그릴 (달링하버)", "category": "레스토랑", "lat": -33.8725, "lng": 151.1995, "desc": "바비큐 소스를 발라 숯불에 구운 두툼한 폭립 명가"},
        {"name": "더 그라운즈 오브 알렉산드리아", "category": "카페", "lat": -33.9108, "lng": 151.1942, "desc": "동화 속 비밀 화원처럼 꾸며진 정원형 브런치 & 스페셜티 카페"}
    ]
}

# -------------------------------------------------------------
# 3. 실시간 통합 도시 검색 (국내 카카오 로컬 / 해외 통합 지원)
# -------------------------------------------------------------
def search_smart_cities(query_text):
    q = query_text.strip()
    if not q:
        return []
    
    matches = []
    # 1. 내장 DB 우선 탐색
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

    # 2. 국내 도시 한글 검색 (카카오 로컬 API 활용)
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

    # 3. 해외 도시 검색 (OpenWeather Geocoding)
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={q}&limit=5&appid={OPENWEATHER_API_KEY}"
    try:
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            for item in res.json():
                ko_name = item.get("local_names", {}).get("ko")
                eng_name = item.get("name", "")
                country = item.get("country", "")
                curr_map = {"RU": "RUB", "JP": "JPY", "CN": "CNY", "US": "USD", "FR": "EUR", "GB": "GBP", "AU": "AUD"}
                curr = curr_map.get(country, "USD")
                label = f"✈️ {ko_name} ({eng_name}, {country})" if ko_name else f"✈️ {eng_name} ({country})"
                matches.append({
                    "label": label,
                    "city_query": eng_name,
                    "currency": "KRW" if country == "KR" else curr,
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
    help="국내 도시(서울, 부산, 수원, 시흥 등)와 전 세계 도시(모스크바, 도쿄, 파리 등)를 검색할 수 있습니다."
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
# 5. API 호출 함수들 (국내 카카오맵 랭킹 검색 포함)
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
    headers = {"User-Agent": "TravelDashboardApp/1.0 (travel_project)"}
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
def fetch_kakao_top_ranking_places(search_name, category_type="restaurant", size=4):
    """국내 모든 도시의 카카오맵 랭킹 상위 식당/카페 검색 (순수 한글 추출)"""
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
# 6. 지도 및 레스토랑/카페 렌더링 (국내/해외 완벽 분기)
# -------------------------------------------------------------
st.title(f"✈️ {selected_city_name} 여행 대시보드")

lat = city_info["lat"]
lng = city_info["lng"]

st.markdown("##### 📍 여행지 위치 & 🍽️ 맛집/카페 지도 탐색")

place_filter = st.radio(
    "지도에 표시할 장소 선택:",
    ["🏙️ 도시 중심만 보기", "🍽️ 레스토랑 보기", "☕ 카페 보기", "✨ 전체 모아보기"],
    horizontal=True
)

pure_city_key = re.sub(r'[^가-힣]', '', selected_city_name.split("(")[0]).strip()
selected_places = []

if place_filter != "🏙️ 도시 중심만 보기":
    if city_info.get("is_korea"):
        # 대한민국 도시: 카카오맵 실시간 랭킹 검색
        target_name = city_info.get("clean_ko", selected_city_name)
        if "레스토랑" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(target_name, "restaurant", size=3))
        if "카페" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(target_name, "cafe", size=3))
    else:
        # 해외 도시: OVERSEAS_PLACES_DB에서 정확한 위도/경도 매칭
        matched_overseas = None
        for k in OVERSEAS_PLACES_DB.keys():
            if k in pure_city_key or k in selected_city_name:
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

st.map(pd.DataFrame(map_rows), zoom=12)

# 장소 카드 출력
if selected_places:
    title_suffix = "카카오맵 실시간 랭킹" if city_info.get("is_korea") else "대표 추천"
    st.markdown(f"**🌟 {selected_city_name} {title_suffix} 장소 ({len(selected_places)}곳):**")
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
elif place_filter != "🏙️ 도시 중심만 보기":
    st.info("ℹ️ 해당 도시의 실시간 장소 목록을 불러오는 중이거나 등록된 매장이 없습니다.")

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
# 9. 도시별 심층 여행 가이드 데이터베이스 (모스크바 등 전 세계 완비)
# -------------------------------------------------------------
TRAVEL_GUIDE_DB = {
    "모스크바": {
        "spots": [
            {"name": "Saint Basil's Cathedral", "kr_name": "붉은 광장 & 성 바실리 대성당", "desc": "러시아의 심장이자 동화 같은 알록달록한 양파 돔 성당"},
            {"name": "Moscow Kremlin", "kr_name": "크렘린 궁전 & 무명용사의 묘", "desc": "황금빛 돔의 성당 군락과 영원의 불꽃이 타오르는 역사적 요새"},
            {"name": "GUM Department Store", "kr_name": "굼(GUM) 백화점 & 참새언덕", "desc": "유리 아케이드 건축미, 명물 아이스크림과 모스크바 전경을 내려다보는 전망대"}
        ],
        "stays": [
            {"area": "트베르스카야 대로", "type": "비즈니스 & 관광 중심", "desc": "붉은 광장까지 도보 이동 가능 및 대형 쇼핑가 인접"},
            {"area": "아르바트 거리", "type": "문화 예술 보행자 거리", "desc": "빅토르 최 추모벽, 기념품점, 카페가 밀집한 활기찬 거리"},
            {"area": "자모스크보레치예", "type": "조용하고 안전한 구역", "desc": "트레티야코프 미술관 근처의 고즈넉한 전통 주거지"}
        ],
        "foods": [
            {"name": "비프 스트로가노프", "desc": "부드러운 소고기를 볶아 사워크림 소스를 얹어 먹는 러시아 대표 고급 요리"},
            {"name": "펠메니 (러시아식 전통 만두)", "desc": "고기 소를 넣어 빚어 스메타나(사워크림)를 찍어 먹는 국민 음식"},
            {"name": "피로그 & 피로시키", "desc": "감자, 고기, 양배추 등을 채워 노릇노릇 구워낸 전통 빵"}
        ],
        "tips": [
            "모스크바 지하철역들은 '지하 궁전'처럼 대리석과 모자이크로 장식되어 있어 메트로 투어를 추천합니다.",
            "대중교통 이용 시 '트로이카(Troika)' 카드를 구매해 충전하면 매우 저렴합니다."
        ]
    },
    "상트페테르부르크": {
        "spots": [
            {"name": "Hermitage Museum", "kr_name": "에르미타주 미술관 (겨울궁전)", "desc": "세계 3대 박물관 중 하나이자 제정 러시아 궁전의 극치"},
            {"name": "Church of the Savior on Blood", "kr_name": "피의 구원 성당", "desc": "화려한 모자이크 벽화로 둘러싸인 정교한 성당"},
            {"name": "Nevsky Prospekt", "kr_name": "네프스키 대로 & 카잔 대성당", "desc": "로마 베드로 대성당을 본뜬 웅장한 콜로네이드 건축"}
        ],
        "stays": [
            {"area": "네프스키 대로 중심부", "type": "관광 최적", "desc": "겨울궁전 및 운하 유람선 선착장 도보 이동"},
            {"area": "폰탄카 운하 주변", "type": "클래식 감성 호텔", "desc": "운하 뷰가 아름다운 유럽풍 호텔 밀집"}
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
            {"name": "Shibuya Sky", "kr_name": "시부야 스카이 & 스크램블", "desc": "도쿄 타워와 후지산까지 보이는 360도 파노라마 루프탑"},
            {"name": "Shinjuku Gyoen", "kr_name": "신주쿠교엔", "desc": "도심 속 거대한 일본/영국/프랑스 정원"}
        ],
        "stays": [
            {"area": "신주쿠 / 시부야", "type": "교통 & 번화가 중심", "desc": "쇼핑, 맛집, 근교 이동 최적"},
            {"area": "긴자 / 도쿄역", "type": "쾌적한 럭셔리 & 비즈니스", "desc": "신칸센 탑승 편리 및 품격 있는 거리"}
        ],
        "foods": [
            {"name": "츠케멘 & 라멘", "desc": "진한 육수에 면을 찍어 먹는 츠케멘"},
            {"name": "에도마에 스시", "desc": "도요스 시장 직송 신선한 초밥"}
        ],
        "tips": [
            "도쿄 서브웨이 티켓으로 교통비를 대폭 절약할 수 있습니다."
        ]
    },
    "오사카": {
        "spots": [
            {"name": "Dotonbori", "kr_name": "도톤보리 & 글리코상", "desc": "화려한 네온사인과 거대한 입체 간판이 가득한 번화가"},
            {"name": "Osaka Castle", "kr_name": "오사카성 천수각", "desc": "웅장한 천수각과 성곽 해자 산책로"}
        ],
        "stays": [
            {"area": "난바 / 신사이바시", "type": "쇼핑 & 미식 중심", "desc": "라피트 직결 및 도톤보리 도보 이동"}
        ],
        "foods": [
            {"name": "타코야키 & 오코노미야키", "desc": "겉바속촉 문어 빵과 두툼한 철판 부침개"}
        ],
        "tips": [
            "교토 일정 시 한큐 패스를 미리 준비하세요."
        ]
    },
    "파리": {
        "spots": [
            {"name": "Eiffel Tower", "kr_name": "에펠탑 & 샹드마르스", "desc": "파리의 영원한 상징과 화이트 에펠 조명 쇼"},
            {"name": "Louvre Museum", "kr_name": "루브르 박물관", "desc": "모나리자를 비롯한 인류 예술의 보고"},
            {"name": "Sacré-Cœur", "kr_name": "몽마르트르 & 사크레쾨르", "desc": "예술가의 언덕과 파리 시내 파노라마"}
        ],
        "stays": [
            {"area": "1~8구 (중심가)", "type": "관광 최적", "desc": "도보 이동 편리 및 안전"}
        ],
        "foods": [
            {"name": "크루아상 & 바게트", "desc": "동네 불랑제리의 겉바속촉 빵"},
            {"name": "뵈프 부르기뇽", "desc": "와인에 졸인 프랑스식 소고기 찜"}
        ],
        "tips": [
            "박물관은 공식 웹사이트 사전 시간 예약이 필수입니다."
        ]
    },
    "베이징": {
        "spots": [
            {"name": "Forbidden City", "kr_name": "자금성 (고궁박물원)", "desc": "명·청 24대 황제가 거처한 세계 최대 목조 궁궐"},
            {"name": "Great Wall of China", "kr_name": "만리장성", "desc": "인류 최대의 건축물이자 유네스코 세계문화유산"}
        ],
        "stays": [
            {"area": "왕푸징 (Wangfujing)", "type": "쇼핑 & 명소 접근성", "desc": "자금성 도보 이동 가능"}
        ],
        "foods": [
            {"name": "베이징 카오야", "desc": "바삭한 껍질과 촉촉한 속살을 싸 먹는 오리 요리"}
        ],
        "tips": [
            "알리페이(Alipay)에 카드를 반드시 사전 등록하세요."
        ]
    },
    "상하이": {
        "spots": [
            {"name": "The Bund", "kr_name": "와이탄 & 동방명주", "desc": "유럽풍 건축물과 초현대식 마천루 야경"}
        ],
        "stays": [
            {"area": "인민광장 / 난징둥루", "type": "교통 및 쇼핑 중심", "desc": "와이탄 도보 가능"}
        ],
        "foods": [
            {"name": "샤오롱바오 (소롱포)", "desc": "진한 고기 육즙이 가득 찬 딤섬"}
        ],
        "tips": [
            "와이탄 건물 조명은 보통 밤 10시에 소등됩니다."
        ]
    },
    "청도": {
        "spots": [
            {"name": "Tsingtao Brewery", "kr_name": "칭다오 맥주박물관", "desc": "100년 역사의 칭다오 맥주 원액 시음"}
        ],
        "stays": [
            {"area": "5.4 광장", "type": "오션뷰 호텔", "desc": "쇼핑몰 및 해변 인접"}
        ],
        "foods": [
            {"name": "바지락 볶음 & 생맥주", "desc": "매콤한 바지락과 신선한 맥주 조합"}
        ],
        "tips": [
            "인천-청도는 비행기로 약 1시간 20분 거리입니다."
        ]
    },
    "뉴욕": {
        "spots": [
            {"name": "Times Square", "kr_name": "타임스퀘어 & 브로드웨이", "desc": "화려한 전광판과 브로드웨이 뮤지컬"},
            {"name": "Central Park", "kr_name": "센트럴 파크", "desc": "도심 속 거대한 숲과 호수"}
        ],
        "stays": [
            {"area": "미드타운 맨해튼", "type": "명소 도보권", "desc": "타임스퀘어 인접"}
        ],
        "foods": [
            {"name": "뉴욕 스트립 스테이크", "desc": "드라이에이징 포터하우스 스테이크"}
        ],
        "tips": [
            "지하철은 컨택트리스 카드로 바로 탈 수 있습니다."
        ]
    },
    "시드니": {
        "spots": [
            {"name": "Sydney Opera House", "kr_name": "오페라 하우스", "desc": "세계적인 랜드마크와 하버 페리 산책"}
        ],
        "stays": [
            {"area": "서큘러 키", "type": "하버 뷰", "desc": "오페라하우스 조망 호텔"}
        ],
        "foods": [
            {"name": "호주 청정우 스테이크", "desc": "육향 가득한 두툼한 스테이크"}
        ],
        "tips": [
            "한국과 계절이 정반대입니다."
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
            {"name": "부산 돼지국밥 & 밀면", "desc": "진한 사골 육수 국밥과 살얼음 동동 쫄깃한 밀면"}
        ],
        "tips": [
            "스카이캡슐은 주말 사전 예매가 필수입니다."
        ]
    },
    "수원": {
        "spots": [
            {"name": "Suwon Hwaseong Fortress", "kr_name": "수원 화성 & 방화수류정", "desc": "유네스코 세계문화유산이자 최고의 피크닉/야경 명소"},
            {"name": "Hwaseong Haenggung", "kr_name": "화성행궁 & 행리단길", "desc": "임시 궁궐과 감성 카페·편집숍 골목"}
        ],
        "stays": [
            {"area": "행궁동", "type": "감성 부티크", "desc": "성곽 산책과 카페 투어 최적"}
        ],
        "foods": [
            {"name": "수원 왕갈비 & 통닭거리", "desc": "숯불 왕갈비와 가마솥에서 튀겨낸 바삭한 통닭"}
        ],
        "tips": [
            "화성어차를 이용하면 성곽 명소를 편안하게 둘러볼 수 있습니다."
        ]
    }
}

# -------------------------------------------------------------
# 10. 화면 렌더링
# -------------------------------------------------------------
st.markdown("---")
st.subheader(f"🪻 {selected_city_name} 여행 핵심 가이드")

matched_guide_key = None
for key in TRAVEL_GUIDE_DB.keys():
    if key in selected_city_name or key in pure_city_key:
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
    st.info(f"선택하신 **{selected_city_name}**의 실시간 여행 정보를 아래 바로가기 버튼을 통해 확인해 보세요.")

st.markdown("##### 🔍 더 알아보기 (실시간 정보 바로가기)")
search_target = city_info.get("clean_ko", selected_city_name)
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.link_button("📍 구글 지도에서 명소/맛집 보기", f"https://www.google.com/maps/search/{search_target}+맛집")
with b_col2:
    st.link_button("🏨 아고다 숙소 최저가 검색", f"https://www.agoda.com/search?city={search_target}")
with b_col3:
    st.link_button("✈️ 트립어드바이저 여행 후기", f"https://www.tripadvisor.com/Search?q={search_target}")