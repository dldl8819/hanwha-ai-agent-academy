# 파일 쓰기
with open("Heifam.txt", "w", encoding="utf-8") as f:
    f.write("안녕하세요.\n")
    f.write("헤이팸 유튜브 구독과 좋아요 알림설정까지 해주시면 큰 힘이 됩니다.\n")
    f.writelines(["헤이팸", "(HeiFam)"]) # 개행은 별도로 \n 작성해야 함
    print("유튜브 : \t https://www.youtube.com/@Hei-minsik", file=f) # print()는 자동 개행됨

# 파일 이어서 쓰기
with open("Heifam.txt", 'a', encoding='utf-8') as f:
    f.write("홈페이지 : \t https://heifam.co.kr")