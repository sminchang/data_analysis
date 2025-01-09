# Web

**Web** : HTTP로 연결된 통신망  

**HTTP** : HTTP에서 P는 Protocol의 약자이다. Protocol은 도로교통에서의 신호체계처럼 정보통신에서의 신호체계를 말한다. 각 프로토콜마다 정해진 포맷이 있고 그 포맷에 맞춰 데이터를 전송함으로써 데이터의 내용을 식별한다. HTTP도 그런 프로토콜의 일종이라고 보면 된다.

**HTTP Message format**
- Request format
  - Start Line: Http Method / URL / Http Version
  - Headers:
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

**Web Page Type**
- Static Page: 모든 웹 페이지 구성 요소를 HTML에 미리 채워서 받는 방식
- Dynamic Page: HTML로 뼈대만 구성하고, 필요한 데이터는 추가 요청에 따라 그때그때 채워주는 방식

**Web Page Rendering Type**
- SSR(Server Side Rendering): 서버에서 렌더링을 완료하고 클라이언트에게 보내주는 방식
- CSR(Client Side Rendering): 서버에서 자원만 보내고 클라이언트에서 렌더링을 진행하는 방식  

※ Rendering : HTML, CSS, JavaScript, image, video, font 등 모든 웹 페이지 구성 요소를 화면에 표시하는 과정  



# Web Scraping

**Scraping** : 특정 자료에서 특정 정보를 추출하는 작업   
※ Crawling:  자동으로, 지속적으로 정보를 수집하는 작업 

- **요청 정보 확보** - HTTP Method  
: HTTP Method에 따라 요청 정보의 위치가 달라지기 때문에 HTTP Method를 파악한다.  
: 페이지 전환 시 URL이 변한다면 보통 GET Request, 변하지 않는다면 POST Reqeust일 확률이 높다.  
    - GET Request  
   : URL에 페이지 요청 상세 정보를 담아서 보내는 방식이다.
      - Path Variable 예시: https://www.shopping.com/products/```4567```
      - Query Param 예시: https://www.shopping.com/products```?opnMod=P&PageIndex=1```  
       ※ ?로 시작하면 Query Param이고 &은 Query Param 간 구분자이다.
    - POST Request  
   : Request Body에 페이지 요청 상세 정보를 담아서 보내는 방식이다. URL에는 아무 변화가 없다.   
   : 개발자 도구에서 해당 HTTP Message(이하 API)를 찾아 다음의 정보들을 찾을 수 있다. 
      - payload: Requset Body
      - Response: Response Body

- **응답 정보 확보** - Web Page Type  
: Web Page Type에 따라 추출할 응답 정보가 달라지기 때문에 Web Page Type을 파악한다.   
: 페이지 전환 시 "개발자 도구(Ctrl+Shift+I)->Network->Fetch/XHR"에 API가 들어오지 않는다면 Static Page, 들어온다면 Dynamic Page일 확률이 높다.  
   - Staitc Page  
    : HTML 전체를 요청-응답받고 거기서 필요한 데이터만 추출한다.
     1. "개발자 도구(Ctrl+Shift+I)->elements->요소 선택 모드(Ctrl+Shift+C)"를 켜고 추출할 영역을 클릭한다.
     2. 개발자 도구 창에 선택한 HTML 위치가 표시되면 "마우스 오른쪽 클릭->copy->copy selector"로 위치를 복사한다.
     3. Web Page URL + Requst Headers(User-Agent..) + Reqeust Body를 설정하고 요청을 보낸다. (python(Requests)활용)
     4. 응답받은 HTML에서 이전에 복사한 HTML 내 추출할 데이터 위치를 활용하여 데이터를 추출한다. (python(Beautifulsoup4)활용)
   - Dynamic Page  
    : Dynamic Data(이하 JSON)만 요청-응답받고 거기서 필요한 데이터를 추출한다.
     1. 내부 API URL + Requst Headers(Content-Type, User-Agent..) + Reqeust Body를 설정하고 요청을 보낸다. (python(Requests)활용)
     2. 응답받은 JSON을 파싱하고 필요한 데이터만 추출한다.



# 번외
- 로그인 페이지에 접근해야하는 경우  
: 브라우저에 로그인 정보를 저장해두고 브라우저 드라이버(Python(selenium))를 통해 페이지를 로딩하고 가져오는 방식을 취할 수 있다.

- 실시간 서비스를 하는 페이지인 경우  
: 웹소켓 등을 사용하여 내부 데이터는 다른 프로토콜로 통신할 수 있다. 이 경우 접근 방식을 달리해야 할 것으로 보인다.

- 개발자 도구에서 html element 값이 안보이는 경우  
: SSR + Dynamic Page에서는 서버가 동적 데이터를 모두 채운 html을 클라이언트에게 다시 보내주기 때문에 html element에 값이 채워져 있지만 CSR + Dynamic Page에서는 기존 html에 클라이언트가 서버로부터 동적 데이터를 받아 직접 값을 채워넣기 때문에 개발자 도구에서 볼 때 html element가 비워져 보인다.
