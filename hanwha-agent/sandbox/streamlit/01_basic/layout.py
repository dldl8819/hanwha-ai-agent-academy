import streamlit as st

st.title("레이아웃")

# 가로로 나누기
c1, c2, c3 = st.columns(3)
c1.metric("전체 문서", "44")
c2.metric("python", "33")
c3.metric("fastapi", "22")

# 컨테이너
with st.container(border=True):
    st.subheader("컨테이너 내부")
    st.caption("컨테이너 끝")

# 탭
t1, t2 = st.tabs(["python", "streamlit"])
t1.write("python tab")
t2.write("streamlib tab")

