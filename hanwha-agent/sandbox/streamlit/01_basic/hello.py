import streamlit as st

st.set_page_config(page_title="사내 업무 에이전트")

st.title("사내 업무 에이전트")
st.write("write는 화면에 텍스트를 출력하는 함수입니다.")

'''
count = 0 

if st.button("문서 1건 추가"):
    count = count + 1

st.write("추가한 문서 수 : ", count)
'''

st.header("제목")
st.subheader("소 제목")

st.markdown(
    "- python\n"
    "- fastAPI\n"
    "- streamlit\n"
)

st.divider()

st.caption("출처 - streamlit 공식 문서")