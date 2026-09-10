import pandas as pd
import streamlit as st

CSV_PATH = '..\common\kpopidolsv3.csv'

st.header('🎤 K-pop 아이돌 데이터 필터링 & 결측치 정리')
st.caption('키·몸무게 조건으로 필터링해보고, 결측치를 제거해 새 csv로 저장합니다.')

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error('❌ 아이돌 파일을 찾을 수가 없습니다.')
else:
    st.metric('원본데이터 행 개수', f'{len(df)}행')
    st.markdown('---')

    st.subheader('1) 키 165 이상 아이돌')
    over_165 = df[df['Height'] >= 165]
    st.write(f'키 165 이상 아이돌 수: **{len(over_165)}명**')
    st.dataframe(over_165[['Korean Name','Group','Height']].head())


# 니아럼; ㅓㅣㄷ 호대ㅑ저럄널ㅇ