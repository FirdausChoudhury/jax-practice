# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_data_preprocessor.ipynb.

# %% ../nbs/00_data_preprocessor.ipynb 2
from __future__ import annotations
import jax
import jax.numpy as jnp
import numpy as np
jax.config.update("jax_enable_x64", True)

# %% auto 0
__all__ = ['DataPreprocessor', 'MinMaxScaler', 'OneHotEncoder', 'Feature', 'FeaturesList']

# %% ../nbs/00_data_preprocessor.ipynb 4
class DataPreprocessor:

    def fit(self, xs, y=None):
        """Fit the preprocessor with `xs` and `y`."""
        self._fit(xs, y)

    def transform(self, xs):
        """Transform `xs`."""
        self._transform(xs)

    def fit_transform(self, xs, y=None):
        """Fit the preprocessor with `xs` and `y`, then transform `xs`."""
        self.fit(xs, y)
        return self.transform(xs)

    def inverse_transform(self, xs):
        """Inverse transform `xs`."""
        self._inverse_transform(xs)

# %% ../nbs/00_data_preprocessor.ipynb 5
def _check_xs(xs: np.ndarray, name: str):
    """Check if `xs` is a 1D array with shape (n_samples,) or a 2D array with shape (n_samples, 1)."""
    if xs.ndim > 2 or (xs.ndim == 2 and xs.shape[1] != 1):
        raise ValueError(f"`{name}` only supports array with a single feature, but got shape={xs.shape}.")

# %% ../nbs/00_data_preprocessor.ipynb 6
class MinMaxScaler(DataPreprocessor):
    def fit(self, xs, y=None):
        _check_xs(xs, name="MinMaxScaler")
        self.min_ = xs.min(axis=0)
        self.max_ = xs.max(axis=0)
        return self

    def transform(self, xs):
        _check_xs(xs, name="MinMaxScaler")
        return (xs - self.min_) / ((self.max_ - self.min_)+1e-8)

    def inverse_transform(self, xs):
        if self.min_ == self.max_ == 0:
            return np.zeros(xs.shape)
        if self.min_ == self.max_ == 1:
            return np.ones(xs.shape)
        return xs * (self.max_ - self.min_) + self.min_

# %% ../nbs/00_data_preprocessor.ipynb 8
class OneHotEncoder(DataPreprocessor):
    """One-hot encoder for a single categorical feature."""
    
    def fit(self, xs, y=None):
        """Fit the OneHotEncoder with `xs`."""
        _check_xs(xs, name="OneHotEncoder")
        if(xs.dtype == object):
            categories = np.unique(xs.astype("float64"))
        else:
            categories = np.unique(xs)
        self.n_categories_ = len(categories)
        self.category_map_ = dict()
        for i, category in enumerate(categories):
            if not np.isnan(category):
                self.category_map_[int(category)] = i
            else:
                self.category_map_[str(category)] = i
        return self

    def transform(self, xs):
        """Transform `xs`."""
        _check_xs(xs, name="OneHotEncoder")
        xs = jnp.where(jnp.isnan(xs.astype("float64")), self.n_categories_ -1, xs.astype("float64"))
        return jax.nn.one_hot(xs.reshape(-1).astype("float64"), num_classes=self.n_categories_, dtype=np.float64)


    def inverse_transform(self, xs):
        """Inverse transform `xs`."""
        decoded = np.argmax(xs, axis=1)
        for i, category in enumerate(self.category_map_.keys()):
            decoded = np.where(decoded == i, category, decoded)
        return decoded.reshape(-1, 1)

# %% ../nbs/00_data_preprocessor.ipynb 10
class Feature:
    def __init__(
            self,
            name: str,
            data: np.ndarray,
            preprocessor: DataPreprocessor = None,
    ):
        self.name = name
        self.data = data
        self.preprocessor = preprocessor

    def transform(self, xs):
        if self.preprocessor is not None:
            xs = self.preprocessor.fit_transform(xs)
            if xs.ndim == 1:
                xs = xs.reshape(-1, 1)
        return xs

    def inverse_transform(self, xs):
        if self.preprocessor is not None:
            xs = self.preprocessor.inverse_transform(xs)
            if xs.ndim == 1:
                xs = xs.reshape(-1, 1)
            if xs.dtype != np.float64:
                xs = xs.astype(np.float64)
        return xs

# %% ../nbs/00_data_preprocessor.ipynb 11
class FeaturesList:
    def __init__(self, features: list[Feature]):
        self.features = features

    def transform(self, xs: np.ndarray):
        """Transform the input data using the preprocessors of the features."""
        transformed_xs = []
        for i, feature in enumerate(self.features):
            transformed_xs.append(feature.transform(xs[:, i]))
        return np.concatenate(transformed_xs, axis=-1)

    def inverse_transform(self, xs: np.ndarray):
        """Inverse transform the input data using the preprocessors of the features."""
        inv_xs = []
        i = 0
        for feature in self.features:
            if np.all(feature.data % 1 != 0):
                inv_xs.append(feature.inverse_transform(xs[:, i]))
                i += 1
            else:
                inv_xs.append(feature.inverse_transform(xs[:, i:i + feature.preprocessor.n_categories_]))
                i += feature.preprocessor.n_categories_
        return np.concatenate(inv_xs, axis=-1)
