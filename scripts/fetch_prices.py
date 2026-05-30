#!/usr/bin/env python3
"""
KOSPI / S&P 500 / 넥슨게임즈 일봉 종가 수집 스크립트.

- 데이터 소스: yfinance (Yahoo Finance)
- 기간: 최근 3년
- 출력: data/prices.json (날짜별 종가 dict)

GitHub Actions에서 매일 1회 실행 → 동일 폴더의 JSON을 갱신하여 커밋.
HTML에서는 raw.githubusercontent.com 으로 fetch.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import yfinance as yf

# 심볼 → 출력 키 매핑 (HTML 쪽 instruments 이름과 일치시키기 위함)
SYMBOLS: dict[str, str] = {
    "^KS11": "kospi",        # 코스피 지수
    "^GSPC": "sp500",        # S&P 500
    "225570.KQ": "nexon",    # 넥슨게임즈 (KOSDAQ)
}

YEARS = 3
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.json"


def fetch_series(symbol: str, start: dt.date, end: dt.date) -> dict[str, float]:
    """심볼 한 종목의 일별 종가를 {YYYY-MM-DD: close} dict로 반환."""
    ticker = yf.Ticker(symbol)
    # auto_adjust=False 로 원래 종가 사용 (수정 종가 X)
    hist = ticker.history(
        start=start.isoformat(),
        end=end.isoformat(),
        interval="1d",
        auto_adjust=False,
    )
    if hist.empty:
        raise RuntimeError(f"{symbol}: 빈 결과")

    result: dict[str, float] = {}
    for ts, row in hist.iterrows():
        close = row.get("Close")
        if close is None or (isinstance(close, float) and (close != close)):  # NaN
            continue
        date_key = ts.strftime("%Y-%m-%d")
        # 소수점 2자리로 반올림 (지수는 그대로, 주식은 원 단위지만 통일)
        result[date_key] = round(float(close), 4)
    return result


def main() -> int:
    today = dt.date.today()
    start = today - dt.timedelta(days=YEARS * 365 + 30)  # 휴장일 보정 여유
    end = today + dt.timedelta(days=1)  # yfinance end는 exclusive

    out: dict = {
        "updated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": start.isoformat(), "end": today.isoformat()},
        "symbols": {},
    }

    errors: list[str] = []
    for symbol, key in SYMBOLS.items():
        try:
            series = fetch_series(symbol, start, end)
            out["symbols"][key] = {
                "symbol": symbol,
                "count": len(series),
                "latest_date": max(series.keys()),
                "latest_close": series[max(series.keys())],
                "data": series,
            }
            print(f"[OK] {symbol} ({key}): {len(series)}개, 최근 {max(series.keys())} = {series[max(series.keys())]}")
        except Exception as e:
            errors.append(f"{symbol}: {e}")
            print(f"[ERR] {symbol}: {e}", file=sys.stderr)

    if not out["symbols"]:
        print("모든 심볼 실패", file=sys.stderr)
        return 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # 사람이 읽기 쉽도록 + diff 최소화를 위해 sort + indent
    OUT_PATH.write_text(
        json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\n저장 완료: {OUT_PATH} ({size_kb:.1f} KB)")
    if errors:
        print(f"부분 실패: {errors}", file=sys.stderr)
        # 부분 성공이어도 0 반환 → 커밋은 진행
    return 0


if __name__ == "__main__":
    sys.exit(main())
