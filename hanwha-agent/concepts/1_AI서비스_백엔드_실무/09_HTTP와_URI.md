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

## HTTP (HyperText Transfer Protocol)

HTTP 메시지 하나로 거의 모든 형태의 데이터를 전송할 수 있다 — HTML/TEXT, 이미지·음성·영상·파일, JSON/XML(API 응답) 등.

### HTTP 버전

| 버전 | 전송 계층 |
| --- | --- |
| HTTP/1.1, HTTP/2 | TCP |
| HTTP/3 | UDP |

### HTTP 메시지 구조

요청/응답 메시지 모두 시작줄(요청 라인 또는 상태 라인) + 헤더 + 빈 줄 + 바디(선택) 구조로 이루어진다. 바디는 GET처럼 조회만 하는 요청에는 보통 없고, POST/PUT처럼 데이터를 실어 보내는 요청·응답에 붙는다.

### HTTP 메서드

| method | 기능 | 회원 기능 예 | URI 예 | 데이터 전송 위치 |
| --- | --- | --- | --- | --- |
| GET | 데이터 조회 | 회원 정보 조회 | `/members/{id}` (예: `/members/3`) | 쿼리스트링(`?query`) |
| POST | 요청 데이터 처리, 등록 요청 | 회원 등록 | `/members` | 메시지 바디 |
| PUT | 데이터 대체, 없으면 생성 | 회원 정보 대체 | `/members/{id}` | 메시지 바디 |
| PATCH | 데이터 부분 변경 | 회원 정보 부분 수정 | `/members/{id}` | 메시지 바디 |
| DELETE | 데이터 삭제 | 회원 정보 삭제 | `/members/{id}` | — |
| HEAD | 바디를 제외하고 헤더만 반환 | | | |
| OPTIONS | 통신 가능한 옵션을 설명 (CORS에서 사용) | | | |

### HTTP 상태 코드

| 코드대 | 이름 | 예 | 의미 |
| --- | --- | --- | --- |
| 1xx | Informational | | 요청이 수신되어 처리 중 |
| 2xx | Successful | 200, 201 | 요청 정상 처리 |
| 3xx | Redirection | 301, 302, 308 | 요청을 완료하려면 추가 행동이 필요 |
| 4xx | Client Error | 400, 401, 403, 404 | 클라이언트의 잘못된 요청이라 서버가 처리할 수 없음 |
| 5xx | Server Error | 500, 503 | 서버가 정상 요청을 처리하지 못함 |

### HTTP 헤더

전송할 때 필요한 부가 정보를 담는 자리다. 역할에 따라 General/Request/Response/Entity(표현 정보) 헤더로 나뉜다.

| 헤더 | 설명 | 예 |
| --- | --- | --- |
| Content-Type | 바디 데이터의 형식 | `application/json`, `text/html;charset=utf-8`, `image/png` |
| Content-Encoding | 데이터의 압축 방식 | `gzip` |
| Content-Language | 데이터의 언어 | `ko`, `en` |
| Accept | 클라이언트가 선호하는 응답 미디어 타입 | `text/*`, `text/plain`, `application/json` |
| User-Agent | 요청을 보낸 클라이언트(브라우저/앱) 정보 | `Mozilla/5.0 (...) Chrome/152.0.0.0 Safari/537.36` |
| Authorization | 클라이언트 인증 정보 | `Bearer xxxxxxxxxxx` |
| Cookie | 클라이언트가 서버에서 받아 저장해둔 쿠키 | 키=값, 유효시간, 도메인, 경로 |

참고: 2일차(day02) 이후 네트워크/HTTP 강의 노트 (별도 실습 노트북 없음)
