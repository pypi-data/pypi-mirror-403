"""Proportions: Bayesian inference for binomial proportions.

This package provides Bayesian and frequentist inference methods for
binomial proportions, including hierarchical models and model comparison.

Quick Start - Single Proportion Inference:
    >>> from proportions import conf_interval_proportion
    >>> ci = conf_interval_proportion(30, 100, confidence=0.95)
    >>> print(ci)
    [0.219, 0.396]

Quick Start - Grouped Data (Hierarchical Bayes):
    >>> import numpy as np
    >>> from proportions import BinomialData, hierarchical_bayes
    >>> data = BinomialData(x=np.array([8, 7, 9]), n=np.array([10, 10, 10]))
    >>> result = hierarchical_bayes(data, n_samples=5000)
    >>> print(f"Mean: {result.posterior.mu:.3f}")
    Mean: 0.800
"""

# Core data models
from proportions.core.models import BinomialData, PosteriorResult

# Grouped data inference
from proportions.inference import (
    hierarchical_bayes,
    empirical_bayes,
    single_theta_bayesian,
    uncoupled_thetas,
    clopper_pearson,
    fisher_test,
)

# Single proportion inference
from proportions.inference import (
    conf_interval_proportion,
    upper_bound_proportion,
    lower_bound_proportion,
    prob_larger_than_threshold,
    prob_smaller_than_threshold,
    prob_of_interval,
)

# Conditional inference
from proportions.inference import conditional_inference_k_out_of_k

# Model comparison
from proportions.diagnostics import (
    compare_models,
    compute_single_theta_evidence,
    compute_uncoupled_thetas_evidence,
)

__version__ = "0.3.5"

__all__ = [
    # Core models
    "BinomialData",
    "PosteriorResult",
    # Grouped data inference
    "hierarchical_bayes",
    "empirical_bayes",
    "single_theta_bayesian",
    "uncoupled_thetas",
    "clopper_pearson",
    "fisher_test",
    # Single proportion inference
    "conf_interval_proportion",
    "upper_bound_proportion",
    "lower_bound_proportion",
    "prob_larger_than_threshold",
    "prob_smaller_than_threshold",
    "prob_of_interval",
    # Conditional inference
    "conditional_inference_k_out_of_k",
    # Model comparison
    "compare_models",
    "compute_single_theta_evidence",
    "compute_uncoupled_thetas_evidence",
]
