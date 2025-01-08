# HTTP

**Protocol** : HTTP에서 P는 Protocol의 약자이다.   
Protocol은 도로교통에서의 신호체계처럼 정보통신에서의 신호체계를 말한다.   
각 프로토콜마다 정해진 포맷이 있고 그 포맷에 맞춰 데이터를 전송함으로써 데이터의 내용을 식별한다.

**HTTP Message format**
- Request format
  - Start Line: Http Method / URL / Http Version
  - Header: 
    - Content-Type: 전송할 body의 데이터 형식 정보
    - User-Agent: 요청자의 OS ~ Browser 정보
  - Body:
    - form data(Contetnt-Type: x-www-form-urlencoded)
    - JSON(Contetnt-Type: application/json)

- Response format
  - Start Line: Http Version / State Code / Reason Phrase
  - Header
  - Body
    - JSON(Content-Type: application/json)
    - HTML(Content-Type: text/html)



# Web Rendering

**Rendering** : HTML, CSS, JavaScript, image, video, font 등 모든 웹 페이지 구성 요소를 화면에 표시하는 과정  

**Web Page Rendering Time**
- Static Page: 모든 웹 페이지 구성 요소를 HTML에 미리 채워서 받는 방식
- Dynamic Page: HTML로 뼈대만 구성하고, 필요한 데이터는 추가 요청에 따라 그때그때 채워주는 방식

**Web Page Rendering Location**
- SSR(Server Side Rendering): 서버에서 렌더링을 완료하고 클라이언트에게 보내주는 방식
- CSR(Client Side Rendering): 서버에서 자원만 보내고 클라이언트에서 렌더링을 진행하는 방식



# Web Scraping - Rendering Type
**Scraping** : 특정 자료에서 특정 정보를 추출하는 작업

   - URL 확인 - Static Page (SSR, CSR)  
    : 요청 시 일정 패턴을 가지고 URL이 변한다면 Static Page일 가능성이 높다.  
    다음 페이지를 클릭했을 때 URL 내 Query Param 중 Page(PageIndex)값이 증가한다거나  
    상세 페이지를 클릭했을 때 URL 내 특정 Path Variable 값만 변하는지 확인해본다.  
    URL에서 패턴을 찾았다면 이를 바탕으로 요청을 반복하면 된다.
       - Path Variable 예시: https://www.shopping.com/products/```4567```
       - Query Param 예시: https://www.shopping.com/products```?opnMod=P&PageIndex=1```  
       ※ ?로 시작하면 Query Param이고 &은 Query Param 간 구분자이다.

   - API 확인 - Dynamic Page   
    : 다음 페이지나 상세 페이지를 클릭했을 때 URL에는 아무 변화가 없고 페이지 내부 데이터만 바뀌는 경우가 있다.  
    이런 경우는 내부 데이터만 따로 API 요청-응답하고 있기 때문에 표면상 드러나는 URL에는 아무 변화가 없는 것이다.  
    이때는 개발자 도구(Ctrl+Shift+I)->Network->Fetch/XHR을 켠 상태에서 다음 페이지 혹은 상세 페이지를 클릭해본다.  
    그러면 별도의 HTTP Message가 들어올텐데 이 API 정보를 활용하면 된다.  

   - HTML elements 확인 - Dynamic Page (SSR / CSR)   
    : 대개 개발자 도구(Ctrl+Shift+I)->elements->요소 선택 모드(Ctrl+Shift+C)로 추출하려는 데이터를 확인했을 때   
    값이 채워져있다면 SSR 방식이고, 값이 비워져있다면 CSR 방식이다.  
     >※ SSR + Dynamic Page에서는 서버가 동적 데이터를 모두 채운 html을 클라이언트에게 다시 보내주기 때문에 html element에 값이 채워져 있지만  
     CSR + Dynamic Page에서는 기존 html에 클라이언트가 서버로부터 동적 데이터를 받아 직접 값을 채워넣기 때문에 개발자 도구에서 볼 때 html element가 비워져 보인다.

 <table><thead>
  <tr>
    <th></th>
    <th>SSR</th>
    <th>CSR</th>
  </tr></thead>
<tbody>
  <tr>
    <td>Static Page</td>
    <td> - 요청 유형: GET Requset<br>  - 추출 대상: WebSite HTML elements </td>
    <td> - 요청 유형: GET Requset<br>  - 추출 대상: WebSite HTML elements</td>
  </tr>
  <tr>
    <td>Dynamic Page</td>
    <td> - 요청 유형: GET, POST Requset<br>  - 추출 대상: WebSite HTML elements or API JSON data</td>
    <td> - 요청 유형: GET, POST Requset<br>  - 추출 대상: API JSON data</td>
  </tr>
</tbody>
</table>



# Web Scraping - Extraction Method

- WebSite HTML elements 추출
  1. HTTP Request 전송
      - Request Header 설정
        - User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36  
       ※ 최소 설정 헤더이며, 윈도우 환경 내 크롬 브라우저 사용 예시이다.  
      - URL 설정  
        - WebSite URL로 설정  
      ※ Path Variable 혹은 Query Param에서 찾은 패턴 적용하여 반복 요청

  2. HTTP Response 가공
     1. WebSite에서 개발자 도구(Ctrl+Shift+I)->elements->요소 선택 모드(Ctrl+Shift+C)로 추출할 데이터를 찾고  
      마우스 오른쪽 클릭 -> copy -> copy selector로 경로 복사
     2. python(beautifulsoup4)를 사용하여 Response Body 내 copy selector 위치에 해당하는 데이터 추출  
  > ※ CSR + Dynamic Page의 경우 API JSON data 추출이 빠르고 편하지만 비공개 API가 사용될 경우 이 방식으로 처리한다.  
  브라우저 드라이버(Python(selenium))를 통해 HTTP Request를 보내야 HTML에 값이 채워진 Response를 받는다.

- API JSON data 추출
  1. API 찾기  
  - 개발자 도구(Ctrl+Shift+I)->Network->Fetch/XHR을 켠 상태에서 다음 페이지나 상세 페이지 등을 클릭해가며 추가되는 API URL을 확인한다.
    - API URL 클릭->payload: API Requset Body 정보
    - API URL 클릭->Response: API Response Body 정보
  2. HTTP Request 전송  
     - Request Header 설정
        - Content-Type: application/x-www-form-urlencoded  
        - User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36  
        ※ Header 및 payload 확인 후 알맞게 수정한다.
     - URL 설정  
        - API URL로 설정  
     - Request Body 설정
         - API payload 정보에 맞춰 설정
  3. HTTP Response 가공
     - Response Body를 리스트 형태의 json 데이터로 파싱하고 리스트 요소에 접근하여 원하는 데이터 추출  
     ※ 대부분 JSON 형식이지만 아닐 경우 그에 맞게 파싱
