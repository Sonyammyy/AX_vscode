import os
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
# 0-1. 프리텐다드 레귤러 폰트 로드 & 아이콘 깨짐 방지 라벤더 CSS
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
# 2. 전 세계 도시 검색 데이터베이스 (한글/영문 매핑)
# -------------------------------------------------------------
GLOBAL_CITY_DB = [
    # 대한민국
    {"ko": "서울", "en": "Seoul", "country": "KR", "currency": "KRW", "lat": 37.5665, "lng": 126.9780, "is_korea": True, "kakao_keyword": "서울특별시청"},
    {"ko": "부산", "en": "Busan", "country": "KR", "currency": "KRW", "lat": 35.1796, "lng": 129.0756, "is_korea": True, "kakao_keyword": "부산광역시청"},
    {"ko": "제주", "en": "Jeju", "country": "KR", "currency": "KRW", "lat": 33.4996, "lng": 126.5312, "is_korea": True, "kakao_keyword": "제주시청"},
    {"ko": "인천", "en": "Incheon", "country": "KR", "currency": "KRW", "lat": 37.4563, "lng": 126.7052, "is_korea": True, "kakao_keyword": "인천광역시청"},
    {"ko": "대구", "en": "Daegu", "country": "KR", "currency": "KRW", "lat": 35.8714, "lng": 128.6014, "is_korea": True, "kakao_keyword": "대구광역시청"},
    {"ko": "강릉", "en": "Gangneung", "country": "KR", "currency": "KRW", "lat": 37.7519, "lng": 128.8761, "is_korea": True, "kakao_keyword": "강릉시청"},
    {"ko": "경주", "en": "Gyeongju", "country": "KR", "currency": "KRW", "lat": 35.8562, "lng": 129.2247, "is_korea": True, "kakao_keyword": "경주시청"},
    {"ko": "전주", "en": "Jeonju", "country": "KR", "currency": "KRW", "lat": 35.8242, "lng": 127.1480, "is_korea": True, "kakao_keyword": "전주시청"},

    # 중국
    {"ko": "베이징", "en": "Beijing", "country": "CN", "currency": "CNY", "lat": 39.9042, "lng": 116.4074},
    {"ko": "상하이", "en": "Shanghai", "country": "CN", "currency": "CNY", "lat": 31.2304, "lng": 121.4737},
    {"ko": "청도", "en": "Qingdao", "country": "CN", "currency": "CNY", "lat": 36.0671, "lng": 120.3826},

    # 일본
    {"ko": "도쿄", "en": "Tokyo", "country": "JP", "currency": "JPY", "lat": 35.6762, "lng": 139.6503},
    {"ko": "오사카", "en": "Osaka", "country": "JP", "currency": "JPY", "lat": 34.6937, "lng": 135.5023},
    {"ko": "후쿠오카", "en": "Fukuoka", "country": "JP", "currency": "JPY", "lat": 33.5904, "lng": 130.4017},
    {"ko": "삿포로", "en": "Sapporo", "country": "JP", "currency": "JPY", "lat": 43.0618, "lng": 141.3545},
    {"ko": "교토", "en": "Kyoto", "country": "JP", "currency": "JPY", "lat": 35.0116, "lng": 135.7681},

    # 러시아
    {"ko": "상트페테르부르크", "en": "Saint Petersburg", "country": "RU", "currency": "RUB", "lat": 59.9343, "lng": 30.3351},
    {"ko": "모스크바", "en": "Moscow", "country": "RU", "currency": "RUB", "lat": 55.7558, "lng": 37.6173},
    {"ko": "블라디보스토크", "en": "Vladivostok", "country": "RU", "currency": "RUB", "lat": 43.1155, "lng": 131.8855},

    # 프랑스 및 유럽
    {"ko": "파리", "en": "Paris", "country": "FR", "currency": "EUR", "lat": 48.8566, "lng": 2.3522},
    {"ko": "런던", "en": "London", "country": "GB", "currency": "GBP", "lat": 51.5074, "lng": -0.1278},
    {"ko": "로마", "en": "Rome", "country": "IT", "currency": "EUR", "lat": 41.9028, "lng": 12.4964},
    {"ko": "바르셀로나", "en": "Barcelona", "country": "ES", "currency": "EUR", "lat": 41.3879, "lng": 2.1699},
    {"ko": "취리히", "en": "Zurich", "country": "CH", "currency": "CHF", "lat": 47.3769, "lng": 8.5417},

    # 미국
    {"ko": "뉴욕", "en": "New York", "country": "US", "currency": "USD", "lat": 40.7128, "lng": -74.0060},
    {"ko": "로스앤젤레스", "en": "Los Angeles", "country": "US", "currency": "USD", "lat": 34.0522, "lng": -118.2437},
    {"ko": "샌프란시스코", "en": "San Francisco", "country": "US", "currency": "USD", "lat": 37.7749, "lng": -122.4194},
    {"ko": "라스베이거스", "en": "Las Vegas", "country": "US", "currency": "USD", "lat": 36.1699, "lng": -115.1398},
    {"ko": "하와이/호놀룰루", "en": "Honolulu", "country": "US", "currency": "USD", "lat": 21.3069, "lng": -157.8583},
    {"ko": "시애틀", "en": "Seattle", "country": "US", "currency": "USD", "lat": 47.6062, "lng": -122.3321},
    {"ko": "시카고", "en": "Chicago", "country": "US", "currency": "USD", "lat": 41.8781, "lng": -87.6298},

    # 호주
    {"ko": "시드니", "en": "Sydney", "country": "AU", "currency": "AUD", "lat": -33.8688, "lng": 151.2093},
    {"ko": "멜버른", "en": "Melbourne", "country": "AU", "currency": "AUD", "lat": -37.8136, "lng": 144.9631},

    # 동남아시아
    {"ko": "하노이", "en": "Hanoi", "country": "VN", "currency": "VND", "lat": 21.0285, "lng": 105.8542},
    {"ko": "다낭", "en": "Da Nang", "country": "VN", "currency": "VND", "lat": 16.0544, "lng": 108.2022},
    {"ko": "방콕", "en": "Bangkok", "country": "TH", "currency": "THB", "lat": 13.7563, "lng": 100.5018},
    {"ko": "타이베이", "en": "Taipei", "country": "TW", "currency": "TWD", "lat": 25.0330, "lng": 121.5654},
    {"ko": "싱가포르", "en": "Singapore", "country": "SG", "currency": "SGD", "lat": 1.3521, "lng": 103.8198},
]

# 해외 도시용 큐레이션 매핑
OVERSEAS_PLACES_DB = {
    "베이징": [
        {"name": "전취덕 (왕푸징 본점)", "category": "레스토랑", "lat": 39.9142, "lng": 116.4115, "desc": "150년 역사를 자랑하는 정통 베이징 카오야(북경오리) 전문점"},
        {"name": "동래순 (왕푸징 훠궈)", "category": "레스토랑", "lat": 39.9125, "lng": 116.4102, "desc": "구리 냄비에 숯불로 양고기를 데쳐 먹는 100년 전통의 훠궈 명가"},
        {"name": "메탈핸즈 (Metal Hands 호퉁)", "category": "카페", "lat": 39.9385, "lng": 116.4124, "desc": "베이징 전통 골목(호퉁) 속 감각적인 스페셜티 에스프레소 바"},
        {"name": "보이저 커피 (Voyage Coffee)", "category": "카페", "lat": 39.9324, "lng": 116.3982, "desc": "사합원 고택을 개조한 세련된 핸드드립 전문 카페"}
    ],
    "도쿄": [
        {"name": "스시 다이와 (도요스)", "category": "레스토랑", "lat": 35.6454, "lng": 139.7915, "desc": "신선한 수산시장 직송 제철 생선으로 쥐어주는 오마카세 스시"},
        {"name": "이치란 라멘 (시부야점)", "category": "레스토랑", "lat": 35.6612, "lng": 139.7008, "desc": "개인 독서실 좌석에서 즐기는 진한 돈코츠 라멘"},
        {"name": "푸글렌 도쿄 (Fuglen 아사쿠사)", "category": "카페", "lat": 35.7145, "lng": 139.7942, "desc": "노르웨이 오슬로 발상의 빈티지 북유럽 인테리어와 커피"},
        {"name": "카페 드 랑브르 (Cafe de L'Ambre)", "category": "카페", "lat": 35.6698, "lng": 139.7625, "desc": "1948년부터 긴자를 지켜온 융드립 커피의 전설적인 킷사텐"}
    ],
    "파리": [
        {"name": "르 불롱제 (Le Bouillon Chartier)", "category": "레스토랑", "lat": 48.8718, "lng": 2.3432, "desc": "100년 넘는 역사의 벨 에포크 양식 홀에서 맛보는 프랑스 전통 가정식"},
        {"name": "레 콕 (Les Cocottes 에펠탑)", "category": "레스토랑", "lat": 48.8578, "lng": 2.3025, "desc": "주물 냄비에 정성껏 졸여낸 비프 부르기뇽과 에스카르고 맛집"},
        {"name": "카페 드 플로르 (Café de Flore)", "category": "카페", "lat": 48.8542, "lng": 2.3325, "desc": "사르트르와 카뮈가 사랑했던 생제르맹 데프레의 문학 카페"},
        {"name": "레 되 마고 (Les Deux Magots)", "category": "카페", "lat": 48.8540, "lng": 2.3332, "desc": "진한 핫초콜릿과 크루아상을 즐기며 파리지앵 테라스를 만끽하는 명소"}
    ],
    "상트페테르부르크": [
        {"name": "문학 카페 (Литературное кафе)", "category": "레스토랑", "lat": 59.9362, "lng": 30.3185, "desc": "푸시킨이 마지막 결투 전 들렀던 역사적인 장소이자 러시아 정통 요리"},
        {"name": "테레목 (Теремок 네프스키점)", "category": "레스토랑", "lat": 59.9345, "lng": 30.3342, "desc": "연어, 치즈, 캐비어가 들어간 즉석 팬케이크(블리니)와 보르시"},
        {"name": "세베르 메트로폴 (Север-Метрополь)", "category": "카페", "lat": 59.9348, "lng": 30.3325, "desc": "1903년 문을 연 상트페테르부르크에서 가장 사랑받는 고전 제과점"},
        {"name": "신치치 커피 (Bolshecoffee)", "category": "카페", "lat": 59.9548, "lng": 30.3142, "desc": "동굴 같은 아늑한 벽돌 인테리어에서 직접 볶은 원두로 내리는 로스터리"}
    ]
}

# -------------------------------------------------------------
# 3. 실시간 추천 검색 함수
# -------------------------------------------------------------
def search_smart_cities(query_text):
    q = query_text.strip().lower()
    if not q:
        return []
    matches = []
    for item in GLOBAL_CITY_DB:
        if q in item["ko"].lower() or q in item["en"].lower():
            label = f"✈️ {item['ko']} ({item['en']}, {item['country']})"
            matches.append({
                "label": label,
                "city_query": item["en"],
                "currency": item["currency"],
                "lat": item["lat"],
                "lng": item["lng"],
                "is_korea": item.get("is_korea", False),
                "kakao_keyword": item.get("kakao_keyword", item["ko"])
            })
            if len(matches) >= 6:
                return matches

    if not matches:
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
                        "currency": "USD",
                        "lat": float(item["lat"]),
                        "lng": float(item["lon"]),
                        "is_korea": (country == "KR"),
                        "kakao_keyword": eng_name if country == "KR" else None
                    })
        except Exception:
            pass
    return matches

# -------------------------------------------------------------
# 4. 사이드바 구성
# -------------------------------------------------------------
st.sidebar.markdown("## 🔍 여행지 검색")

user_input = st.sidebar.text_input(
    "떠나고 싶은 도시를 입력하세요:",
    value="부산",
    help="두 글자만 입력해도 실시간 추천됩니다. (예: 부산, 서울, 제주, 강릉, 도쿄, 파리 등)"
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
    city_info = GLOBAL_CITY_DB[1]  # 부산
    selected_city_name = "부산 (Busan, KR)"

# -------------------------------------------------------------
# 5. API 호출 함수들 (카카오맵 랭킹 맛집/카페 실시간 검색 포함)
# -------------------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_wiki_image(query_name):
    """위키미디어 REST API: 키 없이 명소 대표 고화질 이미지 URL 자동 추출"""
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

def fetch_kakao_place(keyword):
    """카카오 로컬 REST API: 중심 좌표 검색"""
    if not KAKAO_MAP_API_KEY:
        return {"success": False, "msg": "KAKAO_MAP_API_KEY가 비어 있습니다."}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_MAP_API_KEY}"}
    params = {"query": keyword, "size": 1}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            if docs:
                return {
                    "success": True,
                    "lat": float(docs[0]["y"]),
                    "lng": float(docs[0]["x"]),
                    "place_name": docs[0].get("place_name", ""),
                    "address": docs[0].get("address_name", ""),
                    "place_url": docs[0].get("place_url", ""),
                }
            return {"success": False, "msg": f"'{keyword}' 검색 결과가 없습니다."}
        return {"success": False, "status_code": res.status_code, "msg": res.text}
    except Exception as e:
        return {"success": False, "msg": f"네트워크 오류: {str(e)}"}

@st.cache_data(ttl=1800)
def fetch_kakao_top_ranking_places(city_name, category_type="restaurant", size=4):
    """
    [핵심 개선] 카카오맵 랭킹 상위 맛집/카페 실시간 검색 (한국 내 모든 도시 지원)
    - query: '{도시명} 맛집' 또는 '{도시명} 카페'
    - category_group_code: 'FD6'(음식점) / 'CE7'(카페)
    - sort: 'accuracy'(카카오맵 랭킹/정확도 순)
    """
    if not KAKAO_MAP_API_KEY:
        return []
    
    # 순수 한글 도시명 추출 (예: '부산 (Busan, KR)' -> '부산')
    clean_city = city_name.split("(")[0].strip()
    
    if category_type == "restaurant":
        query = f"{clean_city} 맛집"
        category_code = "FD6"
        label_text = "레스토랑"
    else:
        query = f"{clean_city} 카페"
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
                    "desc": f"📍 {d.get('road_address_name', d.get('address_name'))} | 📞 {d.get('phone') if d.get('phone') else '전화번호 정보 없음'}",
                    "url": d.get("place_url")
                })
            return places
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_weather(city_query):
    """OpenWeather API"""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_query}&appid={OPENWEATHER_API_KEY}&units=metric&lang=kr"
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
    """ExchangeRate-API"""
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
    fallback = {
        "USD": 1335.0, "EUR": 1450.0, "JPY": 9.12, "GBP": 1715.0,
        "CNY": 185.0, "RUB": 14.8, "AUD": 880.0, "VND": 0.054
    }
    return fallback.get(target_currency, 1300.0)

# -------------------------------------------------------------
# 6. 대시보드 상단 (지도 및 카카오맵 랭킹 맛집/카페 렌더링)
# -------------------------------------------------------------
st.title(f"✈️ {selected_city_name} 여행 대시보드")

lat = city_info["lat"]
lng = city_info["lng"]

if city_info.get("is_korea"):
    kakao_result = fetch_kakao_place(city_info.get("kakao_keyword", "부산광역시청"))
    if kakao_result.get("success"):
        lat = kakao_result["lat"]
        lng = kakao_result["lng"]

# --- 레스토랑 & 카페 실시간 탐색 필터 ---
st.markdown("##### 📍 여행지 위치 & 🍽️ 카카오맵 랭킹 맛집/카페 지도 탐색")

place_filter = st.radio(
    "지도에 표시할 장소 선택:",
    ["🏙️ 도시 중심만 보기", "🍽️ 레스토랑 랭킹 보기", "☕ 인기 카페 랭킹 보기", "✨ 전체 모아보기"],
    horizontal=True
)

selected_places = []

if place_filter != "🏙️ 도시 중심만 보기":
    if city_info.get("is_korea"):
        # 대한민국 도시: 카카오맵 랭킹 상위 식당/카페 실시간 조회
        if "레스토랑" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(selected_city_name, "restaurant", size=3))
        if "카페" in place_filter or "전체" in place_filter:
            selected_places.extend(fetch_kakao_top_ranking_places(selected_city_name, "cafe", size=3))
    else:
        # 해외 도시: 해외 큐레이션 DB 연동
        matched_k = None
        for k in OVERSEAS_PLACES_DB.keys():
            if k in selected_city_name:
                matched_k = k
                break
        if matched_k:
            items = OVERSEAS_PLACES_DB[matched_k]
            if "레스토랑" in place_filter:
                selected_places = [p for p in items if p["category"] == "레스토랑"]
            elif "카페" in place_filter:
                selected_places = [p for p in items if p["category"] == "카페"]
            elif "전체" in place_filter:
                selected_places = items

# 지도 데이터프레임 구성 (도시 중심점 + 카카오맵 랭킹 맛집/카페 다중 핀)
map_rows = [{"lat": lat, "lon": lng}]
for p in selected_places:
    map_rows.append({"lat": p["lat"], "lon": p["lng"]})

map_df = pd.DataFrame(map_rows)
st.map(map_df, zoom=12)

# 화면에 랭킹 장소 카드 출력
if selected_places:
    st.markdown(f"**🌟 카카오맵 랭킹 추천 장소 ({selected_city_name} 기준 {len(selected_places)}곳):**")
    p_cols = st.columns(min(len(selected_places), 3))
    for idx, pl in enumerate(selected_places):
        with p_cols[idx % 3]:
            icon = "🍽️" if pl["category"] == "레스토랑" else "☕"
            st.markdown(f"**{icon} {pl['name']}**")
            st.caption(f"분류: {pl['category']}")
            st.write(pl.get("desc", ""))
            if pl.get("url"):
                st.markdown(f"[🔗 카카오맵에서 리뷰 및 길찾기]({pl['url']})")
            else:
                st.markdown(f"[🔗 구글 지도에서 길찾기](https://www.google.com/maps/search/{pl['name']})")
elif place_filter != "🏙️ 도시 중심만 보기":
    st.info("ℹ️ 해당 도시의 실시간 장소 목록을 탐색 중이거나 등록된 랭킹 데이터가 없습니다.")

st.markdown("---")

# -------------------------------------------------------------
# 7. 날씨 및 환율 정보
# -------------------------------------------------------------
col_weather, col_rate = st.columns([1, 1])

with col_weather:
    st.subheader("🌤️ 현지 날씨")
    weather_data = fetch_weather(city_info["city_query"])
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
# 8. 접이식 환율 계산기 및 슬라이더 (Expander)
# -------------------------------------------------------------
with st.expander(f"환율 계산기 & 은행 우대율 설정 ({target_curr})", expanded=True):
    st.markdown("##### ⚙️ 환율 상세 옵션")
    s_col1, s_col2 = st.columns(2)
    with s_col1:
        new_spread = st.slider(
            "스프레드율 (%)", min_value=0.5, max_value=4.0, 
            value=float(st.session_state["spread_rate"]), step=0.05, key="slider_spread"
        )
        st.session_state["spread_rate"] = new_spread
    with s_col2:
        new_discount = st.slider(
            "은행 우대율 (%)", min_value=0, max_value=100, 
            value=int(st.session_state["discount_rate"]), step=5, key="slider_discount"
        )
        st.session_state["discount_rate"] = new_discount

    if target_curr != "KRW":
        basic_spread = base_rate * (st.session_state["spread_rate"] / 100.0)
        actual_spread_amount = basic_spread * (1.0 - (st.session_state["discount_rate"] / 100.0))
        cash_buy = base_rate + actual_spread_amount
        cash_sell = base_rate - actual_spread_amount

    st.markdown("---")
    st.markdown("##### 💵 금액 환전 계산")

    calc_direction = st.radio(
        "환전 방식 선택:",
        [
            f"원화(KRW) ➡️ 현지 통화({target_curr}) [사실 때 환율 적용]",
            f"현지 통화({target_curr}) ➡️ 원화(KRW) [파실 때 환율 적용]",
        ],
    )

    is_krw_to_foreign = "원화(KRW) ➡️" in calc_direction
    amount_input = st.number_input(
        "환전할 금액 입력:",
        min_value=0.0,
        value=100000.0 if is_krw_to_foreign else 100.0,
        step=10.0,
    )

    fmt = "{:,.4f}원" if base_rate < 1.0 else "{:,.2f}원"
    if is_krw_to_foreign:
        converted_result = float(amount_input / cash_buy) if cash_buy > 0 else 0.0
        st.success(
            f"💜 **{amount_input:,.0f} KRW** ➡️ **{converted_result:,.2f} {target_curr}** "
            f"(적용 환율: 1 {target_curr} = {fmt.format(cash_buy)})"
        )
    else:
        converted_result = float(amount_input * cash_sell)
        st.success(
            f"💜 **{amount_input:,.2f} {target_curr}** ➡️ **{converted_result:,.0f} KRW** "
            f"(적용 환율: 1 {target_curr} = {fmt.format(cash_sell)})"
        )

# -------------------------------------------------------------
# 9. 도시별 심층 여행 가이드 (서울/부산 등)
# -------------------------------------------------------------
TRAVEL_GUIDE_DB = {
    "부산": {
        "spots": [
            {"name": "Haeundae Beach", "kr_name": "해운대 해수욕장 & 블루라인파크", "desc": "대한민국 대표 해변이자 해변 열차와 스카이캡슐을 즐길 수 있는 오션뷰 핫플레이스"},
            {"name": "Gamcheon Culture Village", "kr_name": "감천문화마을", "desc": "알록달록한 계단식 주택과 어린왕자 포토존이 있는 한국의 산토리니"},
            {"name": "Gwangalli Beach", "kr_name": "광안리 해수욕장 & 광안대교", "desc": "화려한 광안대교 야경과 감성 오션뷰 카페, 드론 라이트 쇼 명소"}
        ],
        "stays": [
            {"area": "해운대", "type": "오션뷰 럭셔리 호텔", "desc": "해수욕장 도보 이동, 고급 호텔 및 편의시설 밀집"},
            {"area": "광안리", "type": "감성 숙소 & 에어비앤비", "desc": "객실 창문 가득 광안대교 오션뷰가 펼쳐지는 힐링 구역"},
            {"area": "서면 / 남포동", "type": "교통 요충지 & 쇼핑 중심", "desc": "KTX 부산역 접근성 및 자갈치시장, 깡통야시장 도보 관광"}
        ],
        "foods": [
            {"name": "부산 돼지국밥", "desc": "진하고 뽀얀 사골 육수에 부추와 새우젓을 넣어 든든하게 먹는 부산 소울푸드"},
            {"name": "밀면 (물밀면 & 비빔밀면)", "desc": "살얼음 동동 띄운 한방 육수에 쫄깃한 면발을 호로록 즐기는 별미"},
            {"name": "부산 어묵 & 씨앗호떡", "desc": "생선살이 듬뿍 들어간 쫄깃한 물떡/어묵과 견과류 가득한 바삭한 호떡"}
        ],
        "tips": [
            "블루라인파크 스카이캡슐은 주말 방문 시 매진이 빠르므로 일주일 전 사전 예매가 필수입니다.",
            "광안리 드론쇼는 매주 토요일 저녁 2회 진행되므로 시간을 미리 확인하세요."
        ]
    },
    "서울": {
        "spots": [
            {"name": "Gyeongbokgung", "kr_name": "경복궁 & 북촌한옥마을", "desc": "조선의 정궁이자 웅장한 근정전, 고즈넉한 전통 한옥 골목과 삼청동 카페 거리"},
            {"name": "N Seoul Tower", "kr_name": "N서울타워 (남산타워)", "desc": "남산 정상에서 서울 360도 파노라마 야경과 사랑의 자물쇠를 만날 수 있는 랜드마크"},
            {"name": "Dongdaemun Design Plaza", "kr_name": "동대문디자인플라자 (DDP)", "desc": "자하 하디드가 설계한 미래지향적 비정형 건축물과 감성 야경"}
        ],
        "stays": [
            {"area": "명동 / 을지로", "type": "쇼핑 & 환승 요충지", "desc": "지하철 2·3·4호선 접근성 최상"},
            {"area": "홍대 / 연남동", "type": "젊음과 버스킹", "desc": "공항철도 직결, 트렌디 부티크"},
            {"area": "강남 / 삼성동", "type": "프리미엄 럭셔리", "desc": "코엑스 몰 및 쾌적한 호캉스 인프라"}
        ],
        "foods": [
            {"name": "K-바비큐 (숙성 삼겹살 & 한우)", "desc": "숯불 불판에 구워 쌈장, 된장찌개와 즐기는 대표 외식"},
            {"name": "광장시장 빈대떡 & 육회", "desc": "두툼한 녹두빈대떡과 신선한 마약김밥, 참기름 육회"},
            {"name": "한강 치맥 (치킨 + 맥주)", "desc": "한강공원 잔디밭에서 즐기는 배달 치킨과 즉석 라면"}
        ],
        "tips": [
            "한복 착용 시 4대 궁궐과 종묘에 무료로 입장할 수 있습니다.",
            "기후동행카드 관광객 단기권을 이용하면 지하철과 시내버스를 무제한으로 이용 가능합니다."
        ]
    }
}

# -------------------------------------------------------------
# 10. 화면 렌더링 (4개 탭 큐레이션 및 무료 고화질 이미지 연동)
# -------------------------------------------------------------
st.markdown("---")
st.subheader(f"🪻 {selected_city_name} 여행 핵심 가이드")

matched_guide_key = None
for key in TRAVEL_GUIDE_DB.keys():
    if key in selected_city_name:
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
search_query = city_info['city_query']
b_col1, b_col2, b_col3 = st.columns(3)
with b_col1:
    st.link_button("📍 구글 지도에서 명소/맛집 보기", f"https://www.google.com/maps/search/{search_query}+attractions")
with b_col2:
    st.link_button("🏨 아고다 숙소 최저가 검색", f"https://www.agoda.com/search?city={search_query}")
with b_col3:
    st.link_button("✈️ 트립어드바이저 여행 후기", f"https://www.tripadvisor.com/Search?q={search_query}")