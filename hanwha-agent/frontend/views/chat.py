from __future__ import annotations
import streamlit as st
from core import api_client
from ui.card import page_header
from ui.source import sources as source_block 
from ui.status import steps as step_list

def render() -> None:
    page_header('AI 업무 도우미', subtitle="사내 규정을 근거로 답변합니다.")
    # 채팅 내역 유무 확인 후, 없으면 sesseion에 'chat'이라는 빈 리스트 생성 
    if 'chat' not in st.session_state:
        st.session_state['chat'] = []
    # 기존 대화내용 화면에 출력 
    for message in st.session_state['chat']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    # 채팅 입력창 생성 
    question = st.chat_input('무엇을 도와드릴까요?')
    if not question:
        return 
    # 대화 내역에 질문 추가 
    st.session_state['chat'].append({'role': 'user', 'content': question})
    # 질문 화면에 출력 
    with st.chat_message('user'):
        st.markdown(question)
    # 답변 화면에 출력 
    with st.chat_message('assistant'):
        with st.spinner('사내 규정 찾아보는 중...'):
            # 백엔드에 질문 주고 답변 요청 
            try:
                response = api_client.ask(question) 
            except api_client.ApiError as e:
                st.error(str(e))
                return 
        # 답변 화면에 뿌리기 
        answer = response.get('answer', '')
        st.markdown(answer)

        # 검색 과정 
        step_list(response.get("steps", []))

        # 근거 문서 
        enough = response.get("enough_evidence", True)
        srcs = [{k: v for k, v in one.items() if k != "doc_id"}
            for one in response.get("sources", [])]
        if srcs:
            st.caption("근거 문서" if enough else "검색된 문서 - 임계값 미달, 답변 근거로 쓰지 않음")
            source_block(srcs, weak=not enough)

        if not enough:
            st.info("등록된 문서에서 근거를 확인하지 못했습니다. 담당 부서에 문의해 주세요.")

    # 대화 내역에 답변 추가 
    st.session_state['chat'].append({'role': 'assistant', 'content': answer})

    