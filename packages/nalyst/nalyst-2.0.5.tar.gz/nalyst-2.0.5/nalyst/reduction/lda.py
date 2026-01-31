"""
Latent Dirichlet Allocation (LDA) for topic modeling.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.special import digamma, gammaln

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class LatentDirichletAllocation(TransformerMixin, BaseLearner):
    """
    Latent Dirichlet Allocation.

    Generative probabilistic model for discovering abstract "topics"
    in a collection of documents.

    Parameters
    ----------
    n_components : int, default=10
        Number of topics.
    doc_topic_prior : float, optional
        Prior of document topic distribution (alpha).
        If None, defaults to 1/n_components.
    topic_word_prior : float, optional
        Prior of topic word distribution (beta).
        If None, defaults to 1/n_components.
    learning_method : {"batch", "online"}, default="batch"
        Method for parameter updates.
    learning_decay : float, default=0.7
        Learning rate decay for online learning.
    learning_offset : float, default=10.0
        Downweights early iterations in online learning.
    max_iter : int, default=10
        Maximum number of iterations.
    batch_size : int, default=128
        Number of documents per mini-batch.
    evaluate_every : int, default=-1
        How often to evaluate perplexity.
    total_samples : int, default=1e6
        Total number of documents.
    perp_tol : float, default=1e-1
        Perplexity tolerance.
    mean_change_tol : float, default=1e-3
        Stopping tolerance based on mean change.
    max_doc_update_iter : int, default=100
        Max iterations for document topic distribution.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Topic word distribution (beta in literature).
    exp_dirichlet_component_ : ndarray of shape (n_components, n_features)
        Exponential of expected log topic word distribution.
    n_batch_iter_ : int
        Number of batch iterations.
    n_iter_ : int
        Number of passes over the dataset.
    bound_ : float
        Final value of variational lower bound.
    doc_topic_prior_ : float
        Actual doc-topic prior.
    topic_word_prior_ : float
        Actual topic-word prior.

    Examples
    --------
    >>> from nalyst.reduction import LatentDirichletAllocation
    >>> X = np.array([[1, 0, 2], [0, 3, 1], [2, 1, 0], [1, 2, 1]])
    >>> lda = LatentDirichletAllocation(n_components=2)
    >>> lda.train(X)
    LatentDirichletAllocation(n_components=2)
    >>> topics = lda.apply(X)
    """

    def __init__(
        self,
        n_components: int = 10,
        *,
        doc_topic_prior: Optional[float] = None,
        topic_word_prior: Optional[float] = None,
        learning_method: Literal["batch", "online"] = "batch",
        learning_decay: float = 0.7,
        learning_offset: float = 10.0,
        max_iter: int = 10,
        batch_size: int = 128,
        evaluate_every: int = -1,
        total_samples: float = 1e6,
        perp_tol: float = 1e-1,
        mean_change_tol: float = 1e-3,
        max_doc_update_iter: int = 100,
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.doc_topic_prior = doc_topic_prior
        self.topic_word_prior = topic_word_prior
        self.learning_method = learning_method
        self.learning_decay = learning_decay
        self.learning_offset = learning_offset
        self.max_iter = max_iter
        self.batch_size = batch_size
        self.evaluate_every = evaluate_every
        self.total_samples = total_samples
        self.perp_tol = perp_tol
        self.mean_change_tol = mean_change_tol
        self.max_doc_update_iter = max_doc_update_iter
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "LatentDirichletAllocation":
        """
        Learn model parameters.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Document-term matrix.
        y : ignored

        Returns
        -------
        self : LatentDirichletAllocation
            Fitted model.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Set priors
        self.doc_topic_prior_ = self.doc_topic_prior or (1.0 / self.n_components)
        self.topic_word_prior_ = self.topic_word_prior or (1.0 / self.n_components)

        # Initialize components
        self.components_ = np.random.gamma(
            100.0, 1.0 / 100.0,
            (self.n_components, n_features)
        )

        self.n_batch_iter_ = 0

        if self.learning_method == "batch":
            self._train_batch(X)
        else:
            self._train_online(X)

        # Compute final statistics
        self.exp_dirichlet_component_ = np.exp(
            digamma(self.components_) -
            digamma(self.components_.sum(axis=1, keepdims=True))
        )

        return self

    def _train_batch(self, X: np.ndarray):
        """Batch variational Bayes inference."""
        n_samples, n_features = X.shape

        for n_iter in range(self.max_iter):
            # E-step: infer document-topic distributions
            _, suff_stats = self._e_step(X)

            # M-step: update topic-word distributions
            self.components_ = self.topic_word_prior_ + suff_stats

            self.n_iter_ = n_iter + 1
            self.n_batch_iter_ += 1

    def _train_online(self, X: np.ndarray):
        """Online variational Bayes inference."""
        n_samples, n_features = X.shape

        for n_iter in range(self.max_iter):
            for start in range(0, n_samples, self.batch_size):
                end = min(start + self.batch_size, n_samples)
                X_batch = X[start:end]

                # E-step
                _, suff_stats = self._e_step(X_batch)

                # Compute learning rate
                rho = (self.learning_offset + self.n_batch_iter_) ** (-self.learning_decay)

                # M-step with learning rate
                self.components_ = (
                    (1 - rho) * self.components_ +
                    rho * (self.topic_word_prior_ +
                           n_samples / len(X_batch) * suff_stats)
                )

                self.n_batch_iter_ += 1

            self.n_iter_ = n_iter + 1

    def _e_step(self, X: np.ndarray):
        """
        E-step: infer document-topic distributions.

        Returns gamma (document-topic distributions) and sufficient statistics.
        """
        n_samples, n_features = X.shape

        # Compute expected log topic-word distribution
        Elogbeta = digamma(self.components_) - digamma(
            self.components_.sum(axis=1, keepdims=True)
        )
        expElogbeta = np.exp(Elogbeta)

        # Initialize document-topic distribution
        gamma = np.random.gamma(100.0, 1.0 / 100.0, (n_samples, self.n_components))

        # Sufficient statistics for M-step
        suff_stats = np.zeros_like(self.components_)

        for d in range(n_samples):
            # Get non-zero words
            ids = np.nonzero(X[d])[0]
            cts = X[d, ids]

            # Iterate to update gamma[d]
            gamma_d = gamma[d].copy()

            for _ in range(self.max_doc_update_iter):
                gamma_d_old = gamma_d.copy()

                Elogtheta_d = digamma(gamma_d) - digamma(gamma_d.sum())
                expElogtheta_d = np.exp(Elogtheta_d)

                # Update phi
                phinorm = np.dot(expElogtheta_d, expElogbeta[:, ids]) + 1e-100

                # Update gamma
                gamma_d = self.doc_topic_prior_ + np.dot(
                    cts / phinorm,
                    (expElogtheta_d[:, np.newaxis] * expElogbeta[:, ids]).T
                )

                # Check convergence
                if np.mean(np.abs(gamma_d - gamma_d_old)) < self.mean_change_tol:
                    break

            gamma[d] = gamma_d

            # Accumulate sufficient statistics
            Elogtheta_d = digamma(gamma_d) - digamma(gamma_d.sum())
            expElogtheta_d = np.exp(Elogtheta_d)
            phinorm = np.dot(expElogtheta_d, expElogbeta[:, ids]) + 1e-100

            suff_stats[:, ids] += (
                (expElogtheta_d[:, np.newaxis] * expElogbeta[:, ids]) *
                (cts / phinorm)
            )

        return gamma, suff_stats

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data to topic distributions.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Document-term matrix.

        Returns
        -------
        doc_topic_distr : ndarray of shape (n_samples, n_components)
            Document topic distributions.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        gamma, _ = self._e_step(X)

        # Normalize
        return gamma / gamma.sum(axis=1, keepdims=True)

    def score(self, X: np.ndarray, y=None) -> float:
        """
        Calculate approximate log-likelihood as score.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Document-term matrix.
        y : ignored

        Returns
        -------
        score : float
            Per-word approximate log-likelihood.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        doc_topic_distr = self.apply(X)

        # Compute expected log-likelihood
        beta_normalized = self.components_ / self.components_.sum(axis=1, keepdims=True)

        # E[log p(w | z, beta)]
        log_likelihood = np.sum(
            X * np.log(np.dot(doc_topic_distr, beta_normalized) + 1e-100)
        )

        # Normalize by total word count
        total_words = X.sum()

        return log_likelihood / total_words

    def perplexity(self, X: np.ndarray) -> float:
        """
        Calculate perplexity.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Document-term matrix.

        Returns
        -------
        perplexity : float
            Perplexity score.
        """
        return np.exp(-self.score(X))
