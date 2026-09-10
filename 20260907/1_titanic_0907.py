"""
타이타닉 데이터셋 기초 탐색
pandas head/tail/shape/info/columns 를 사용해서 데이터셋의 기본 정보를 화면에 순서대로 보여주는 streamlit 앱이다.
실행방법: streamlit run 타이타닉_0907.py
"""

import pandas as pd     # 판다스는 엑셀을 위한 것이다..
import streamlit as st
import os
import io

# Titanic.csv 가져오기
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'common', 'Titanic.csv')
# CSV_PATH = "Titinic.csv"

st.title('🛳️ 타이타닉 데이터셋 기초 탐색')
st.caption('pandas의 head/tail/shape/info/columns 로 데이터셋 기본 정보를 확인합니다.')

uploaded_file = st.file_uploader('Titanic.csv 파일을 직접 업로드 할 수 있습니다.(선택사항)', type='csv')

if uploaded_file is not None:   # st.file_uploader로 파일을 직접 올릴 수 있다. 아무것도 올리지 않으면 아래의 기존 로직대로 
    df = pd.read_csv(uploaded_file)
else:
    try:
        df = pd.read_csv(CSV_PATH)      # 이 스크립트와 같은 폴더에 있는 타이타닉 파일을 읽어 온다.

    except FileNotFoundError:
        st.error('❌ 타이타닉 파일을 찾을 수가 없습니다.')
        st.info('같은 경로에 파일을 업로드 하거나 csv 파일을 폴더에 넣고 새로고침 하세요.')
        df = None


if df is not None:
    st.subheader('1) head(): 데이터의 앞부분 5개 행 미리보기')
    st.dataframe(df.head(), use_container_width=True)       # 앞부분 기본행 5개

    st.subheader('2) tail(): 데이터의 뒷부분 5개 행 미리보기')
    st.dataframe(df.tail(), use_container_width=True)       # 뒷부분 기본행 5개

    st.subheader('3) shape(): 행 개수, 열 개수')
    col1, col2 = st.columns(2)      # 컬럼 2개 만들고 각각 col1, col2라고 할 거야.
    with col1:
        st.metric('행 개수', f'{df.shape[0]}개')       # 행의 개수 가져와
    with col2:
        st.metric('열 개수', f'{df.shape[1]}개')       # 열의 개수 가져와

    st.subheader('4) columns: 전체 열(컬럼) 이름 목록 가져오기')
    # st.write(df.columns)
    st.write(list[str](df.columns))

    st.subheader('5) info(): 각 열의 자료형과 결측치(NaN) 여부 요약하기')
    # df.info 는 값을 리턴하지 않고, 화면에 집적적으로 출력만 해주는 함수라서,
    # os.StringIO() 라는 '메모리 위에 가짜 파일'에 결과를 받아낸 뒤 그 내용을 text 로 보여준다.
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

    # info_df = pd.DataFrame({
    #   '타입': df.dtypes,
    #   '결측치 아닌 개수': df.notna().sum(),
    #   '결측치 개수': df.isna().sum(),
    # })
    # st.dataframe(info_df, use_container_width=True)
    # 이런 식으로 사용할 수 있다. 

    st.success('기초 정보 확인이 끝났습니다. 다음 예제에서 전처리 필터링을 하겠습니다.')