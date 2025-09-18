# 프로젝트 환경 구축 가이드

## 실행 환경 구축

### CPython 설치
1. [Python 공식 홈페이지](https://www.python.org)에서 Python 컴파일러(인터프리터)를 다운로드하여 설치
2. 설치 과정 중 `Add Python to PATH` 옵션을 체크하여 시스템 PATH에 Python을 추가
3. 설치 경로 어렵지 않게 설정

### IDE 설정
1. [Visual Studio Code](https://code.visualstudio.com)를 설치
2. VSCode의 `Extensions`에서 `Python` 확장 프로그램을 설치
3. CPython 폴더 하위에 프로젝트용 폴더 생성
4. `Run and Debug` (`Ctrl + Shift + D`)에서 `create launch.json` 클릭 후 `Python File` 디버거를 설치(launch.json 생성)
5. 프로젝트 폴더에 `.py` 확장자로 Python 파일 생성 후 실행

### 가상 환경 구축 및 라이브러리 설치

1. PowerShell 또는 명령 프롬프트에서 아래 명령어를 입력하여 가상 환경을 구축
   ```bash
   1-1. python -m venv .venv (.venv는 가상 환경에 대한 암묵적 작명법, 하위 폴더 생성 후 가상 환경 구축)
   1-2-1. .\.venv\Scripts\activate.bat (윈도우 cmd 기준 가상 환경 활성화, 실행 환경에 따라 명령어가 다를 수 있다.)
   1-2-2. .venv\Scripts\activate (1-2-1이 안될 경우)
   1-3. pip install 라이브러리명 입력 (venv를 통해 해당 프로젝트 폴더에서만 라이브러리가 설치되도록 설정)
2. VS code 우측 하단에 interpreter가 '.venv':venv로 안되어 있다면 클릭해서 Create Virtual Environment으로 venv로 설정
3. 가상 환경 비활성화: deactivate(실행 중인 (.venv)cmd 창에 명령어 입력)


## 인터렉티브 환경 추가

### IDE 설정
1. VSCode의 `Extensions`에서 `Jupyter` 확장 프로그램을 설치
2. `command palette` (`Ctrl + Shift + P`)에서 `create: New Jupyter Notebook` 입력
3. .ipynb 파일 생성
