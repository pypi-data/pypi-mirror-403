import numpy as np

class MyIQROutlierHandler:
    def __init__(
        self,
        strategy:str = 'clip',
        factor: float = 1.5,
        auto: bool = False,
        threshold: float = 0.01,
        cols = None,
        ) -> None:
    
        self.strategy = strategy
        self.factor = factor
        self.auto = auto
        self.cols = cols
        self.threshold = threshold
        
        self.bounds_ = {}
        self.active_cols_ = []
        
    def _compute_bounds(self, X_col):
        Q1  = np.percentile(X_col, 25)
        Q3 = np.percentile(X_col, 75)
        
        IQR = Q3 - Q1
        
        lower = Q1 - self.factor * IQR
        upper = Q3 +  self.factor * IQR
        
        return lower, upper
    
    def _has_outliers(self, X_col, lower, upper):
        outliers = (X_col < lower) | (X_col > upper)
        ratio = np.sum(outliers) / len(X_col)
        return ratio >= self.threshold
    
    def fit(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        if self.cols is None:
            self.cols = list(range(X.shape[1]))
            
        for col in self.cols:
            
            col_data = X[:, col]
            
            lower, upper = self._compute_bounds(col_data)
            
            if self.auto:
                if not self._has_outliers(col_data, lower, upper):
                    continue
                
            self.bounds_[col] = (lower, upper)
            self.active_cols_.append(col)
            
        return X
    
    def transform(self, X):
        
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:   # 
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        for col, (lower, upper) in self.bounds_.items():
            if self.strategy == 'clip':
                X[:, col] = np.clip(X[:, col], lower, upper)
                
            elif self.strategy == 'remove':
                mask = (X[:, col] >= lower) & (X[:, col] <= upper)
                X = X[mask]
                
            else:
                raise ValueError("strategy must be 'clip' or 'reove' ")
            
        return X
    
    def fit_transform(self, X):
        
        X = np.asarray(X, dtype=float)
        if X.ndim == 0:   
            raise ValueError("Input must be array-like, not scalar")
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
            
        self.fit(X)
        return self.transform(X)
    
import numpy as np

class _RobustStatsBase:
    def _robust_stats(self, col):
        col = col[~np.isnan(col)]

        if len(col) < 3:
            return None

        median = np.median(col)
        mad = np.median(np.abs(col - median))

        if mad == 0:
            return None

        scale = mad * 1.4826
        return median, mad, scale


class MyMADOutlierHandler(_RobustStatsBase):
    def __init__(self, threshold=3.5, strategy="clip"):
        """
        threshold: robust z-score threshold (default 3.5)
        strategy: 'clip', 'remove', 'mean', 'median'
        """
        self.threshold = threshold
        self.strategy = strategy
        self.bounds_ = {}   # lower & upper per column
        self.stats_ = {}    # median, mad, scale, mean, std per column
        self.outlier_cols_ = []

    def fit(self, X):
        X = np.asarray(X, dtype=float)

        self.bounds_.clear()
        self.stats_.clear()
        self.outlier_cols_.clear()

        for i in range(X.shape[1]):
            res = self._robust_stats(X[:, i])
            if res is None:
                continue

            med, mad, scale = res
            lower = med - self.threshold * scale
            upper = med + self.threshold * scale
            mean = np.mean(X[:, i])
            std = np.std(X[:, i])

            self.bounds_[i] = (lower, upper)
            self.stats_[i] = {"median": med, "mad": mad, "scale": scale, "mean": mean, "std": std}
            self.outlier_cols_.append(i)

        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float).copy()

        for i in self.outlier_cols_:
            col = X[:, i]
            lower, upper = self.bounds_[i]
            stats = self.stats_[i]

            mask_low = col < lower
            mask_high = col > upper
            mask = mask_low | mask_high

            if self.strategy == "clip":
                col = np.clip(col, lower, upper)
            elif self.strategy == "remove":
                col[mask] = np.nan
            elif self.strategy == "mean":
                col[mask] = stats["mean"]
            elif self.strategy == "median":
                col[mask] = stats["median"]
            else:
                raise ValueError("strategy must be one of: clip, remove, mean, median")

            X[:, i] = col

        return X

    def fit_transform(self, X):
        return self.fit(X).transform(X)



class MyHuberClipper(_RobustStatsBase):
    def __init__(self, delta=1.5):
        self.delta = delta
        self.stats_ = {}        # stores median & scale per column
        self.clip_cols_ = []    # which columns have robust stats

    def fit(self, X):
        X = np.asarray(X, dtype=float)

        self.stats_.clear()
        self.clip_cols_.clear()

        for i in range(X.shape[1]):
            res = self._robust_stats(X[:, i])
            if res is None:
                continue

            med, mad, scale = res
            self.stats_[i] = {"median": med, "scale": scale}
            self.clip_cols_.append(i)

        return self

    def transform(self, X):
        """Apply Huber clipping using the stats from fit"""
        X = np.asarray(X, dtype=float).copy()

        for i in self.clip_cols_:
            col = X[:, i]
            stats = self.stats_[i]
            med = stats["median"]
            scale = stats["scale"]

            # robust z-score
            z = (col - med) / scale
            # soft clip
            z = np.clip(z, -self.delta, self.delta)
            # reconstruct
            X[:, i] = med + z * scale

        return X

    def fit_transform(self, X):
        """Convenience method"""
        return self.fit(X).transform(X)
