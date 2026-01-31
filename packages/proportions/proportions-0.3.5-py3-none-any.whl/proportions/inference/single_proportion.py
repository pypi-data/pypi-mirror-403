"""Single proportion Bayesian inference with truncated Beta priors.

This module implements Bayesian inference for a single binomial proportion
with support for truncated Beta priors. These functions are useful when you have
a single (success, counts) pair rather than grouped data.

The standard Beta-Binomial conjugate model is:
    θ ~ Beta(α, β)           # Prior (optionally truncated to [lower, upper])
    x ~ Binomial(n, θ)       # Likelihood
    θ | x ~ Beta(α + x, β + n - x)  # Posterior (truncated)

When lower=0.0 and upper=1.0 (default), this reduces to the standard Beta-Binomial model.

For grouped data (array inputs), automatically uses Hierarchical Bayes to compute
inference on the population mean μ.
"""

import numpy as np

from proportions.distributions.truncated_beta import (
    truncated_beta_cdf,
    truncated_beta_ppf,
)
from proportions.core.models import BinomialData
from proportions.inference.hierarchical_bayes import hierarchical_bayes


def _validate_inputs(
    success: int,
    counts: int,
    prior_alpha: float,
    prior_beta: float,
    lower: float,
    upper: float,
    confidence: float | None = None,
) -> None:
    """Validate common input parameters.

    Args:
        success: Number of successes.
        counts: Total number of trials.
        prior_alpha: Prior alpha parameter.
        prior_beta: Prior beta parameter.
        lower: Lower truncation bound.
        upper: Upper truncation bound.
        confidence: Optional confidence level.

    Raises:
        ValueError: If any parameter is invalid.
    """
    if success < 0:
        raise ValueError(f"success must be non-negative, got {success}")
    if counts < 0:
        raise ValueError(f"counts must be non-negative, got {counts}")
    if success > counts:
        raise ValueError(f"success ({success}) cannot exceed counts ({counts})")

    if prior_alpha <= 0:
        raise ValueError(f"prior_alpha must be positive, got {prior_alpha}")
    if prior_beta <= 0:
        raise ValueError(f"prior_beta must be positive, got {prior_beta}")

    if not (0.0 <= lower < upper <= 1.0):
        raise ValueError(
            f"Must have 0 <= lower < upper <= 1, got lower={lower}, upper={upper}"
        )

    if confidence is not None:
        if not (0.0 < confidence < 1.0):
            raise ValueError(f"confidence must be in (0, 1), got {confidence}")


def _is_single_proportion(success, trials):
    """Check if inputs represent a single proportion or grouped data.

    Args:
        success: Scalar or array-like of success counts.
        trials: Scalar or array-like of trial counts.

    Returns:
        True if inputs represent a single proportion, False for grouped data.

    Raises:
        ValueError: If one input is scalar and the other is array-like.
    """
    success_scalar = np.isscalar(success)
    trials_scalar = np.isscalar(trials)

    if success_scalar and trials_scalar:
        return True
    elif success_scalar or trials_scalar:
        raise ValueError(
            "success and trials must both be scalars or both be array-like"
        )
    else:
        # Both are array-like
        success_arr = np.asarray(success)
        trials_arr = np.asarray(trials)

        if success_arr.ndim != 1 or trials_arr.ndim != 1:
            raise ValueError("success and trials arrays must be 1-dimensional")

        if len(success_arr) != len(trials_arr):
            raise ValueError(
                f"success and trials arrays must have same length, "
                f"got {len(success_arr)} and {len(trials_arr)}"
            )

        # Single element arrays → treat as single proportion
        if len(success_arr) == 1:
            return True

        return False


def _conf_interval_hierarchical(successes, trials, confidence, n_samples):
    """Compute confidence interval for population mean μ using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        confidence: Confidence level between 0 and 1.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Array [lower_bound, upper_bound] for population mean μ.
    """
    # Convert to BinomialData
    data = BinomialData(x=np.array(successes), n=np.array(trials))

    # Call hierarchical_bayes with default hyperprior parameters
    # Note: ci_level in hierarchical_bayes corresponds to our confidence parameter
    result = hierarchical_bayes(data, n_samples=n_samples, ci_level=confidence)

    # Extract CI from result (already computed at requested confidence level)
    return np.array([result.posterior.ci_lower, result.posterior.ci_upper])


def _upper_bound_hierarchical(successes, trials, confidence, n_samples):
    """Compute upper bound for population mean μ using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        confidence: Confidence level between 0 and 1.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Upper bound such that P(μ ≤ bound | data) = confidence.
    """
    data = BinomialData(x=np.array(successes), n=np.array(trials))
    result = hierarchical_bayes(data, n_samples=n_samples)

    # Use fitted Beta parameters for μ posterior (standard Beta: lower=0, upper=1)
    return float(truncated_beta_ppf(confidence,
                                    result.posterior.alpha_fitted,
                                    result.posterior.beta_fitted,
                                    lower=0.0, upper=1.0))


def _lower_bound_hierarchical(successes, trials, confidence, n_samples):
    """Compute lower bound for population mean μ using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        confidence: Confidence level between 0 and 1.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Lower bound such that P(μ ≥ bound | data) = confidence.
    """
    data = BinomialData(x=np.array(successes), n=np.array(trials))
    result = hierarchical_bayes(data, n_samples=n_samples)

    # Use fitted Beta parameters for μ posterior (standard Beta: lower=0, upper=1)
    return float(truncated_beta_ppf(1 - confidence,
                                    result.posterior.alpha_fitted,
                                    result.posterior.beta_fitted,
                                    lower=0.0, upper=1.0))


def _prob_larger_hierarchical(successes, trials, threshold, n_samples):
    """Compute P(μ > threshold) using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        threshold: Threshold value.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Probability that μ > threshold.
    """
    data = BinomialData(x=np.array(successes), n=np.array(trials))
    result = hierarchical_bayes(data, n_samples=n_samples)

    # Use fitted Beta parameters for μ posterior (standard Beta: lower=0, upper=1)
    return float(1 - truncated_beta_cdf(threshold,
                                        result.posterior.alpha_fitted,
                                        result.posterior.beta_fitted,
                                        lower=0.0, upper=1.0))


def _prob_smaller_hierarchical(successes, trials, threshold, n_samples):
    """Compute P(μ < threshold) using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        threshold: Threshold value.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Probability that μ < threshold.
    """
    data = BinomialData(x=np.array(successes), n=np.array(trials))
    result = hierarchical_bayes(data, n_samples=n_samples)

    # Use fitted Beta parameters for μ posterior (standard Beta: lower=0, upper=1)
    return float(truncated_beta_cdf(threshold,
                                    result.posterior.alpha_fitted,
                                    result.posterior.beta_fitted,
                                    lower=0.0, upper=1.0))


def _prob_interval_hierarchical(successes, trials, lb, ub, n_samples):
    """Compute P(lb < μ < ub) using Hierarchical Bayes.

    Args:
        successes: Array-like of success counts.
        trials: Array-like of trial counts.
        lb: Lower bound of interval.
        ub: Upper bound of interval.
        n_samples: Number of importance samples for hierarchical inference.

    Returns:
        Probability that μ is in [lb, ub].
    """
    data = BinomialData(x=np.array(successes), n=np.array(trials))
    result = hierarchical_bayes(data, n_samples=n_samples)

    # Use fitted Beta parameters for μ posterior (standard Beta: lower=0, upper=1)
    cdf_lb = truncated_beta_cdf(lb,
                                result.posterior.alpha_fitted,
                                result.posterior.beta_fitted,
                                lower=0.0, upper=1.0)
    cdf_ub = truncated_beta_cdf(ub,
                                result.posterior.alpha_fitted,
                                result.posterior.beta_fitted,
                                lower=0.0, upper=1.0)
    return float(cdf_ub - cdf_lb)


def conf_interval_proportion(
    success,
    counts,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> np.ndarray:
    """Compute equal-tails credible interval for a binomial proportion.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Uses Beta-Binomial conjugate updating
      with optional truncation.
    - **Grouped data** (array inputs): Uses Hierarchical Bayes to compute
      credible interval for population mean μ. In this mode, prior_alpha,
      prior_beta, lower, and upper are ignored (uses HB default hyperpriors).

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        confidence: Credible interval level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Array [lower_bound, upper_bound] of the credible interval.

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> interval = conf_interval_proportion(30, 100, confidence=0.95)
        >>> interval[0] < 0.3 < interval[1]  # Should contain point estimate
        True

        >>> # Grouped data: multiple scenarios
        >>> import numpy as np
        >>> interval = conf_interval_proportion(
        ...     [30, 25, 35], [100, 100, 100], confidence=0.95
        ... )
        >>> # Returns CI for population mean μ ≈ 0.3

        >>> # With truncated prior (single proportion only)
        >>> interval_trunc = conf_interval_proportion(30, 100, lower=0.2, upper=0.8)
        >>> 0.2 <= interval_trunc[0] < interval_trunc[1] <= 0.8
        True
    """
    # Dispatch based on input type
    if _is_single_proportion(success, counts):
        # Single proportion mode - existing implementation
        # Extract scalar from single-element arrays if needed
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

        # Posterior parameters (Beta-Binomial conjugate update)
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        # Compute equal-tails credible interval
        alpha_level = (1 - confidence) / 2.0
        lower_bound = truncated_beta_ppf(alpha_level, alpha_post, beta_post, lower, upper)
        upper_bound = truncated_beta_ppf(1 - alpha_level, alpha_post, beta_post, lower, upper)

        return np.array([lower_bound, upper_bound])
    else:
        # Grouped data mode - use Hierarchical Bayes
        return _conf_interval_hierarchical(success, counts, confidence, n_samples)


def upper_bound_proportion(
    success,
    counts,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> float:
    """Compute upper credible bound for a binomial proportion.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Uses Beta-Binomial conjugate updating.
    - **Grouped data** (array inputs): Uses Hierarchical Bayes to compute
      upper bound for population mean μ. In this mode, prior_alpha, prior_beta,
      lower, and upper are ignored.

    The upper bound u satisfies P(θ ≤ u | data) = confidence (single proportion)
    or P(μ ≤ u | data) = confidence (grouped data).

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        confidence: Confidence level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Upper credible bound.

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> ub = upper_bound_proportion(30, 100, confidence=0.95)
        >>> ub > 0.3  # Should be above point estimate
        True

        >>> # Grouped data: multiple scenarios
        >>> ub_grouped = upper_bound_proportion([30, 25, 35], [100, 100, 100])
        >>> # Returns upper bound for population mean μ
    """
    if _is_single_proportion(success, counts):
        # Single proportion mode
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

        # Posterior parameters
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        return float(truncated_beta_ppf(confidence, alpha_post, beta_post, lower, upper))
    else:
        # Grouped data mode
        return _upper_bound_hierarchical(success, counts, confidence, n_samples)


def lower_bound_proportion(
    success,
    counts,
    confidence: float = 0.95,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> float:
    """Compute lower credible bound for a binomial proportion.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Uses Beta-Binomial conjugate updating.
    - **Grouped data** (array inputs): Uses Hierarchical Bayes to compute
      lower bound for population mean μ. In this mode, prior_alpha, prior_beta,
      lower, and upper are ignored.

    The lower bound l satisfies P(θ ≥ l | data) = confidence (single proportion)
    or P(μ ≥ l | data) = confidence (grouped data).

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        confidence: Confidence level between 0 and 1 (default: 0.95).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Lower credible bound.

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> lb = lower_bound_proportion(30, 100, confidence=0.95)
        >>> lb < 0.3  # Should be below point estimate
        True

        >>> # Grouped data: multiple scenarios
        >>> lb_grouped = lower_bound_proportion([30, 25, 35], [100, 100, 100])
        >>> # Returns lower bound for population mean μ
    """
    if _is_single_proportion(success, counts):
        # Single proportion mode
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper, confidence)

        # Posterior parameters
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        # Lower bound at confidence level means we want the (1-confidence) quantile
        return float(truncated_beta_ppf(1 - confidence, alpha_post, beta_post, lower, upper))
    else:
        # Grouped data mode
        return _lower_bound_hierarchical(success, counts, confidence, n_samples)


def prob_larger_than_threshold(
    success,
    counts,
    threshold: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> float:
    """Compute probability that proportion is larger than a threshold.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Computes P(θ > threshold | data).
    - **Grouped data** (array inputs): Computes P(μ > threshold | data) where
      μ is the population mean. In this mode, prior_alpha, prior_beta, lower,
      and upper are ignored.

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        threshold: Threshold value between 0 and 1.
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Probability that proportion (or population mean) > threshold.

    Raises:
        ValueError: If threshold is not in [0, 1].

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> prob = prob_larger_than_threshold(30, 100, threshold=0.25)
        >>> prob > 0.5  # Should be fairly high
        True

        >>> # Grouped data: multiple scenarios
        >>> prob_grouped = prob_larger_than_threshold(
        ...     [30, 25, 35], [100, 100, 100], threshold=0.25
        ... )
        >>> # Returns P(μ > 0.25 | data)
    """
    if _is_single_proportion(success, counts):
        # Single proportion mode
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")

        # Posterior parameters
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        # P(θ > threshold) = 1 - P(θ ≤ threshold) = 1 - CDF(threshold)
        cdf_val = truncated_beta_cdf(threshold, alpha_post, beta_post, lower, upper)
        return float(1.0 - cdf_val)
    else:
        # Grouped data mode
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")
        return _prob_larger_hierarchical(success, counts, threshold, n_samples)


def prob_smaller_than_threshold(
    success,
    counts,
    threshold: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> float:
    """Compute probability that proportion is smaller than a threshold.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Computes P(θ < threshold | data).
    - **Grouped data** (array inputs): Computes P(μ < threshold | data) where
      μ is the population mean. In this mode, prior_alpha, prior_beta, lower,
      and upper are ignored.

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        threshold: Threshold value between 0 and 1.
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Probability that proportion (or population mean) < threshold.

    Raises:
        ValueError: If threshold is not in [0, 1].

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> prob = prob_smaller_than_threshold(30, 100, threshold=0.35)
        >>> prob > 0.5  # Should be fairly high
        True

        >>> # Grouped data: multiple scenarios
        >>> prob_grouped = prob_smaller_than_threshold(
        ...     [30, 25, 35], [100, 100, 100], threshold=0.35
        ... )
        >>> # Returns P(μ < 0.35 | data)
    """
    if _is_single_proportion(success, counts):
        # Single proportion mode
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")

        # Posterior parameters
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        # P(θ < threshold) = CDF(threshold)
        return float(truncated_beta_cdf(threshold, alpha_post, beta_post, lower, upper))
    else:
        # Grouped data mode
        if not (0.0 <= threshold <= 1.0):
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")
        return _prob_smaller_hierarchical(success, counts, threshold, n_samples)


def prob_of_interval(
    success,
    counts,
    lb: float,
    ub: float,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    lower: float = 0.0,
    upper: float = 1.0,
    n_samples: int = 5000,
) -> float:
    """Compute probability that proportion falls within an interval.

    Supports both single proportion and grouped data:
    - **Single proportion** (scalar inputs): Computes P(lb < θ < ub | data).
    - **Grouped data** (array inputs): Computes P(lb < μ < ub | data) where
      μ is the population mean. In this mode, prior_alpha, prior_beta, lower,
      and upper are ignored.

    Args:
        success: Number of successes (int) or array of success counts.
        counts: Total number of trials (int) or array of trial counts.
        lb: Lower bound of query interval (must be in [0, 1]).
        ub: Upper bound of query interval (must be in [0, 1] and >= lb).
        prior_alpha: Alpha parameter of Beta prior (default: 1.0 = uniform).
                    Only used for single proportion mode.
        prior_beta: Beta parameter of Beta prior (default: 1.0 = uniform).
                   Only used for single proportion mode.
        lower: Lower bound of prior truncation (default: 0.0).
              Only used for single proportion mode.
        upper: Upper bound of prior truncation (default: 1.0).
              Only used for single proportion mode.
        n_samples: Number of importance samples for hierarchical inference
                  (default: 5000). Only used for grouped data mode.

    Returns:
        Probability that θ ∈ [lb, ub] (single proportion) or μ ∈ [lb, ub] (grouped data).

    Raises:
        ValueError: If lb or ub are invalid or lb > ub.

    Examples:
        >>> # Single proportion: 30 successes out of 100 trials
        >>> # What's the probability that true rate is in [0.25, 0.35]?
        >>> prob = prob_of_interval(30, 100, lb=0.25, ub=0.35)
        >>> 0.0 < prob < 1.0
        True

        >>> # Grouped data: multiple scenarios
        >>> prob_grouped = prob_of_interval(
        ...     [30, 25, 35], [100, 100, 100], lb=0.25, ub=0.35
        ... )
        >>> # Returns P(0.25 < μ < 0.35 | data)
    """
    if _is_single_proportion(success, counts):
        # Single proportion mode
        if not np.isscalar(success):
            success = np.asarray(success).item()
            counts = np.asarray(counts).item()

        _validate_inputs(success, counts, prior_alpha, prior_beta, lower, upper)

        if not (0.0 <= lb <= 1.0):
            raise ValueError(f"lb must be in [0, 1], got {lb}")
        if not (0.0 <= ub <= 1.0):
            raise ValueError(f"ub must be in [0, 1], got {ub}")
        if lb > ub:
            raise ValueError(f"lb ({lb}) must be <= ub ({ub})")

        # Posterior parameters
        alpha_post = success + prior_alpha
        beta_post = counts - success + prior_beta

        # P(lb ≤ θ ≤ ub) = CDF(ub) - CDF(lb)
        cdf_lb = truncated_beta_cdf(lb, alpha_post, beta_post, lower, upper)
        cdf_ub = truncated_beta_cdf(ub, alpha_post, beta_post, lower, upper)

        return float(cdf_ub - cdf_lb)
    else:
        # Grouped data mode
        if not (0.0 <= lb <= 1.0):
            raise ValueError(f"lb must be in [0, 1], got {lb}")
        if not (0.0 <= ub <= 1.0):
            raise ValueError(f"ub must be in [0, 1], got {ub}")
        if lb > ub:
            raise ValueError(f"lb ({lb}) must be <= ub ({ub})")
        return _prob_interval_hierarchical(success, counts, lb, ub, n_samples)
