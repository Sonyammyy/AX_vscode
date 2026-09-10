"""
타이타닉 데이터 필터링, 결측지 정리
age(나이)가 35 이상인 승객 필터링
성별별로 필터링
titanic_cleaned.csv로 저장
실행방법: streamlit run titanic_filtering_0907.py
"""

import pandas as pd
import streamlit as st

CSV_PATH = '..\common\Titanic.csv'

st.header('🛳️ 타이타닉 데이터 필터링 & 결측치 정리')
st.caption('나이·성별 조건으로 필터링해보고, 결측치를 제거해 새 csv로 저장합니다.')

try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    st.error('❌ 타이타닉 파일을 찾을 수가 없습니다.')      # 에러 메시지
else:
    st.metric('원본 데이터 행 개수', f'{len(df)}행')
    st.markdown('---')

    # Age 35세 이상 필터링
    st.subheader('1) 나이 35세 이상 승객')
    over_35 = df[df['Age'] >= 35]       # 35세 이상인 아이를 걸러, True로 나오고 그걸 df 라는 자료에 다시 보낸다. 그 자료를 over_35라는 변수로 보내라.
    st.write(f'나이 35세 이상 승객 수: **{len(over_35)}명**')
    st.dataframe(over_35[['Name','Sex','Age']].head())

    st.markdown('---')

    # 성별 여자 남자 필터링 2컬럼 사용
    st.subheader('2) 성별 필터링 결과')
    female_df = df[df['Sex'] == 'female']
    male_df = df[df['Sex'] == 'male']

    col1, col2 = st.columns(2)
    with col1:
        st.metric('여성 승객 수', f'{len(female_df)}명')
    with col2:
        st.metric('남성 승객 수', f'{len(male_df)}명')

    st.markdown('---')

    # &(and), ||(or)
    female_over_35 = df[(df['Age'] >= 35) & (df['Sex'] == 'female')]
    st.subheader('3) 35세 이상 & 여성 승객')
    st.write(f'35세 이상 & 여성 승객 수: **{len(female_over_35)}명**')

    st.markdown('---')

    # 나이의 결측치(NaN) 확인 및 dropna 처리
    st.subheader('4) Age 결측치 처리')
    missing_age_count = df['Age'].isna().sum()      # isna() 로 결측치 하나씩 찾으면서 True로 반환하고, 이를 누적 카운트를 세는 거라 sum()을 써야 한다.
    st.write(f'Age 열의 결측치 개수: **{missing_age_count}개**')

    # Age 열이 결측치인 행만 골라서 제거한다.
    df_clean = df.dropna(subset=['Age'])        # subset = ['Age']: Age 열이 결측치인 행만 골라서 제거한다.
    col1, col2 = st.columns(2)
    with col1:
        st.metric('제거 전', f'{len(df)}행')
    with col2:
        st.metric('제거 후', f'{len(df_clean)}행')

    # 정리된 데이터를 csv 파일로 저장
    output_path = 'titanic_cleaned.csv'
    df_clean.to_csv(output_path, index=False)
    st.success('파일을 저장했습니다.')
    st.dataframe(df_clean.head(), use_container_width=True)
        