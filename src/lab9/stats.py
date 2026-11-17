"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def _norm(labels: Sequence[str]) -> list[str]:
    return [str(x).strip().upper() for x in labels]


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    h, j = _norm(human), _norm(judge)
    if len(h) != len(j):
        raise ValueError(f"paired labels differ in length: {len(h)} vs {len(j)}")
    cm = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for a, b in zip(h, j):
        if b == POS:
            cm["tp" if a == POS else "fp"] += 1
        else:
            cm["fn" if a == POS else "tn"] += 1
    return cm


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    # precision = tp/(tp+fp), recall = tp/(tp+fn); 0.0 when the denominator is 0
    cm = confusion(human, judge)
    precision = cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else 0.0
    recall = cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    h, j = _norm(human), _norm(judge)
    if len(h) != len(j) or not h:
        raise ValueError("kappa needs paired, non-empty labels")
    n = len(h)
    p_o = sum(a == b for a, b in zip(h, j)) / n
    classes = set(h) | set(j)
    p_e = sum((h.count(c) / n) * (j.count(c) / n) for c in classes)
    if p_e >= 1.0 - 1e-12:      # degenerate: both sides constant
        raise ValueError("kappa undefined: chance agreement p_e == 1")
    return (p_o - p_e) / (1.0 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    # (p_obs + spec - 1) / (sens + spec - 1)
    denom = sensitivity + specificity - 1.0
    if denom <= 0:
        raise ValueError("Rogan-Gladen undefined: sensitivity + specificity <= 1")
    return min(1.0, max(0.0, (observed_rate + specificity - 1.0) / denom))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    x = np.asarray(list(a), dtype=float)
    y = np.asarray(list(b), dtype=float)
    if x.shape != y.shape or x.size == 0:
        raise ValueError("paired_bootstrap needs two non-empty, equal-length sequences")
    if np.array_equal(x, y):
        return (0.0, 0.0, 0.0)
    res = bootstrap((x, y), statistic=lambda p, q: np.mean(p) - np.mean(q), paired=True,
                    n_resamples=n_resamples, method="percentile", confidence_level=confidence,
                    rng=np.random.default_rng(rng))
    return (float(np.mean(x) - np.mean(y)), float(res.confidence_interval.low),
            float(res.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    raise NotImplementedError


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    raise NotImplementedError
