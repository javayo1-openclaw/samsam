# samsam

폴리마켓 **BTC 15분 Up/Down** 자동매매 봇입니다.

## 핵심 기능
- Polymarket CLOB API 연동(키 기반)
- BTC 15m YES/NO 토큰만 매매
- 점수 기반 자동 진입 (UP/DOWN)
- 익절 자동 청산(`TAKE_PROFIT_PCT`)
- 최대 보유시간 청산(`MAX_HOLD_SECONDS`)
- 텔레그램 상태/수동 제어
  - `/status`: 현재 상태/성과
  - `/buyup`: 수동 UP 진입
  - `/buydown`: 수동 DOWN 진입
  - `/close`: 즉시 청산
- 실전 체결 데이터 SQLite 저장 + 주기적 파라미터 자동 조정

## 1) 사전 준비
1. BTC 15분 마켓의 YES/NO `token_id` 확인
2. Polymarket private key / api key / secret / passphrase 준비
3. 텔레그램 봇 토큰과 chat id 준비

## 2) 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 값 입력
set -a && source .env && set +a
python -m bot.engine
```

## 3) 설정값
- `BTC15M_YES_TOKEN_ID`, `BTC15M_NO_TOKEN_ID`: 15분 BTC Up/Down 토큰 ID
- `TAKE_PROFIT_PCT`: 예) `0.02` = +2% 도달 시 자동 청산
- `MAX_HOLD_SECONDS`: 최대 보유시간(초)
- `ORDER_SIZE`: 1회 주문 수량

## 주의
- 현재는 단일 포지션 모델(동시 다중 포지션 없음)
- 봇은 공격형 자동매매를 전제로 하므로 실제 운용 전 소액 테스트 권장
