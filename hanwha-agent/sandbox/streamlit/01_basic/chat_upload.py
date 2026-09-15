import streamlit as st

st.title("AI 채팅창")

# 채팅 메시지 저장소 없으면 생성
if "messages" not in st.session_state:
    st.session_state.messages = []

# 파일 업로드
up = st.file_uploader("파일 업로드", type=["docx", "pdf"])
if up is not None:
    st.success(f"업로드 파일명 - {up.name} 사이즈 - ({up.size:,} bytes)")

# 채팅
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["text"])

# 채팅 입력창
q = st.chat_input("문의 내용")
if q:
    st.session_state.messages.append({"role": "user", "text": q})
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write("기능 구현은 추후에 진행")

HISTORY = [
    {"role": "user", "text": "출장비 기준이 뭔가요"},
    {"role": "assistant", "text": "DOC-HR-014 제14조입니다"},
    {"role": "user", "text": "광역시는요"},
    {"role": "assistant", "text": "3급 70,000원입니다"},
    {"role": "user", "text": "숙박비 말고 식비는요"},
    {"role": "assistant", "text": "제12조를 보세요"},
]

def trim_history(messages, max_turn=2):
    keep = max_turn * 2
    if len(messages) <= keep:
        return messages
    return messages[-keep:]

print(trim_history(HISTORY, max_turn=2)[0]["text"])