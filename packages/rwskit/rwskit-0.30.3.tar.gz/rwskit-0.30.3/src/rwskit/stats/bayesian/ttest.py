"""An implementation of Bayesian t-tests."""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from dataclasses import dataclass
from typing import Any, Optional, Union

# 3rd Party Library
import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pymc as pm

from icontract import require
from matplotlib.axes import Axes
from numpy.typing import ArrayLike

# 1st Party Library
from rwskit.benchmarking import is_iterable

log = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel("INFO")
logging.getLogger("matplotlib").setLevel("INFO")


InferenceData = Union[az.InferenceData, pm.backends.base.MultiTrace]  # type: ignore
"""
Data generated during Bayesian inference.
"""


# region Validation Functions
def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer))


def _is_numeric_iterable(obj: Any) -> bool:
    return is_iterable(obj) and all(_is_number(x) for x in obj)


# endregion Validation Functions


@dataclass(frozen=True)
class BayesFactor:
    """
    The pair of Bayes Factors for two models :math:`M_0` and :math:`M_1`.
    Both directions are provided for convenience even though one can always be
    derived from the other.

    """

    bf_10: float
    """
    The Bayes Factor :math:`BF_{10} = \\frac{p(y | M_1)}{p(y | M_0)}`.
    """

    inference_data: Optional[InferenceData] = None
    """
    The trace of the sampling process, i.e., all the samples generated and
    used to compute the Bayes Factors.
    """

    @property
    def bf_01(self) -> float:
        """
        The Bayes Factor :math:`BF_{01} = \\frac{1}{BF_{10}} = \\frac{p(y | M_0)}{p(y | M_1)}`.
        """
        return 1.0 / self.bf_10

    def is_significant(self, significance_level: float = 10.0) -> bool:
        """Test if support for the hypothesis is significant.

        Returns ``True`` if the Bayes Factor in support of the hypothesis
        model (i.e., :math:`BF_{10}`) is greater than the specified
        ``significance_level``. See `this article <https://www.statology.org/bayes-factor/>`__
        for a table of common significance levels.

        If :data:`bf_10` is ``inf``, this function will always return ``True``.

        Parameters
        ----------
        significance_level : float, default = 10.0
            The Bayes Factor to consider evidence in favor of the hypothesis
            significant.

        Returns
        -------
        bool
            ``True`` if :data:`bf_10` is greater than the specified ``significance_level``.
        """
        if np.isinf(self.bf_10):
            return True

        return self.bf_10 > significance_level

    def plot_trace(self, combined: bool = True, show: bool = False) -> Optional[Axes]:
        """Plot the inference trace using the :data:`inference_data`.

        This method fixes the title formatting of :func:`arviz.plot_trace`.
        Without this fix, the subplot titles on the left graph overlap
        with the x-axis of the subplot just above it making them
        illegible.

        Parameters
        ----------
        combined : bool
            If ``True``, the inference chains will all be plotted using a
            single series.
        show : bool
            If ``True`` render the plot to the current device.

        Returns
        -------
        Axes
            The matplotlib axes.
        """
        if self.inference_data is None:
            log.warning("There is no inference data to use for plotting.")
            return None

        ax = az.plot_trace(self.inference_data, combined=combined)
        fig = ax[0, 0].get_figure()
        fig.subplots_adjust(hspace=0.5)

        if show:
            plt.show()

        return ax


@require(
    lambda group_1: _is_numeric_iterable(group_1),
    "'group_1' must be a sequence of numbers",
)
@require(
    lambda group_2: _is_numeric_iterable(group_2),
    "'group_2' must be a sequence of numbers",
)
@require(
    lambda beta_0_range: (
        True
        if beta_0_range is None
        else len(beta_0_range) == 2 and beta_0_range[0] < beta_0_range[1]
    ),
    "'beta_0_range[0]' must be less than 'beta_0_range[1]'",
)
@require(
    lambda cohen_d_scale: cohen_d_scale > 0, "'cohen_d_scale' must be a positive number"
)
@require(lambda sigma_scale: sigma_scale > 0, "'sigma_scale' must be a positive number")
@require(
    lambda n_posterior_samples: isinstance(n_posterior_samples, int)
    and n_posterior_samples > 0,
    "'n_posterior_samples' must be a positive integer",
)
@require(
    lambda n_prior_samples: isinstance(n_prior_samples, int) and n_prior_samples > 0,
    "'n_prior_samples' must be a positive integer",
)
@require(
    lambda random_seed: (
        isinstance(random_seed, int) if random_seed is not None else None
    ),
    "'random_seed' must be an integer",
)
def savage_dickey_t_test(
    group_1: ArrayLike,
    group_2: ArrayLike,
    beta_0_range: Optional[tuple[float, float]] = None,
    cohen_d_scale: float = 1,
    sigma_scale: float = 10,
    n_posterior_samples: int = 1000,
    n_prior_samples: int = 4000,
    random_seed: Optional[int] = None,
    return_trace: bool = False,
) -> BayesFactor:
    """Perform a Bayesian t-test on the two arrays.

    The test can be used to estimate the likelihood that the true means of two
    groups are different. The returned Bayes Factor represents the ratio between
    the probability of the null-hypothesis :math:`H_{0}`, that the means are
    equal, and the alternate hypothesis :math:`H_{1}`, the means are different.

    :math:`BF_{10} > 1` indicates support that the means are different.
    :math:`BF_{10} > 10` generally indicates strong support that the means
    are different (:math:`H_{1}` is more than 10 times as likely than
    :math:`H_{0}`). Note, :math:`BF_{10} = \\frac{1}{BF_{01}}`.

    The default priors are extremely weakly informative. In practice, this
    means more data is needed to make strong conclusions about the data. If
    more information is known about the groups it should be used to
    refine the priors.

    See the description of :ref:`model` below for the meaning of the parameters:
    ``beta_0``, ``cohen_d``, and ``sigma``.

    Parameters
    ----------
    group_1 : array-like
        The first array.
    group_2 : array_like
        The second array
    beta_0_range : tuple[float, float], optional
        The range of values for the Uniform prior on :math:`\\beta_{1}`. If
        not provided, defaults to
        ``(min(group_1 + group_2), max(group_1 + group_2))``.
    cohen_d_scale : float
        The scale to use for the ``cohen_d`` prior drawn from a Cauchy
        distribution.
    sigma_scale : float
        The scale to use for model noise drawn from a half Normal
        distribution. Using a large value will bias the model towards
        indicating the groups are the same (because the prior belief
        is most of the variability is due to random noise).
    n_posterior_samples : int, default = 1000
        The number of samples to draw from the posterior distribution.
    n_prior_samples : int, default = 4000
        The number of samples to draw from the predictive prior
        distribution.
    random_seed : int, default = None
        The random seed to use when drawing samples.
    return_trace: bool, default = False
        If ``True`` return the sampled inference data.

    Returns
    -------
    BayesFactor
        The Bayes Factors for :math:`H_{10}` and :math:`H_{01}`. When the
        groups are very different sometimes the posterior of the fit model
        does not contain the reference value for comparison (i.e., the value
        ``0``). In this case ``bf_10=np.inf`` and ``bf_01=0``. If this behavior
        is not caused by an error in the sampling process, it provides extreme
        support that the group means are different (but probably not infinite
        support).


    .. _model:

    The Model
    ---------
    The test is implemented based on the method proposed by
    `Rouder et al. (2009) <https://pubmed.ncbi.nlm.nih.gov/19293088/>`__
    and described by
    `Maarten Speekenbrink <https://mspeekenbrink.github.io/sdam-book/ch-Bayes-factors.html#a-bayesian-t-test>`__.

    The model is defined as:

    .. math::

       Y            &\\sim \\mathcal{N}(\\mu, \\sigma_{y}) \\\\
       \\sigma_{y}  &\\sim \\mathcal{N^{+}}(\\tau_{\\sigma_{y}}) \\\\
       d_{c}        &\\sim \\text{Cauchy}(0, \\tau_{d_{c}}) \\\\
       \\beta_{1}   &= d_{c} \\cdot \\sigma_{y} \\\\
       \\beta_{0}   &\\sim \\text{Uniform}(\\tau_{\\beta_{0}[0]}, \\tau_{\\beta_{0}[1]}) \\\\
       \\mu         &= \\beta_{0} \\cdot \\beta_{1} \\cdot C_{h}(X) \\\\

    :math:`\\sigma_{y}` is the random noise in the process, i.e., the
    expected standard deviation of the values from the mean du to chance.
    The prior is drawn from a half Normal distribution with scale
    :math:`\\tau_{\\sigma_{y}}`.

    :math:`X` is an indicator variable for our two groups. It is
    coded using Helmert coding, :math:`C_{h}(X)`, which compares a group
    mean to the average of the other group means. In the case of 2 groups, it
    will cause :math:`\\beta_{1}` to converge to :math:`\\mu_{1} - \\mu_{2}`
    and :math:`\\beta_{0}` to :math:`\\frac{\\mu_{1} + \\mu_{2}}{2}`.

    Because the range of values of
    :math:`\\mu_{1} - \\mu_{2}` is highly dependent data generating process, it
    is difficult to pick a prior that is likely to work well for any 2 groups
    we might encounter. The proposed method is to sample from
    `Cohen's d <https://statisticsbyjim.com/basics/cohens-d/>`__,
    :math:`d_{c} = \\frac{\\mu_1 - \\mu_{2}}{\\sigma_{y}}`, instead.
    :math:`\\beta_{1}` can be easily recovered by multiplying
    :math:`d_{c}` by :math:`\\sigma_{y}`.

    :math:`\\beta_{0}` is drawn from a Normal distribution with scale
    :math:`\\tau_{\\beta_{0}}`.

    :math:`\\mu` is the linear model using the indicator variable defined above.
    The intercept is :math:`\\beta_{0}` and the slope is :math:`\\beta_{1}`.

    :math:`Y \\sim \\mathcal{N}(\\mu, \\sigma_{y})` is the full model that
    incorporates the random noise.

    Hypothesis Testing
    ------------------

    We can use the model for hypothesis testing by setting up our two
    hypotheses as follows:

    .. math::

       H_0: \\mu_1 - \\mu_2 &=  \\beta_{1} &=       0   \\\\
       H_1: \\mu_1 - \\mu_2 &=  \\beta_{1} &\\neq   0

    Because the models for :math:`H_{0}` and :math:`H_{1}` are
    properly nested [1]_, we can use the
    `Savage-Dickey density ratio <https://statproofbook.github.io/P/bf-sddr.html>`__
    to estimate the Bayes Factor. So that:

    .. math::

       \\text{BF}_{01} = \\frac{p(\\beta_{1}=0 | D, Y)}{p(\\beta_{1}=0 | Y)}

    Where :math:`D` is our observed data and :math:`Y` is our (linear) model.
    In words this essentially says, the Bayes Factor in support of the
    null-hypothesis can be found by taking the ratio of the probability that
    :math:`\\beta_{1}` equals 0 in the posterior distribution to the
    probability that :math:`\\beta_{1}` equals 0 in the (predictive) prior
    distribution.

    .. [1] Briefly, two models are properly nested if they have the same
           parameters, but in one model, :math:`M_{1}`, they are all free
           to take on any value while in the other (at least) one of the
           parameters is fixed to a constant value.
    """
    # Create the observed values by concatenating the lists
    group_1 = np.asarray(group_1)
    group_2 = np.asarray(group_2)

    observed = np.concatenate((group_1, group_2))

    # Set up the Helmert contrast coded predictor variables.
    x = [0.5] * len(group_1) + [-0.5] * len(group_2)

    if not beta_0_range:
        # This is not entirely kosher, but seems reasonable for the task.
        # beta_1 cannot be below or above the min and max of the observed data.
        beta_0_range = (np.min(observed), np.max(observed))

    beta_0_lower, beta_0_upper = beta_0_range

    with pm.Model():
        # Depending on the data, calculating the Bayesian Factor (below) will
        # issue a warning that the reference value is outside the posterior.
        # I think this is normal, and as the warning indicates, this just means
        # the model is very sure the two groups do not have the same mean.

        # 'sigma' represents the random noise in the data.
        sigma = pm.HalfNormal("sigma", sigma=sigma_scale)

        # 'beta_0' represents the y-intercept and should converge to the mean
        # of means: (mu_1 + mu_2) / 2. 'beta_0' is drawn from a (very) weakly
        # informative prior.
        beta_0 = pm.Uniform("beta_0", lower=beta_0_lower, upper=beta_0_upper)

        # 'cohen_d' represents Cohen's d. Cohen's d is defined as
        # (mu_1 - mu_2) / sigma_y. We define the prior on Cohen's d,
        # instead of directly on (mu_1 - mu_2), because it is a normalized
        # value, which makes it invariant to the scale of the input data.
        cohen_d = pm.Cauchy("cohen_d", alpha=0, beta=cohen_d_scale)

        # 'beta_1', under the specified contrast-coded scheme, represents
        # the difference in group means (mu_1 - mu_2), and is the value we
        # are interested in comparing.
        beta_1 = pm.Deterministic("beta_1", cohen_d * sigma)  # noqa

        # The linear equation
        mu = beta_0 + beta_1 * x  # noqa

        # The final distribution
        pm.Normal("y", mu=mu, sigma=sigma, observed=observed)

        # Draw samples from the posterior
        idata = pm.sample(
            draws=n_posterior_samples, random_seed=random_seed, progressbar=False
        )

        # Draw samples from the prior (predictive) distribution.
        # The Bayes Factor (under the nested model assumptions) will be the
        # ratio of the values posterior to prior when beta_1 == 0
        idata.extend(
            pm.sample_prior_predictive(draws=n_prior_samples, random_seed=random_seed)
        )

    reference_var = "beta_1"
    reference_val = 0

    # Check to see if the reference value is outside the posterior.
    posterior = az.data.utils.extract(idata, var_names=reference_var)
    if not posterior.min() <= reference_val <= posterior.max():
        # The reference value was never sampled from the posterior
        # distribution. This usually indicates that the reference value
        # is extremely unlikely given the data. The Bayes Factor is
        # probably not actually infinity, but we don't really have a better
        # estimate. In our case it shouldn't really matter, because it
        # just means the null-hypothesis is (almost) certainly false.
        return BayesFactor(np.inf)

    bf, ax = az.plot_bf(
        idata, var_name=reference_var, ref_val=reference_val, show=False
    )
    ax.remove()

    inference_data = idata if return_trace else None
    return BayesFactor(bf["BF10"], inference_data=inference_data)  # type: ignore
