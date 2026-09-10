import streamlit as st
import pandas as pd
import os

# 페이지 설정
st.set_page_config(page_title="무역 데이터 분석", layout="wide")

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 스크립트 위치를 기준으로 절대 경로 구성
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, '..', 'common', 'raw_trade_data.csv')
    return pd.read_csv(file_path)

st.title("📊 무역 데이터 분석 대시보드")

# 데이터 불러오기
df = load_data()
# 조건 필터링
# HS 코드 85로 시작하고, 국가명이 미국/베트남이며, 수출입구분이 Export(수출)인 데이터
cond_hs = df['hs_code'].astype(str).str.startswith('85')
cond_country = df['국가명'].isin(['미국', '베트남'])
cond_type = df['수출입구분'].str.lower() == 'export'

filtered_df = df[cond_hs & cond_country & cond_type]

if not filtered_df.empty:
    # 수출금액 기준 상위 10건 내역
    top_10 = filtered_df.sort_values(by='수출금액', ascending=False).head(10)
    
    # 3개 컬럼 메트릭 구성
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="조건 부합 건수", value=f"{len(filtered_df):,} 건")
    with col2:
        top_10_sum = top_10['수출금액'].sum()
        st.metric(label="상위 10건 총 수출액", value=f"${top_10_sum:,}")
    with col3:
        max_export = filtered_df['수출금액'].max()
        st.metric(label="최고 수출액", value=f"${max_export:,}")
        
    # 데이터프레임 출력
    st.subheader("📌 수출금액 상위 10건 상세 내역")
    st.dataframe(top_10)
else:
    st.info("조건에 부합하는 데이터가 존재하지 않습니다.")

# 간단한 분석 예시: 수출입구분별 수출금액 총합
st.subheader("수출입 구분별 수출금액 분석")
if '수출금액' in df.columns:
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    
    summary = df.groupby('수출입구분')['수출금액'].sum()
    
    # 한글 폰트 설정 (20260907 폴더의 Pretendard-Regular.otf 사용)
    base_path = os.path.dirname(os.path.abspath(__file__))
    FONT_PATH = os.path.join(base_path, '..', '20260907', 'Pretendard-Regular.otf')
    if os.path.exists(FONT_PATH):
        font_manager.fontManager.addfont(FONT_PATH)
        font_prop = font_manager.FontProperties(fname=FONT_PATH)
        plt.rc('font', family=font_prop.get_name())
        plt.rcParams['axes.unicode_minus'] = False
        
    fig, ax = plt.subplots(figsize=(8, 5))
    summary.plot(kind='bar', ax=ax, color=['#4F46E5', '#10B981'])
    
    # x축 레이블(Export, Import)을 똑바로(0도 회전) 표시하도록 설정
    ax.tick_params(axis='x', rotation=0)
    
    ax.set_title("수출입 구분별 수출금액 분석")
    ax.set_xlabel("수출입구분")
    ax.set_ylabel("수출금액")
    
    st.pyplot(fig)
else:
    st.write("분석할 '수출금액' 컬럼을 찾을 수 없습니다.")

