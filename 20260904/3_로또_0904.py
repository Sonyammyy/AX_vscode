# 1 ~ 45 숫자 중에 6개 숫자 5세트
# random 모듈을 이용해서 중복되지 않게 넣어야 한다. 큰 수가 먼저 나올 수도 있기 때문에 정렬해야 한다.
# 이왕이면 예쁘게 이모지 색깔 공을 넣는다.
# 자료 구조는 중복되지 않는 set을 써야 한다.
# 버튼을 누르면 5세트를 한번에 생성한다.
# datetime 으로 생성 시간도 함께 보여준다.

import streamlit as st
import random
from datetime import datetime   # datetime 안에 들어 있는 datetime 함수만 호출할게

st.title('🎱 로또 번호 자동 생성기')
st.caption('버튼을 누르면 1 ~ 45 사이의 중복 없는 번호 6개짜리 세트를 5개 만들어 드립니다. 🍀')


def lotto_one_set() -> list:
    """1 ~ 45 에서 중복 없이 번호 6개 뽑아 정렬된 리스트로 반환"""

    number = set[int]()
    while len(number) < 6:
        number.add(random.randint(1,45))    # 1 이상 45 이하 정수 하나
    return sorted(number)

def get_ball_emoji(num: int) -> str:
    """번호 대역에 맞는 색깔 공 이모지와 번호 문자열 반화"""
    if num <= 10:
        return f"🟡 {num}"
    elif num <= 20:
        return f"🔵 {num}"
    elif num <= 30:
        return f"🔴 {num}"
    elif num <= 40:
        return f"⚫ {num}"
    else:
        return f"🟢 {num}"

st.markdown('---')

if st.button('🍀 5세트 번호 생성하기', key='lotto_generate_btn'):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.write(f'생성 시각: **{now_str}**')

    for set_index in range(1,6):
        lotto_num = lotto_one_set()
        formatted_balls = " ".join([get_ball_emoji(n) for n in lotto_num])

        st.write(f'**{set_index}세트:** {formatted_balls}')



