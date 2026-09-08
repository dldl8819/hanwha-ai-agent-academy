# HTTP와 URI

## 웹 요청과 URI

브라우저로 웹 서비스를 요청할 때는 URI로 원하는 자원을 지정한다.

**URI (Uniform Resource Identifier)**

- Uniform: 자원을 식별하는 통일된 방식
- Resource: 자원
- Identifier: 다른 것과 구분하는 데 필요한 정보

즉 자원이 어디 있는지, 그 자원 자체를 식별하는 방법이다.

### URI 구조

```text
프로토콜:// IP(또는 도메인) : 포트번호 / 경로 ... ? 쿼리 # fragment
```

예시로 뜯어보면:

```text
https://www.google.com/search?q=hello&oq=hello&gs_lcrp=EgZjaHJ..생략..&ie=UTF-8

* 프로토콜   : https
* IP        : www.google.com (도메인이 IP를 대신함)
* Port      : 443 (https 기본 포트라 생략됨)
* 경로       : /search
* 쿼리스트링  : ?q=hello&oq=hello&...  (파라미터/쿼리)
```

```text
https://{ip}/p/Day05?source=copy_link#3d5170418e1b804eba09c55c857dc56c

* 경로   : /p/Day05
* 쿼리   : ?source=copy_link
* fragment : #3d5170418e1b804eba09c55c857dc56c  (같은 페이지 안의 특정 위치를 가리킴, 서버로는 전송되지 않음)
```

포트 번호는 프로토콜의 기본 포트(HTTP=80, HTTPS=443)와 같으면 생략할 수 있다.

참고: 2일차(day02) 이후 네트워크/HTTP 강의 노트 (별도 실습 노트북 없음)
