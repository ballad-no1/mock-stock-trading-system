# Samsung Auto Trader Mock

한국투자증권 Open API **모의투자 REST API 전용** 삼성전자(005930) 자동 주문 예제입니다.

이 프로젝트는 웹소켓을 사용하지 않습니다. 모의투자 API 호출 제한을 고려해 보수적인 polling 방식으로 동작합니다.

## 기능

- 삼성전자 현재가 조회
- 계좌 잔고/보유수량 조회
- 현재가 기준 지정가 매수: 현재가 - 1,000원
- 현재가 기준 지정가 매도: 현재가 + 1,000원
- 주문 후 잔고/보유수량 재조회로 체결 여부 추정
- 09:10 ~ 15:30 사이에만 주문
- 당일 발급 토큰 캐시 재사용
- 로그 파일 저장

## 폴더 구조

```text
samsung_auto_trader/
├── main.py
├── config.py
├── auth.py
├── api_client.py
├── market_data.py
├── account.py
├── orders.py
├── trader.py
├── logger.py
├── token_cache.json
├── requirements.txt
├── README.md
└── .gitignore
```

## 환경변수 설정

GitHub Codespaces에서는 아래 경로에서 저장합니다.

```text
https://github.com/settings/codespaces
```

Repository secrets 또는 Codespaces secrets에 다음 값을 저장하세요.

```text
GH_ACCOUNT=12345678-01
GH_APPKEY=발급받은_모의투자_APP_KEY
GH_APPSECRET=발급받은_모의투자_APP_SECRET
```

`GH_ACCOUNT`는 모의투자 계좌번호입니다. 보통 `앞 8자리-뒤 2자리` 형식으로 넣으면 됩니다. 예: `12345678-01`

## 실행 방법

```bash
cd samsung_auto_trader
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## VS Code / Codespaces에서 실행

1. GitHub repository에 이 폴더를 업로드합니다.
2. Codespaces secret에 `GH_ACCOUNT`, `GH_APPKEY`, `GH_APPSECRET`를 저장합니다.
3. Codespace 터미널에서 `python main.py`를 실행합니다.

## 주의사항

- 이 코드는 모의투자 전용 예제입니다.
- 실전투자용으로 가정하지 않았습니다.
- API 필드명 또는 TR ID가 바뀔 수 있으므로 `config.py`의 TR ID를 확인하세요.
- 모의투자는 호출 제한이 낮으므로 `poll_interval_seconds`를 너무 작게 줄이지 마세요.
- 체결 확인은 보유수량 변화로 추정합니다. 정확한 주문체결 조회가 필요하면 별도 주문체결조회 API를 추가하세요.
- `token_cache.json`은 실제 토큰을 담을 수 있으므로 Git에 올리지 않는 것을 권장합니다.
