import pandas as pd
import streamlit as st
import io


st.title('🎤 K-pop 아이돌 데이터셋 기초 탐색')
st.caption('pandas의 head/tail/shape/info/columns 로 데이터셋 기본 정보를 확인합니다.')

uploaded_file = st.file_uploader('kpopidolsc3.csv 파일을 업로드 하세요.', type='csv')

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    st.error('❌ 아이돌 파일을 찾을 수 없습니다.')
    st.info('csv 파일을 폴더에 넣고 새로고침 하세요.')
    df = None

if df is not None:
    st.subheader('1) head(): 데이터의 앞부분 5개 행 미리보기')
    st.dataframe(df.head(), use_container_width=True)

    st.subheader('2) tail(): 데이터의 뒷부분 5개 행 미리보기')
    st.dataframe(df.tail(), use_container_width=True)

    st.subheader('3) shape(): 행 개수, 열 개수')
    col1, col2 = st.columns(2)
    with col1:
        st.metric('행 개수', f'{df.shape[0]}개')
    with col2:
        st.metric('열 개수', f'{df.shape[1]}개')

    st.subheader('4) columns(): 전체 열(컬럼) 이름 목록 가져오기')
    st.write(list(df.columns))

    st.subheader('5) info(): 각 열의 자료형과 결측지(NaN) 여부 요약하기')
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())
    st.write('결측치 개수')
    st.write(df.isna().sum())
    
    st.success('기초 정보 확인이 끝났습니다. 다음 예제에서 전처리 필터링을 하겠습니다.')