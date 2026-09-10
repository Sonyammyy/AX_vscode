# 인코딩 자동 감지 + 한글 폰트 막대그래프
# 여러 인코딩('utf-8-sig','cp949','euc-kr') 순서대로 시도
# 내가 쓸 폰트 같은 경로에 있어야 함
# 객실등급별 생존율 막대그래프 생성 후 그림으로 저장 chart.png(확장자)
# 실행방법: streamlit run 5_인코딩_0907.py


import os
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib import font_manager

CSV_PATH = os.path.join(os.path.dirname(__file__), 'titanic_cleaned.csv')       # 같은 폴더에 있으므로 바로 파일명
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Pretendard-Regular.otf')


st.title('📊 인코딩 자동 감지 + 한글 폰트 막대그래프 (Titanic 연습)')
st.caption('여러 인코딩을 순서대로 시도해서 파일을 읽고, 객실등급별 생존율을 그래프로 그립니다.')


def read_csv_with_auto_encoding(file_path):
    """'utf-8-sig', 'cp949', 'euc-kr' 인코딩을 차례로 시도하여 CSV 파일을 읽어오는 함수"""
    encodings = ['utf-8-sig', 'cp949', 'euc-kr']

    for enc in encodings:
        try:
            # Streamlit UploadedFile 객체 지원 (포인터 되감기)
            if hasattr(file_path, 'seek'):
                file_path.seek(0)
            df = pd.read_csv(file_path, encoding=enc)
            st.write(f'{enc}으로 읽었습니다.')
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f'지원하는 인코딩({encodings})으로 파일을 읽을 수 없습니다.')

# 인코딩 자동 감지로 csv 읽기
st.subheader('1) 인코딩 자동 감지')
df = read_csv_with_auto_encoding(CSV_PATH)      # 이 파일을 넣어서 보내면 무슨 인코딩으로 읽었는지 독해해줘.

st.markdown('---')

# 객실등급(Pclass)별 생존율 집계
# 사망 0 / 생존 1 로 표시하는 등급별 평균을 내면 그대로가 등급의 생존 비율이 된다.
# 1000 생존 300  300/1000 == 30%

pclass_survival_rate = df.groupby('Pclass')['Survived'].mean().sort_index()     # 1은 1끼리, 2는 2끼리 정리한 다음 그룹핑할게.
st.dataframe(  (pclass_survival_rate * 100).round(1).rename('생존율(%)'))

# 차트 그리기

st.markdown('---')
st.subheader('3) 객실 등급별 생존율 막대그래프')

# try:
#     # 조건이 온전히 맞을 때
#     # 폰트 파일이 없으면 FileNotFoundError가 발생한다.
#     font_prop = font_manager.FontProperties(fname=FONT_PATH)
#     # matplotlib 에서 font_manafer의 역할은 여기에 폰트를 등록하고, 전역 폰트로 설정한다. 차트 그리는 모든 글꼴로 설정한다.
#     font_manager.fontManager.addfont(FONT_PATH)
#     plt.rcParams['font.familly']
#     st.write('Pretendard-Regular 폰트를 적용했습니다.')
# except FileNotFoundError:
#     st.warning('Pretendard-Regular 폰트파일을 찾을 수가 없습니다.')

try:
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError

    # 1. 폰트 매니저에 파일 등록
    font_manager.fontManager.addfont(FONT_PATH)
    # 2. 폰트 파일의 실제 폰트 이름 추출
    font_prop = font_manager.FontProperties(fname=FONT_PATH)
    # 3. Matplotlib 전역 글꼴로 설정 (이 부분이 빠져서 깨졌던 것!)
    plt.rc('font', family=font_prop.get_name())
    # 4. 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False

    st.write('Pretendard-Regular 폰트를 적용했습니다.')
except FileNotFoundError:
    st.warning('Pretendard-Regular 폰트파일을 찾을 수가 없습니다.')

fig, ax = plt.subplots(figsize=(8, 5))
(pclass_survival_rate * 100).plot(kind='bar', color='#C8C5EB', ax=ax)

ax.set_title('객실 등급별 생존율')
ax.set_xlabel('객실등급(Pclass)')

# 1. 글자 사이에 줄바꿈(\n)을 넣고 회전을 0도로 고정
ax.set_ylabel('생\n존\n율\n(%)', rotation=0, labelpad=20, va='center')

# 2. x축의 1, 2, 3도 똑바로 세우기
ax.tick_params(axis='x', rotation=0)

st.pyplot(fig)      # streamlit으로 matplotlib 차트 띄울 땐 무조건 사용해야 한다.
# fig가 바깥쪽 차트 영역, ax가 안쪽 도화지 그림 영역
# 숫자데이터가 갖고 싶어서 수식만 가지고 들어온다. 필드명이 필요없다. 라벨을 별도로 찍을 거기 때문이다.

output_png = os.path.join(os.path.dirname(__file__), 'chart.png')
fig.savefig(output_png)

st.success('차트 저장을 완료했습니다.')