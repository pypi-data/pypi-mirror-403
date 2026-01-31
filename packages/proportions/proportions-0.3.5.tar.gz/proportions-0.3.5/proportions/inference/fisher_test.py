"""
Fisher's Exact Test for Two Proportions

Classical frequentist test for comparing two binomial proportions.
Tests the null hypothesis that the odds ratio equals 1 (equal proportions).
"""

import numpy as np
from scipy.stats import fisher_exact
from scipy.stats.contingency import odds_ratio as odds_ratio_ci

from proportions.core.models import BinomialData, FisherTestResult


def fisher_test(
    x,
    n,
    ci_level: float = 0.95,
    alternative: str = "two-sided"
) -> FisherTestResult:
    """
    Fisher's exact test for comparing two proportions.

    Tests whether two binomial proportions differ significantly using
    Fisher's exact test. Computes p-value and confidence interval for
    the odds ratio.

    Parameters
    ----------
    x : array-like of length 2
        Success counts [x1, x2] for groups 1 and 2
    n : array-like of length 2
        Trial counts [n1, n2] for groups 1 and 2
    ci_level : float, default=0.95
        Confidence level for odds ratio CI
    alternative : str, default="two-sided"
        Defines the alternative hypothesis:
        - "two-sided": proportions are different (H1: OR ≠ 1)
        - "greater": proportion 1 > proportion 2 (H1: OR > 1)
        - "less": proportion 1 < proportion 2 (H1: OR < 1)

    Returns
    -------
    FisherTestResult
        Contains p_value, odds_ratio, CI bounds, and data summary

    Examples
    --------
    >>> from proportions import fisher_test
    >>> # Compare 8/10 vs 2/10
    >>> result = fisher_test([8, 2], [10, 10])
    >>> print(f"p-value: {result.p_value:.4f}")
    p-value: 0.0230
    >>> print(f"Odds Ratio: {result.odds_ratio:.2f}")
    Odds Ratio: 16.00
    >>> print(f"95% CI: [{result.ci_lower:.2f}, {result.ci_upper:.2f}]")
    95% CI: [1.21, 148.07]

    >>> # One-sided test: Group 1 > Group 2
    >>> result_greater = fisher_test([8, 2], [10, 10], alternative="greater")
    >>> print(f"p-value (one-sided): {result_greater.p_value:.4f}")
    p-value (one-sided): 0.0115

    Notes
    -----
    - Uses scipy.stats.fisher_exact for computation
    - Exact test (not asymptotic) - valid for small samples
    - For large samples, consider Chi-square test for computational efficiency
    - Odds ratio is the ratio of odds: (x1/(n1-x1)) / (x2/(n2-x2))
    - When any cell count is 0, odds ratio is inf or 0; CI bounds may be extreme
    - The test assumes independent samples from two binomial distributions
    - No continuity correction needed (this is an exact test)

    References
    ----------
    Fisher, R.A. (1922). "On the interpretation of χ² from contingency tables,
    and the calculation of P". Journal of the Royal Statistical Society, 85(1), 87-94.
    """
    # Convert to numpy arrays
    x = np.asarray(x)
    n = np.asarray(n)

    # Create BinomialData for validation
    data = BinomialData(x=x, n=n)

    # Validate input
    if data.n_groups != 2:
        raise ValueError(
            f"Fisher's exact test requires exactly 2 groups, got {data.n_groups}"
        )

    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(
            f"alternative must be 'two-sided', 'greater', or 'less', "
            f"got '{alternative}'"
        )

    if not (0.0 < ci_level < 1.0):
        raise ValueError(f"ci_level must be in (0, 1), got {ci_level}")

    # Extract data
    x1, x2 = int(data.x[0]), int(data.x[1])
    n1, n2 = int(data.n[0]), int(data.n[1])

    # Construct 2x2 contingency table
    # Row 1: Group 1 (success, failure)
    # Row 2: Group 2 (success, failure)
    table = np.array([
        [x1, n1 - x1],
        [x2, n2 - x2]
    ])

    # Compute Fisher's exact test
    odds_ratio, p_value = fisher_exact(table, alternative=alternative)

    # Compute confidence interval for odds ratio
    # scipy.stats.contingency.odds_ratio provides CI
    res = odds_ratio_ci(table)
    ci = res.confidence_interval(confidence_level=ci_level)

    return FisherTestResult(
        p_value=p_value,
        alternative=alternative,
        odds_ratio=odds_ratio,
        ci_level=ci_level,
        ci_lower=ci.low,
        ci_upper=ci.high,
        n_group1=n1,
        n_group2=n2,
        x_group1=x1,
        x_group2=x2,
        rate_group1=data.observed_rates[0],
        rate_group2=data.observed_rates[1]
    )
