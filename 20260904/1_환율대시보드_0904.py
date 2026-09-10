import streamlit as st
import pandas as pd
import os



CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'common', 'raw_trade_data.csv')
# CSV_PATH = os.path.join(os.path.dirname(__file__), 'raw_trade_data.csv')  ->  내가 있는 이 경로에서 파일을 불러와라.
# 파일을 불러온 거지 판다스가 읽을 수 있는 파일이 아니므로 후에 pd.read_csv()가 필요하다.

# 환율샘플 데이터
# 딕셔너리로 표 만들기
exchange_data = {
    '통화' : ['USD', 'EUR', 'JPY(100엔)', 'CNY'],
    '환율' : [1390.5, 1503.2, 930.8, 191.3],
    '전일 대비' : [+5.2, -3.1, +1.0, -0.4],
}

df_exchange = pd.DataFrame(exchange_data)


st.title('💱 오늘의 환율 대시보드')
st.caption('아래 데이터는 실제 환율이 아닌 실습용 샘플 데이터입니다.')


st.subheader('1) 환율 표 보기')
st.write('▶ st.dataframe (상호작용 가능한 표)')
st.dataframe(df_exchange, use_container_width=True)


st.write('▶ st.table (정적인 표)')
st.table(df_exchange)


st.markdown('---')


st.subheader('2) 주요 환율 카드 (st.metric)')
# st.metric(라벨, 현재값, 증감값)
col1, col2, col3 = st.columns(3)    # 컬럼 3개 만들고 각각을 col1, col2, col3이라 할 거야.
with col1 :
    st.metric(label='USD/KRW', value='1,390.0', delta='+5.2')
with col2 :
    st.metric(label='EUR/KRW', value='1,503.2', delta='-3.1')
with col3 :
    st.metric(label='JPY(100엔)/KRW', value='930.8', delta='+1.0')


st.markdown('---')


df_trade_raw = pd.read_csv(CSV_PATH, encoding='utf-8')

st.subheader('3) 보너스: 무역 원본 데이터 미리보기')
st.write('공용 데이터 파일 raw_trade_data.csv를 읽어온 상위 5행이다.')
st.dataframe(df_trade_raw.head())