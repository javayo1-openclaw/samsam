# samsam

폴리마켓 **BTC 15분 Up/Down** 규칙 기반 자동매매 봇입니다.

## 현재 반영된 전략 규칙
- 대상: BTC 15분 Up/Down (YES/NO token_id 고정)
- 라운드 시작(정각 15분 단위) 후 **5초 동안 BTC 가격 추세**를 보고 방향 결정
  - 상승: `UP`
  - 하락: `DOWN`
- **라운드 10분 시점**에 선택된 방향 토큰 가격이 `0.30 이하`일 때만 진입
- 진입 주문은 FOK, 실패 시 **반대 방향으로 1회 재시도(반대매매)**
- 청산 규칙
  - 정상 진입: 수익률 150% 이상이면 자동 청산
  - 반대 진입: 수익률 100% 이상이면 자동 청산
  - 만기 3분 전(`T-180s`) 자동 청산
- 연속진입 없음: 라운드당 최대 1회 진입

## 텔레그램 명령
- `/status`: 상태/성과 조회
- `/close`: 현재 포지션 즉시 청산
- `/history`: 최근 5건 전적 + 한글 진입근거/청산사유

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

## 3) 주요 설정값
- `BTC15M_YES_TOKEN_ID`, `BTC15M_NO_TOKEN_ID`
- `ENTRY_PRICE_CAP=0.30`
- `TAKE_PROFIT_PCT_PRIMARY=1.5` (정상 진입 익절 150%)
- `TAKE_PROFIT_PCT_FALLBACK=1.0` (반대 진입 익절 100%)
- `ENTRY_CHECK_SECOND=600` (10분)
- `FORCE_EXIT_BEFORE_EXPIRY_SEC=180` (만기 3분 전)
- `ORDER_SIZE`

## 주의
- 실거래 코드이므로 소액으로 먼저 검증 권장
- BTC 가격 추세 소스는 Binance ticker API를 사용
