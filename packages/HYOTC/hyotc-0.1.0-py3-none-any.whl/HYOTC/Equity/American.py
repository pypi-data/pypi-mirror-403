# -*- coding: utf-8 -*-
"""
Created on Tue Jan  6 10:23:49 2026

@author: S.T.Hwang
"""

import numpy as np
from math import log, sqrt, exp
from scipy.stats import norm
from scipy.optimize import brentq

def bs_price(S, K, T, r, q, sigma, option="call"):
    """Black-Scholes European option price (continuous dividend yield q)."""
    if T <= 0:
        intrinsic = max(S - K, 0.0) if option == "call" else max(K - S, 0.0)
        return intrinsic

    d1 = (log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    if option == "call":
        return S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    else:
        return K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)

def bs_delta(S, K, T, r, q, sigma, option="call"):
    """Black-Scholes European delta (continuous dividend yield q)."""
    if T <= 0:
        if option == "call":
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0

    d1 = (log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrt(T))
    if option == "call":
        return exp(-q * T) * norm.cdf(d1)
    else:
        return exp(-q * T) * (norm.cdf(d1) - 1.0)

def _baw_params(T, r, q, sigma):
    """
    BAW에서 쓰는 공통 파라미터.
    b = r - q (cost of carry)
    """
    b = r - q
    sig2 = sigma * sigma
    # M = 2r/sigma^2, N = 2b/sigma^2
    M = 2.0 * r / sig2
    N = 2.0 * b / sig2
    # Kappa = 1 - exp(-rT)
    kappa = 1.0 - exp(-r * T)
    return b, M, N, kappa

def _baw_q1_q2(T, r, q, sigma):
    """
    q1, q2는 BAW 논문/실무 표기에서 임계가격 방정식에 들어가는 지수.
    (문헌마다 기호가 조금 다르지만, 아래 형태가 표준적으로 쓰입니다.)
    """
    b, M, N, kappa = _baw_params(T, r, q, sigma)
    sig2 = sigma * sigma

    # sqrt term
    sqrt_term = sqrt((N - 1.0) ** 2 + 4.0 * M / kappa)

    # Call 쪽 지수(양수)
    q2 = 0.5 * (-(N - 1.0) + sqrt_term)
    # Put 쪽 지수(음수)
    q1 = 0.5 * (-(N - 1.0) - sqrt_term)
    return q1, q2

def american_baw(S, K, T, r, q, sigma, option="call"):

    """
    Barone-Adesi & Whaley approximation for American option (continuous dividend yield).

    Parameters
    ----------
    S : float
    K : float
    T : float (years)
    r : float
    q : float (dividend yield)
    sigma : float
    option : "call" or "put"

    Returns
    -------
    price : float
    """

    # 만기면 내재가치
    if T <= 0:
        return max(S - K, 0.0) if option == "call" else max(K - S, 0.0)

    # 배당이 없으면(또는 cost-of-carry가 r에 가까우면) Call은 보통 조기행사 없음 → 유럽형과 동일
    # (엄밀히는 q==0이면 American call = European call)
    if option == "call" and q <= 1e-14:
        return bs_price(S, K, T, r, q, sigma, option="call")

    # 공통 파라미터
    b, M, N, kappa = _baw_params(T, r, q, sigma)
    q1, q2 = _baw_q1_q2(T, r, q, sigma)

    # 유럽형 가격/델타
    euro = bs_price(S, K, T, r, q, sigma, option=option)

    # --------- 임계가격 S* 찾기 ---------
    # 임계가격에서:
    # option = call : V(S*) = S* - K  and  V'(S*) = 1
    # option = put  : V(S*) = K - S*  and  V'(S*) = -1
    #
    # BAW에서는 (S/S*)^q 형태의 premium term을 붙여서 위 조건으로 S*를 푼다.

    if option == "call":
        # A2(S*) = (S*/q2) * (1 - e^{-qT} N(d1*))  (문헌 형태 중 가장 흔한 형태)
        # 여기선 smooth pasting을 이용해 f(S*)=0을 구성해 root 찾음.
        def f(S_star):
            # 유럽형 call at S_star
            C_e = bs_price(S_star, K, T, r, q, sigma, option="call")
            delta_e = bs_delta(S_star, K, T, r, q, sigma, option="call")
            # A2 from smooth pasting: A2 = (1 - delta_e) * S_star / q2
            A2 = (1.0 - delta_e) * S_star / q2
            # value matching: C_e + A2 = S_star - K
            return C_e + A2 - (S_star - K)

        # root bracket: S*는 보통 K보다 큼
        low = K
        high = K * 50.0
        # 브래킷이 안 잡히면 더 확장
        fl, fh = f(low), f(high)
        if fl * fh > 0:
            high = K * 200.0
            fh = f(high)
            if fl * fh > 0:
                # 안전장치: 그래도 안 되면 유럽형으로 fallback
                return euro

        S_star = brentq(f, low, high, maxiter=200)

        # S >= S*이면 즉시행사(내재가)
        if S >= S_star:
            return S - K

        # 아니면: American = European + A2*(S/S*)^q2
        delta_star = bs_delta(S_star, K, T, r, q, sigma, option="call")
        A2 = (1.0 - delta_star) * S_star / q2
        return euro + A2 * (S / S_star) ** q2

    else:  # put
        def f(S_star):
            P_e = bs_price(S_star, K, T, r, q, sigma, option="put")
            delta_e = bs_delta(S_star, K, T, r, q, sigma, option="put")
            # A1 from smooth pasting: A1 = (-1 - delta_e) * S_star / q1
            A1 = (-1.0 - delta_e) * S_star / q1
            # value matching: P_e + A1 = K - S_star
            return P_e + A1 - (K - S_star)

        # put의 S*는 보통 K보다 작음
        low = 1e-12
        high = K

        fl, fh = f(low), f(high)
        if fl * fh > 0:
            # 확장 시도
            low = 1e-10
            fl = f(low)
            if fl * fh > 0:
                return euro

        S_star = brentq(f, low, high, maxiter=200)

        # S <= S*이면 즉시행사(내재가)
        if S <= S_star:
            return K - S

        # 아니면: American = European + A1*(S/S*)^q1
        delta_star = bs_delta(S_star, K, T, r, q, sigma, option="put")
        A1 = (-1.0 - delta_star) * S_star / q1
        return euro + A1 * (S / S_star) ** q1


import math
import numpy as np
from scipy.stats import norm, multivariate_normal

# ============================================================
# BS2002 (Bjerksund-Stensland 2002) American option approximation
#   - Implements the 2002 paper formulas:
#     Flat boundary: Eq (4) with boundary X_T from Eq (10)-(13)
#     Two-step boundary: Proposition 1 + Eq (16)-(18)
#     Put via call-transformation: Eq (19)
# ============================================================

def _bivar_norm_cdf(a: float, b: float, rho: float) -> float:
    """Standard bivariate normal CDF M(a,b,rho)."""
    rho = max(min(rho, 0.999999999), -0.999999999)
    mean = np.array([0.0, 0.0])
    cov = np.array([[1.0, rho], [rho, 1.0]])
    return float(multivariate_normal.cdf([a, b], mean=mean, cov=cov))

def _beta(r: float, b: float, sigma: float) -> float:
    """
    Paper Eq (6):
      beta = (1/2 - b/sigma^2) + sqrt((b/sigma^2 - 1/2)^2 + 2r/sigma^2)
    """
    sig2 = sigma * sigma
    tmp = (b / sig2 - 0.5)
    return 0.5 - (b / sig2) + math.sqrt(tmp * tmp + 2.0 * r / sig2)

def _boundary_XT(K: float, T: float, r: float, b: float, sigma: float) -> float:
    """
    Paper Eq (10)-(13):
      X_T = B0 + (B1 - B0) * (1 - exp(h(T)))
      h(T) = -(bT + 2 sigma sqrt(T)) * ( K^2 / ((B1-B0)*B0) )
      B1 = beta/(beta-1) * K
      B0 = max(K, (r/(r-b))*K)  if r-b>0 else B1
    """
    if T <= 0:
        return float(K)

    beta = _beta(r, b, sigma)
    # B1 (perpetual boundary)
    B1 = (beta / (beta - 1.0)) * K

    # B0
    if (r - b) > 1e-14:
        B0 = max(K, (r / (r - b)) * K)
    else:
        B0 = B1

    # h(T)
    denom = (B1 - B0) * B0
    if denom <= 0:
        return float(B1)

    h = - (b * T + 2.0 * sigma * math.sqrt(T)) * (K * K / denom)
    X = B0 + (B1 - B0) * (1.0 - math.exp(h))
    return float(max(X, K))

def _phi(S: float, T: float, gamma: float, H: float, X: float,
         r: float, b: float, sigma: float) -> float:
    """
    Paper Eq (7)-(9):  ' (phi)
      phi(S,T | gamma, H, X)
        = exp(lambda*T) * S^gamma * [ N(d1) - (X/S)^kappa * N(d2) ]
    with
      lambda = -r + gamma*b + 0.5*gamma*(gamma-1)*sigma^2   (Eq 8)
      kappa  = 2b/sigma^2 + (2gamma - 1)                    (Eq 9)
      d1 = - [ ln(S/H) + (b + (gamma-1/2)*sigma^2)T ] / (sigma*sqrtT)
      d2 = - [ ln(X^2/(S H)) + (b + (gamma-1/2)*sigma^2)T ] / (sigma*sqrtT)
    (Requires H <= X in the barrier interpretation.)
    """
    if T <= 0:
        return 0.0
    if S <= 0 or H <= 0 or X <= 0 or sigma <= 0:
        return 0.0

    sig2 = sigma * sigma
    sqrtT = math.sqrt(T)

    lam = -r + gamma * b + 0.5 * gamma * (gamma - 1.0) * sig2
    kappa = (2.0 * b / sig2) + (2.0 * gamma - 1.0)

    d1 = - (math.log(S / H) + (b + (gamma - 0.5) * sig2) * T) / (sigma * sqrtT)
    d2 = - (math.log((X * X) / (S * H)) + (b + (gamma - 0.5) * sig2) * T) / (sigma * sqrtT)

    term = norm.cdf(d1) - ((X / S) ** kappa) * norm.cdf(d2)
    return math.exp(lam * T) * (S ** gamma) * term

def _psi(S: float, T: float, gamma: float, H: float, X: float, x: float, t: float,
         r: float, b: float, sigma: float) -> float:
    """
    Paper Proposition 1:  Ψ (denoted as ᵃ / "A" in the text)
    Eq at lines around (286)-(333) and the definitions of d1..d4, D1..D4.

      psi = exp(lambda*T) * S^gamma * [
          M(d1, D1, +sqrt(t/T))
        - (X/S)^kappa * M(d2, D2, +sqrt(t/T))
        - (x/S)^kappa * M(d3, D3, -sqrt(t/T))
        + (x/X)^kappa * M(d4, D4, -sqrt(t/T))
      ]

    where M is standard bivariate normal CDF,
      lambda = -r + gamma*b + 0.5*gamma*(gamma-1)*sigma^2
      kappa  = 2b/sigma^2 + (2gamma - 1)

    d1 = -[ ln(S/x) + (b + (gamma-1/2)sig^2)t ] / (sig*sqrt(t))
    d2 = -[ ln(X^2/(Sx)) + (b + (gamma-1/2)sig^2)t ] / (sig*sqrt(t))
    d3 = -[ ln(S/x) - (b + (gamma-1/2)sig^2)t ] / (sig*sqrt(t))
    d4 = -[ ln(X^2/(Sx)) - (b + (gamma-1/2)sig^2)t ] / (sig*sqrt(t))

    D1 = -[ ln(S/H) + (b + (gamma-1/2)sig^2)T ] / (sig*sqrt(T))
    D2 = -[ ln(X^2/(S H)) + (b + (gamma-1/2)sig^2)T ] / (sig*sqrt(T))
    D3 = -[ ln(x^2/(S H)) + (b + (gamma-1/2)sig^2)T ] / (sig*sqrt(T))
    D4 = -[ ln((S x^2)/(H X^2)) + (b + (gamma-1/2)sig^2)T ] / (sig*sqrt(T))
    """
    if T <= 0 or t <= 0:
        return 0.0
    if S <= 0 or H <= 0 or X <= 0 or x <= 0 or sigma <= 0:
        return 0.0
    if t >= T:  # avoid rho>1
        t = 0.999999999 * T

    sig2 = sigma * sigma
    sqrtt = math.sqrt(t)
    sqrtT = math.sqrt(T)

    lam = -r + gamma * b + 0.5 * gamma * (gamma - 1.0) * sig2
    kappa = (2.0 * b / sig2) + (2.0 * gamma - 1.0)

    common_t = (b + (gamma - 0.5) * sig2) * t
    common_T = (b + (gamma - 0.5) * sig2) * T

    d1 = - (math.log(S / x) + common_t) / (sigma * sqrtt)
    d2 = - (math.log((X * X) / (S * x)) + common_t) / (sigma * sqrtt)
    d3 = - (math.log(S / x) - common_t) / (sigma * sqrtt)
    d4 = - (math.log((X * X) / (S * x)) - common_t) / (sigma * sqrtt)

    D1 = - (math.log(S / H) + common_T) / (sigma * sqrtT)
    D2 = - (math.log((X * X) / (S * H)) + common_T) / (sigma * sqrtT)
    D3 = - (math.log((x * x) / (S * H)) + common_T) / (sigma * sqrtT)
    D4 = - (math.log((S * x * x) / (H * X * X)) + common_T) / (sigma * sqrtT)

    rho = math.sqrt(t / T)

    M1 = _bivar_norm_cdf(d1, D1, +rho)
    M2 = _bivar_norm_cdf(d2, D2, +rho)
    M3 = _bivar_norm_cdf(d3, D3, -rho)
    M4 = _bivar_norm_cdf(d4, D4, -rho)

    bracket = (
        M1
        - (X / S) ** kappa * M2
        - (x / S) ** kappa * M3
        + (x / X) ** kappa * M4
    )
    return math.exp(lam * T) * (S ** gamma) * bracket

def _call_flat(S: float, K: float, T: float, r: float, b: float, sigma: float) -> float:
    """Paper Eq (4) with X = X_T."""
    if T <= 0:
        return max(S - K, 0.0)
    if sigma <= 0:
        # deterministic: compare immediate vs hold (rough handling)
        return max(S - K, 0.0)

    beta = _beta(r, b, sigma)
    X = _boundary_XT(K, T, r, b, sigma)
    if S >= X:
        return S - K

    alpha = (X - K) * (X ** (-beta))  # Eq (5)

    val = (
        alpha * (S ** beta)
        - alpha * _phi(S, T, beta, X, X, r, b, sigma)
        + _phi(S, T, 1.0, X, X, r, b, sigma)
        - _phi(S, T, 1.0, K, X, r, b, sigma)
        - K * _phi(S, T, 0.0, X, X, r, b, sigma)
        + K * _phi(S, T, 0.0, K, X, r, b, sigma)
    )
    return float(val)

def _call_two_step_lower_bound(S: float, K: float, T: float, r: float, b: float, sigma: float) -> float:
    """
    Paper Proposition 1 + Eq (16)-(18).
    t = 0.5*(sqrt(5)-1)*T
    X = X_T,  x = X_{T-t}
    """
    if T <= 0:
        return max(S - K, 0.0)
    if sigma <= 0:
        return max(S - K, 0.0)

    beta = _beta(r, b, sigma)

    # Eq (16)
    t = 0.5 * (math.sqrt(5.0) - 1.0) * T
    # Eq (17)-(18)
    X = _boundary_XT(K, T, r, b, sigma)
    x = _boundary_XT(K, T - t, r, b, sigma)

    if S >= X:
        return S - K

    alphaX = (X - K) * (X ** (-beta))
    alphax = (x - K) * (x ** (-beta))

    # Proposition 1 (lines 275-282 in the PDF view)
    val = (
        alphaX * (S ** beta)
        - alphaX * _phi(S, t, beta, X, X, r, b, sigma)
        + _phi(S, t, 1.0, X, X, r, b, sigma)
        - _phi(S, t, 1.0, x, X, r, b, sigma)
        - K * _phi(S, t, 0.0, X, X, r, b, sigma)
        + K * _phi(S, t, 0.0, x, X, r, b, sigma)
        + alphax * _phi(S, t, beta, x, X, r, b, sigma)
        - alphax * _psi(S, T, beta, x, X, x, t, r, b, sigma)
        + _psi(S, T, 1.0, x, X, x, t, r, b, sigma)
        - _psi(S, T, 1.0, K, X, x, t, r, b, sigma)
        - K * _psi(S, T, 0.0, x, X, x, t, r, b, sigma)
        + K * _psi(S, T, 0.0, K, X, x, t, r, b, sigma)
    )
    return float(val)

def american_bs2002(S: float, K: float, T: float, r: float, q: float, sigma: float,
                   is_call: bool = True,
                   use_proxy: bool = True) -> float:
    """
    Public API:
      S: spot
      K: strike
      T: maturity (years)
      r: risk-free continuously compounded
      q: dividend yield continuously compounded
      sigma: volatility

    is_call: True=call, False=put
    use_proxy:
      True  -> returns proxy = 2*c_two_step - c_flat  (paper's suggested proxy)
      False -> returns two-step lower bound itself
    """
    if T <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)
    if sigma <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)

    b = r - q  # cost of carry for stock with continuous dividend yield

    # Early exercise is non-optimal for call if b >= r (i.e., q <= 0 typically),
    # but the paper's call formulas assume b < r for beta>1. We'll fall back to BS Euro call in that case.
    # (You can remove this if you strictly want the approximation regardless.)
    if is_call and b >= r - 1e-14:
        # American call ~= European call when no carry advantage for early exercise
        # (common special case: q=0 => b=r)
        return _bs_european(S, K, T, r, q, sigma, is_call=True)

    if is_call:
        c_two = _call_two_step_lower_bound(S, K, T, r, b, sigma)
        if not use_proxy:
            return c_two
        c_flat = _call_flat(S, K, T, r, b, sigma)
        return float(2.0 * c_two - c_flat)

    # Put via symmetry transform (paper Eq 19):
    # P(S,K,T,r,b,sigma) = C(K,S,T, r-b, -b, sigma)
    # Here b = r-q, so (r-b)=q
    S2 = K
    K2 = S
    r2 = r - b  # = q
    b2 = -b

    c_two = _call_two_step_lower_bound(S2, K2, T, r2, b2, sigma)
    if not use_proxy:
        return c_two
    c_flat = _call_flat(S2, K2, T, r2, b2, sigma)
    return float(2.0 * c_two - c_flat)

def _bs_european(S: float, K: float, T: float, r: float, q: float, sigma: float, is_call: bool) -> float:
    """Standard Black-Scholes European option (continuous dividend yield)."""
    if T <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)
    if sigma <= 0:
        fwd = S * math.exp((r - q) * T)
        disc = math.exp(-r * T)
        intrinsic_fwd = max(fwd - K, 0.0) if is_call else max(K - fwd, 0.0)
        return disc * intrinsic_fwd

    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    df_r = math.exp(-r * T)
    df_q = math.exp(-q * T)

    if is_call:
        return df_q * S * norm.cdf(d1) - df_r * K * norm.cdf(d2)
    else:
        return df_r * K * norm.cdf(-d2) - df_q * S * norm.cdf(-d1)


import numpy as np


def lsm_american_gbm(
    S0: float,
    K: float,
    T: float,          # years
    r: float,
    q: float,
    sigma: float,
    n_steps: int,      # time steps
    n_paths: int,      # MC paths
    callput: str = "put",
    basis_deg: int = 2,   # polynomial degree: 2면 (1,S,S^2)
    seed: int = 111,
    antithetic: bool = True,
    return_paths: bool = False
):
    """
    Longstaff-Schwartz (LSM) American option pricer under GBM.

    Returns:
      price (float)
      (optional) S_paths (n_paths, n_steps+1)
    Example:
      S, K, T = 90, 100, 0.5
      r, q, sig = 0.1, 0.1, 0.15
      lsm_american_greeks(S, K, T, r, q, sigma, callput="call",n_steps=252,n_paths=10000)

    """

    callput = callput.lower().strip()
    if callput not in ("call", "put"):
        raise ValueError("callput must be 'call' or 'put'")

    rng = np.random.default_rng(seed)
    dt = T / n_steps
    disc = np.exp(-r * dt)

    # --- 1) 경로 생성 (GBM) ---
    # d ln S = (r - q - 0.5σ^2)dt + σ sqrt(dt) Z
    mu = (r - q - 0.5 * sigma**2) * dt
    vol = sigma * np.sqrt(dt)

    if antithetic:
        half = (n_paths + 1) // 2
        Z_half = rng.standard_normal(size=(half, n_steps))
        Z = np.vstack([Z_half, -Z_half])[:n_paths, :]
    else:
        Z = rng.standard_normal(size=(n_paths, n_steps))

    ln_incr = mu + vol * Z  # (n_paths, n_steps)
    lnS = np.cumsum(ln_incr, axis=1)
    lnS = np.hstack([np.zeros((n_paths, 1)), lnS])  # t=0 포함
    S = S0 * np.exp(lnS)  # (n_paths, n_steps+1)

    # --- 2) 내재가치(payoff) ---
    if callput == "call":
        intrinsic = np.maximum(S - K, 0.0)
    else:
        intrinsic = np.maximum(K - S, 0.0)

    # --- 3) LSM: 뒤에서 앞으로 회귀하며 exercise 결정 ---
    # cashflow[t] = "t에서 exercise 했다면 받는 금액" (그 외 0)
    cashflow = intrinsic[:, -1].copy()  # 만기에는 무조건 intrinsic (미국형도 만기는 동일)

    # exercise_time: 언제 exercise 했는지 추적(디버깅/분석용)
    exercise_time = np.full(n_paths, n_steps, dtype=int)

    # t = n_steps-1 ... 1 (보통 t=0은 exercise 안한다고 가정)
    for t in range(n_steps - 1, 0, -1):
        # 지금 시점까지 디스카운트(한 스텝씩 뒤로 오면서 disc 곱해줌)
        cashflow *= disc

        # ITM(in-the-money) path만 회귀
        itm = intrinsic[:, t] > 0
        if not np.any(itm):
            continue

        X = S[itm, t]  # 상태변수(여기서는 S만 사용)
        Y = cashflow[itm]  # 계속 보유했을 때의 "할인된 미래 현금흐름"

        # --- 회귀: E[continuation | S_t] ≈ beta0 + beta1*S + beta2*S^2 + ...
        # basis: [1, X, X^2, ..., X^basis_deg]
        A = np.vstack([X**d for d in range(basis_deg + 1)]).T  # (n_itm, deg+1)
        beta, *_ = np.linalg.lstsq(A, Y, rcond=None)
        continuation = A @ beta  # (n_itm,)

        # exercise if intrinsic >= continuation
        ex_now = intrinsic[itm, t] >= continuation # 즉시 행사하는 인덱스

        # exercise한 경로는 cashflow를 intrinsic로 교체, time 업데이트
        idx_itm = np.where(itm)[0]
        ex_idx = idx_itm[ex_now]

        cashflow[ex_idx] = intrinsic[ex_idx, t]
        exercise_time[ex_idx] = t

        # exercise한 경로는 이후 시점 cashflow가 더 이상 없다고 보는 효과:
        # 이미 cashflow를 "t 시점 지급액"으로 갈아끼웠기 때문에,
        # 뒤로 더 갈 때는 disc만 적용되며 유지됨(LSM 표준 방식)

    # 마지막으로 t=0로 한 번 더 디스카운트 (t=1 -> t=0)
    price = np.mean(cashflow) * disc

    if return_paths:
        return float(price), S, exercise_time
    return float(price)


import numpy as np

# ============================================================
# 0) Z(표준정규) 고정 + LSM 가격 함수 (CRN 지원)
#    - 네 코드와 동일한 로직인데, rng 대신 Z를 입력받음
# ============================================================
def lsm_american_gbm_price_with_Z(
    S0: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    n_steps: int,
    Z: np.ndarray,          # (n_paths, n_steps) standard normal shocks
    callput: str = "put",
    basis_deg: int = 2,
):
    callput = callput.lower().strip()
    if callput not in ("call", "put"):
        raise ValueError("callput must be 'call' or 'put'")

    n_paths = Z.shape[0]
    if Z.shape[1] != n_steps:
        raise ValueError("Z must have shape (n_paths, n_steps)")

    dt = T / n_steps
    disc = np.exp(-r * dt)

    # --- 1) 경로 생성 (GBM) ---
    mu = (r - q - 0.5 * sigma**2) * dt
    vol = sigma * np.sqrt(dt)

    ln_incr = mu + vol * Z
    lnS = np.cumsum(ln_incr, axis=1)
    lnS = np.hstack([np.zeros((n_paths, 1)), lnS])  # t=0 포함
    S = S0 * np.exp(lnS)  # (n_paths, n_steps+1)

    # --- 2) 내재가치 ---
    if callput == "call":
        intrinsic = np.maximum(S - K, 0.0)
    else:
        intrinsic = np.maximum(K - S, 0.0)

    # --- 3) LSM backward ---
    cashflow = intrinsic[:, -1].copy()

    for t in range(n_steps - 1, 0, -1):
        cashflow *= disc

        itm = intrinsic[:, t] > 0
        if not np.any(itm):
            continue

        X = S[itm, t]
        Y = cashflow[itm]

        A = np.vstack([X**d for d in range(basis_deg + 1)]).T
        beta, *_ = np.linalg.lstsq(A, Y, rcond=None)
        continuation = A @ beta

        ex_now = intrinsic[itm, t] >= continuation
        idx_itm = np.where(itm)[0]
        ex_idx = idx_itm[ex_now]

        cashflow[ex_idx] = intrinsic[ex_idx, t]

    price = np.mean(cashflow) * disc
    return float(price)


# ============================================================
# 1) Z 생성기 (antithetic 옵션)
# ============================================================
def make_Z(n_paths: int, n_steps: int, seed: int = 111, antithetic: bool = True) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if antithetic:
        half = (n_paths + 1) // 2
        Z_half = rng.standard_normal(size=(half, n_steps))
        Z = np.vstack([Z_half, -Z_half])[:n_paths, :]
    else:
        Z = rng.standard_normal(size=(n_paths, n_steps))
    return Z


# ============================================================
# 2) Greeks: bump-and-revalue with CRN
# ============================================================
def lsm_american_greeks(
    S0: float,
    K: float,
    T: float,
    r: float,
    q: float,
    sigma: float,
    n_steps: int,
    n_paths: int,
    callput: str = "put",
    basis_deg: int = 2,
    seed: int = 111,
    antithetic: bool = True,
    # bump sizes
    dS: float | None = None,
    dSigma: float = 1e-2,   # 0.01 = 1%p vol
    dr: float = 1e-4,       # 1bp = 0.0001
    dT: float = 1/365,      # 1 day in years
):
    # 공통난수
    Z = make_Z(n_paths, n_steps, seed=seed, antithetic=antithetic)

    if dS is None:
        dS = 0.01 * S0  # 기본: 1% spot bump

    # base
    P0 = lsm_american_gbm_price_with_Z(
        S0, K, T, r, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )

    # Delta, Gamma (central diff)
    P_up = lsm_american_gbm_price_with_Z(
        S0 + dS, K, T, r, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    P_dn = lsm_american_gbm_price_with_Z(
        S0 - dS, K, T, r, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    delta = (P_up - P_dn) / (2.0 * dS)
    gamma = (P_up - 2.0 * P0 + P_dn) / (dS * dS)

    # Vega (central diff, per 1.00 vol)
    V_up = lsm_american_gbm_price_with_Z(
        S0, K, T, r, q, sigma + dSigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    V_dn = lsm_american_gbm_price_with_Z(
        S0, K, T, r, q, max(sigma - dSigma, 1e-8), n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    vega = (V_up - V_dn) / (2.0 * dSigma)  # per 1.00 vol
    vega_per_1pct = 0.01 * vega            # per 1%p vol

    # Rho (central diff, per 1.00 rate)
    R_up = lsm_american_gbm_price_with_Z(
        S0, K, T, r + dr, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    R_dn = lsm_american_gbm_price_with_Z(
        S0, K, T, r - dr, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    rho = (R_up - R_dn) / (2.0 * dr)       # per 1.00 rate
    rho_per_bp = 1e-4 * rho                # per 1bp

    # Theta (보통 “가격이 시간 지나면 얼마나 줄어드나”: -dP/dT)
    # 여기서는 central diff로 dP/dT를 구하고 theta = -dP/dT 로 둠.
    # (T-dT가 0 이하로 가지 않게 보호)
    T_up = T + dT
    T_dn = max(T - dT, 1e-6)

    Tprice_up = lsm_american_gbm_price_with_Z(
        S0, K, T_up, r, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    Tprice_dn = lsm_american_gbm_price_with_Z(
        S0, K, T_dn, r, q, sigma, n_steps, Z, callput=callput, basis_deg=basis_deg
    )
    dPdT = (Tprice_up - Tprice_dn) / (T_up - T_dn)
    theta = -dPdT                 # per 1 year
    theta_per_day = theta / 365.0 # per day

    return {
        "price": P0,
        "delta": delta,
        "gamma": gamma,
        "vega(1%)": vega_per_1pct,
        "rho(1bp)": rho_per_bp,
        "theta(1day)": theta_per_day,
    }

