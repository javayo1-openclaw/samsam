# samsam

실전 데이터 수집 중심의 공격형 자동매매 엔진 템플릿입니다.

## 포함 기능
- 실시간 루프 기반 자동 진입/청산
- 트레이드 로그(SQLite) 저장
- 최근 실전 결과 기반 자동 파라미터 보정
- 텔레그램 상태 알림 및 수동 명령
  - `/status`: 현재 상태/성과
  - `/buyup`: 수동 UP 진입
  - `/buydown`: 수동 DOWN 진입
  - `/close`: 현재 포지션 즉시 청산

## 주의
- 현재 `bot/polymarket_client.py`는 **시뮬레이션 플레이스홀더**입니다.
- 실제 투입 전 폴리마켓 API 인증/주문/체결 로직으로 교체해야 합니다.
- 자동 중지 조건은 사용자 요구에 맞춰 기본 미포함입니다.

## 빠른 시작
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a && source .env && set +a
python -m bot.engine
```

## 아키텍처
- `bot/engine.py`: 메인 트레이딩 루프, 텔레그램 명령 처리
- `bot/strategy.py`: 신호 점수화 + 온라인 자동 보정
- `bot/data_store.py`: 체결 결과 기록/요약
- `bot/telegram.py`: 텔레그램 송수신
- `bot/polymarket_client.py`: 거래소 어댑터 (현재 mock)
