import streamlit as st
import streamlit_shadcn_ui as ui

st.title("shadcn 사용해보기")

ui.card(
    title="첫 카드",
    description="카드 설명",
    content="실제 내용2",
    key="first_card"
)

ui.badge("뱃지1", key="b_first")
ui.badge("뱃지2", key="b_second", variant="secondary")

ui.metric_card("전체 문서", "44", description="지난 주 대비 +3", key="m1")

if ui.button("문서 열기", key="open_btn"):
    st.write("문서 열기 버튼 클릭했습니다.")