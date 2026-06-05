# Samsung Auto Trader

한국투자증권 Open API 모의투자 환경에서 삼성전자 `005930`을 대상으로 작동하는 REST 기반 자동매매 예제입니다.

## 핵심 특징

- 모의투자 전용
- REST API만 사용
- WebSocket 사용 안 함
- 당일 access token 캐싱
- 삼성전자 `005930` 대상
- 초단기 이격도 전략
- 익절, 손절, 60초 시간청산
- 모의투자 요청 제한을 고려한 보수적 polling

## 전략

최근 20개 현재가 평균 대비 현재가 이격도를 계산합니다.

- 이격도 <= 99.6: 매수
- 이격도 >= 100.2: 매도
- 진입 후 +0.2%: 익절
- 진입 후 -0.15%: 손절
- 진입 후 60초 경과: 청산

## 폴더 구조

```text
samsung_auto_trader/
├─ main.py
├─ config.py
├─ logger.py
├─ auth.py
├─ api_client.py
├─ market_data.py
├─ account.py
├─ orders.py
├─ trader.py
├─ token_cache.json
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## GitHub Codespaces Secrets

아래 3개를 저장해야 합니다.

```text
GH_ACCOUNT
GH_APPKEY
GH_APPSECRET
```

저장 위치:

```text
GitHub → Settings → Codespaces → Secrets → New secret
```

계좌번호 예시:

```text
GH_ACCOUNT=12345678-01
```

또는

```text
GH_ACCOUNT=1234567801
```

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python main.py
```

## 브랜치 생성 후 업로드 예시

repo 루트에서 실행하세요.

```bash
git checkout -b samsung-auto-trader
git add samsung_auto_trader
git commit -m "Add Samsung mock auto trader"
git push -u origin samsung-auto-trader
```

main에 바로 올리고 싶으면 브랜치를 만들지 않고 아래처럼 해도 됩니다.

```bash
git add samsung_auto_trader
git commit -m "Add Samsung mock auto trader"
git push
```

## 주의사항

이 코드는 모의투자 환경을 위한 예제입니다. 실전투자를 가정하지 않습니다.

한국투자 Open API의 TR ID, endpoint, 응답 필드명은 API 문서 변경이나 계좌 유형에 따라 달라질 수 있습니다.
수정이 필요한 경우 `config.py`, `market_data.py`, `account.py`를 먼저 확인하세요.

특히 아래 값은 본인 API 문서와 다르면 수정해야 합니다.

```python
tr_id_current_price = "FHKST01010100"
tr_id_balance_mock = "VTTC8434R"
tr_id_buy_mock = "VTTC0802U"
tr_id_sell_mock = "VTTC0801U"
```

## 로그

실행 로그는 콘솔과 `trader.log`에 동시에 기록됩니다.

## 요청 제한 관련

모의투자 환경은 요청 제한이 엄격합니다.

이 프로젝트는 기본적으로 다음 방식으로 API 사용을 줄입니다.

- 토큰은 당일 재사용
- 현재가는 10초 간격 조회
- 잔고는 최소 30초 간격 캐싱
- 주문 직후에만 잔고를 다시 확인
- 초당 거래건수 초과 오류가 나오면 로그를 남기고 짧게 대기
