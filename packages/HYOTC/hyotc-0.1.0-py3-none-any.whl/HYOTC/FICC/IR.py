# -*- coding: utf-8 -*-
"""
Created on Fri Jan 30 15:27:22 2026

@author: S.T.Hwang
"""

def bnd_irr(price, coupon_rate, freq, maturity, face_value):
    import sympy as sp
    import numpy as np
    import pandas as pd

    r = sp.symbols('r', positive=True)

    # freq: 연 쿠폰 지급횟수
    period = 1 / freq

    T = np.arange(period, maturity + 0.001, period)
    nT = np.arange(1, len(T) + 1)
    Disc = 1 / (1 + r/freq) ** nT  # 할인율 적용

    # 현금흐름 계산
    coupons = coupon_rate * face_value
    CF = np.array([coupons / freq] * len(T))
    CF[-1] += face_value  # 만기 원금 상환

    # 할인 현금흐름
    Disc_CF = CF * Disc  # Discounted Cash Flow

    # 데이터프레임으로 보기
    df = pd.DataFrame({
        'Time': T,
        'CashFlow': CF,
        'DF': Disc,
        'Disc_CF': Disc_CF
    })

    print(df)

    # 합계 조건
    col_sum = df.sum(axis=0)
    SumP = col_sum['Disc_CF']
    eq = price - SumP

    sol = sp.solve(eq, r)

    return sol


# 채권 가격 구하는 함수
def bond_price(coupon_rate, freq, maturity, face_value, r_val):
  import sympy as sp
  import numpy as np
  import pandas as pd

  r = sp.symbols('r', positive=True)

  # freq: 연 쿠폰 지급횟수
  period = 1 / freq

  T = np.arange(period, maturity + 0.001, period)
  nT = np.arange(1, len(T) + 1)
  Disc = 1 / (1 + r/freq) ** nT  # 할인율 적용

  # 현금흐름 계산
  coupons = coupon_rate * face_value
  CF = np.array([coupons / freq] * len(T))
  CF[-1] += face_value  # 만기 원금 상환

  # 할인 현금흐름
  Disc_CF = CF * Disc  # Discounted Cash Flow

  # 데이터프레임으로 보기
  df = pd.DataFrame({
    'Time': T,
    'CashFlow': CF,
    'DF': Disc,
    'Disc_CF': Disc_CF
  })

  # 1) DF 열 갱신
  df["DF"] = df["DF"].apply(lambda expr: float(sp.N(expr.subs({r: r_val}))))

  # 2) Disc_CF 열 갱신
  df["Disc_CF"] = df["Disc_CF"].apply(lambda expr: float(sp.N(expr.subs({r: r_val}))))

  col_sum = df.sum(axis=0)
  SumP = col_sum['Disc_CF']

  return SumP,df


def bond_duration_convexity(coupon_rate, freq, maturity, face_value, r_val):
    """
    네 bond_price()를 이용해
    - Macaulay Duration (years)
    - Modified Duration (years)
    - Convexity (years^2)  [주기복리 기준]
    를 계산해 반환.
    """
    # 1) 가격과 현금흐름 DF 테이블
    price, df = bond_price(coupon_rate, freq, maturity, face_value, r_val)

    # df에는 Time, CashFlow, DF, Disc_CF가 있음 (Disc_CF = PV)
    out = df.copy()
    out["PV"] = out["Disc_CF"].astype(float)

    P = float(price)
    if P <= 0:
        raise ValueError("Bond price must be positive.")

    # 2) 가중치(각 현금흐름 PV / 가격)
    out["w"] = out["PV"] / P

    # 3) Macaulay Duration: sum(t * w)
    macaulay = float((out["Time"] * out["w"]).sum())

    # 4) Modified Duration (주기복리): D_mod = D_mac / (1 + y/freq)
    mod_duration = macaulay / (1.0 + r_val / freq)

    # 5) Convexity (주기복리, years^2)
    # 공식(주기복리) :
    # Conv = (1/P) * Σ [ CF_n * n(n+1) / (1+y/f)^(n+2) ] * (1/f^2)
    # 여기서 n은 1,2,... (지급회차), f=freq
    n = np.arange(1, len(out) + 1, dtype=float)
    y = float(r_val)
    f = float(freq)

    CF = out["CashFlow"].to_numpy(dtype=float)
    denom = (1.0 + y / f) ** (n + 2.0)

    convexity = float(np.sum(CF * n * (n + 1.0) / denom) * (1.0 / (P * f * f)))

    # 참고용 컬럼(검산/보고용)
    out["t_w"] = out["Time"] * out["w"]

    return {
        "Price": P,
        "MacaulayDuration": macaulay,
        "ModifiedDuration": mod_duration,
        "Convexity": convexity,
        "Table": out
    }
