"""
scikit-learn optimization strategy for Epochly Level 3.

CRITICAL INSIGHT (Nov 2025 mcp-reflect research):
Re-parallelizing sklearn operations provides NO benefit because:
1. sklearn already has internal parallelization via n_jobs parameter
2. Pickle/IPC overhead for models can be significant (MB to GB)
3. Benchmarks showed 0.98x (2% slower) with interception

SOLUTION: Auto-configure n_jobs=-1 instead of re-parallelizing
This leverages sklearn's native joblib-based parallelization without
adding any Epochly overhead.

Strategy:
1. Wrap estimator __init__ to auto-set n_jobs=-1
2. Don't intercept fit/predict/transform calls
3. Let sklearn handle parallelization natively
"""

from __future__ import annotations

import os
import logging
import functools
from typing import Type, Any, Optional, Set

logger = logging.getLogger(__name__)


# Set of sklearn estimators that support n_jobs
NJOBS_SUPPORTED_ESTIMATORS: Set[str] = {
    # Ensemble methods
    'RandomForestClassifier',
    'RandomForestRegressor',
    'ExtraTreesClassifier',
    'ExtraTreesRegressor',
    'GradientBoostingClassifier',
    'GradientBoostingRegressor',
    'AdaBoostClassifier',
    'AdaBoostRegressor',
    'BaggingClassifier',
    'BaggingRegressor',
    'VotingClassifier',
    'VotingRegressor',
    'StackingClassifier',
    'StackingRegressor',
    'HistGradientBoostingClassifier',
    'HistGradientBoostingRegressor',

    # Neighbors
    'KNeighborsClassifier',
    'KNeighborsRegressor',
    'RadiusNeighborsClassifier',
    'RadiusNeighborsRegressor',
    'NearestNeighbors',

    # Linear models (some)
    'LogisticRegression',
    'LogisticRegressionCV',
    'RidgeClassifierCV',
    'Perceptron',
    'SGDClassifier',
    'SGDRegressor',

    # Preprocessing
    'StandardScaler',  # n_jobs in transform

    # Model selection
    'GridSearchCV',
    'RandomizedSearchCV',
    'cross_val_score',
    'cross_validate',
    'cross_val_predict',

    # Others
    'OneVsRestClassifier',
    'OneVsOneClassifier',
    'OutputCodeClassifier',
    'MultiOutputClassifier',
    'MultiOutputRegressor',
    'ClassifierChain',
    'RegressorChain',
}


class SklearnAutoConfigurator:
    """
    Auto-configure sklearn estimators to use all CPU cores.

    Instead of intercepting sklearn operations and re-parallelizing them
    (which adds overhead), this configurator wraps estimator constructors
    to automatically set n_jobs=-1.

    This provides speedup without any Epochly overhead by leveraging
    sklearn's native joblib-based parallelization.
    """

    def __init__(self, auto_n_jobs: int = -1):
        """
        Args:
            auto_n_jobs: Value to set for n_jobs (-1 = all cores)
        """
        self.auto_n_jobs = auto_n_jobs
        self._wrapped_classes: Set[Type] = set()
        self._original_inits = {}

    def wrap_estimator_class(self, estimator_class: Type) -> Type:
        """
        Wrap an estimator class to auto-configure n_jobs.

        Args:
            estimator_class: sklearn estimator class

        Returns:
            Wrapped class with auto n_jobs configuration
        """
        if estimator_class in self._wrapped_classes:
            return estimator_class  # Already wrapped

        # Check if class supports n_jobs
        class_name = estimator_class.__name__
        if class_name not in NJOBS_SUPPORTED_ESTIMATORS:
            # Check if n_jobs is in __init__ signature
            try:
                import inspect
                sig = inspect.signature(estimator_class.__init__)
                if 'n_jobs' not in sig.parameters:
                    logger.debug(f"Skipping {class_name}: no n_jobs parameter")
                    return estimator_class
            except Exception:
                return estimator_class

        # Save original __init__
        original_init = estimator_class.__init__
        self._original_inits[estimator_class] = original_init
        auto_n_jobs = self.auto_n_jobs

        @functools.wraps(original_init)
        def wrapped_init(self, *args, **kwargs):
            # Auto-set n_jobs if not explicitly provided
            if 'n_jobs' not in kwargs:
                kwargs['n_jobs'] = auto_n_jobs
                logger.debug(f"Auto-configured {class_name} with n_jobs={auto_n_jobs}")
            return original_init(self, *args, **kwargs)

        # Replace __init__
        estimator_class.__init__ = wrapped_init
        self._wrapped_classes.add(estimator_class)

        logger.info(f"Wrapped {class_name} for auto n_jobs={auto_n_jobs}")
        return estimator_class

    def wrap_sklearn_module(self):
        """
        Wrap all sklearn estimators that support n_jobs.

        Call this after sklearn is imported to auto-configure
        parallelization for all supported estimators.
        """
        try:
            import sklearn
        except ImportError:
            logger.warning("sklearn not installed, skipping auto-configuration")
            return

        wrapped_count = 0

        # Wrap ensemble estimators
        try:
            from sklearn import ensemble
            for name in dir(ensemble):
                if name in NJOBS_SUPPORTED_ESTIMATORS:
                    estimator_class = getattr(ensemble, name)
                    if isinstance(estimator_class, type):
                        self.wrap_estimator_class(estimator_class)
                        wrapped_count += 1
        except Exception as e:
            logger.debug(f"Error wrapping ensemble: {e}")

        # Wrap neighbors estimators
        try:
            from sklearn import neighbors
            for name in dir(neighbors):
                if name in NJOBS_SUPPORTED_ESTIMATORS:
                    estimator_class = getattr(neighbors, name)
                    if isinstance(estimator_class, type):
                        self.wrap_estimator_class(estimator_class)
                        wrapped_count += 1
        except Exception as e:
            logger.debug(f"Error wrapping neighbors: {e}")

        # Wrap linear_model estimators
        try:
            from sklearn import linear_model
            for name in dir(linear_model):
                if name in NJOBS_SUPPORTED_ESTIMATORS:
                    estimator_class = getattr(linear_model, name)
                    if isinstance(estimator_class, type):
                        self.wrap_estimator_class(estimator_class)
                        wrapped_count += 1
        except Exception as e:
            logger.debug(f"Error wrapping linear_model: {e}")

        # Wrap model_selection
        try:
            from sklearn import model_selection
            for name in ['GridSearchCV', 'RandomizedSearchCV']:
                if hasattr(model_selection, name):
                    estimator_class = getattr(model_selection, name)
                    if isinstance(estimator_class, type):
                        self.wrap_estimator_class(estimator_class)
                        wrapped_count += 1
        except Exception as e:
            logger.debug(f"Error wrapping model_selection: {e}")

        # Wrap multioutput estimators
        try:
            from sklearn import multioutput
            for name in dir(multioutput):
                if name in NJOBS_SUPPORTED_ESTIMATORS:
                    estimator_class = getattr(multioutput, name)
                    if isinstance(estimator_class, type):
                        self.wrap_estimator_class(estimator_class)
                        wrapped_count += 1
        except Exception as e:
            logger.debug(f"Error wrapping multioutput: {e}")

        logger.info(f"Auto-configured {wrapped_count} sklearn estimators with n_jobs={self.auto_n_jobs}")

    def unwrap_all(self):
        """
        Restore original __init__ methods.

        Call this to disable auto-configuration.
        """
        for estimator_class, original_init in self._original_inits.items():
            estimator_class.__init__ = original_init

        self._wrapped_classes.clear()
        self._original_inits.clear()
        logger.info("Restored original sklearn __init__ methods")


# Global configurator instance
_global_configurator: Optional[SklearnAutoConfigurator] = None


def get_sklearn_configurator() -> SklearnAutoConfigurator:
    """Get the global sklearn configurator."""
    global _global_configurator
    if _global_configurator is None:
        _global_configurator = SklearnAutoConfigurator()
    return _global_configurator


def auto_configure_sklearn():
    """
    Auto-configure all sklearn estimators to use all CPU cores.

    This is the recommended way to optimize sklearn with Epochly.
    Instead of intercepting operations, we configure sklearn to
    use its native parallelization.

    Example:
        >>> from epochly.interception.frameworks import auto_configure_sklearn
        >>> auto_configure_sklearn()
        >>> # Now all sklearn estimators automatically use n_jobs=-1
        >>> from sklearn.ensemble import RandomForestClassifier
        >>> rf = RandomForestClassifier()  # n_jobs=-1 automatically set
    """
    configurator = get_sklearn_configurator()
    configurator.wrap_sklearn_module()
