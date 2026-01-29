import numpy as np

# Imports for defaults
from autoprep.scaler import MyStandardScaler
from autoprep.nan_handler import MyNanHandler
from autoprep.outlier_handler import MyIQROutlierHandler, MyMADOutlierHandler, MyHuberClipper
from autoprep.encoder import MyOneHotEncoder, MyOrdinalEncoder
from autoprep.skew_handler import My1LogpSkew, MyBowleyLog1pSkew

class AutoPrep:
    def __init__(
        self,
        num_cols=None,
        cat_cols=None,
        encoder=None,
        outlier_handler=None,
        scaler=None,
        skew_handler=None,
        nan_strategy="auto"
    ):
        self.num_cols = num_cols
        self.cat_cols = cat_cols

        # ---------- Defaults ----------
        self.encoder = encoder if encoder is not None else MyOneHotEncoder()
        self.outlier_handler = outlier_handler if outlier_handler is not None else MyIQROutlierHandler()
        self.scaler = scaler if scaler is not None else MyStandardScaler()
        self.skew_handler = skew_handler
        self.nan_strategy = nan_strategy

        # Internal storage
        self._fitted = False
        self.nan_handler_num = None
        self._cat_fill_values = {}  # Store fill values for categorical columns

    # ------------------ Helper: Handle Categorical NaNs ------------------
    def _handle_cat_nans(self, X_cat, fit=True):
        """
        Handle NaNs in categorical data manually.
        Uses most_frequent strategy for categorical columns.
        
        Args:
            X_cat: Categorical data (2D array)
            fit: If True, compute fill values. If False, use stored values.
        
        Returns:
            X_cat with NaNs filled
        """
        X_cat = X_cat.copy()
        
        for col_idx in range(X_cat.shape[1]):
            col = X_cat[:, col_idx]
            
            if fit:
                # Find most frequent non-NaN value
                mask = np.array([
                    x is not None and 
                    x is not np.nan and 
                    not (isinstance(x, float) and np.isnan(x)) and
                    str(x).lower() != 'nan'
                    for x in col
                ])
                
                if mask.any():
                    unique, counts = np.unique(col[mask], return_counts=True)
                    most_frequent = unique[np.argmax(counts)]
                    self._cat_fill_values[col_idx] = most_frequent
                else:
                    # All NaNs - use a default placeholder
                    self._cat_fill_values[col_idx] = "MISSING"
            
            # Fill NaNs with the stored fill value
            fill_value = self._cat_fill_values.get(col_idx, "MISSING")
            for i in range(len(col)):
                if (col[i] is None or 
                    col[i] is np.nan or 
                    (isinstance(col[i], float) and np.isnan(col[i])) or
                    str(col[i]).lower() == 'nan'):
                    X_cat[i, col_idx] = fill_value
        
        return X_cat

    # ------------------ Fit ------------------
    def fit(self, X):
        """
        Fit the AutoPrep pipeline on training data.
        
        Args:
            X: Input data (2D array-like)
        
        Returns:
            self
        """
        X = np.asarray(X, dtype=object)

        n_features = X.shape[1]
        
        # Auto-detect numerical columns if not specified
        if self.num_cols is None:
            self.num_cols = [
                i for i in range(n_features) 
                if self.cat_cols is None or i not in self.cat_cols
            ]

        # -------- Numerical Columns --------
        if self.num_cols and len(self.num_cols) > 0:
            X_num = X[:, self.num_cols].astype(float)

            # Handle NaNs in numerical data
            self.nan_handler_num = MyNanHandler(strategy=self.nan_strategy)
            X_num = self.nan_handler_num.fit_transform(X_num)

            # Apply skew transformation if specified
            if self.skew_handler is not None:
                self.skew_handler.fit(X_num)
                X_num = self.skew_handler.transform(X_num)

            # Handle outliers
            X_num = self.outlier_handler.fit_transform(X_num)
            
            # Fit scaler
            self.scaler.fit(X_num)

        # -------- Categorical Columns --------
        if self.cat_cols and len(self.cat_cols) > 0:
            X_cat = X[:, self.cat_cols]

            # Handle NaNs manually for categorical data
            X_cat = self._handle_cat_nans(X_cat, fit=True)

            # Fit encoder
            self.encoder.fit(X_cat)

        self._fitted = True
        return self

    # ------------------ Transform ------------------
    def transform(self, X):
        """
        Transform data using fitted pipeline.
        
        Args:
            X: Input data (2D array-like)
        
        Returns:
            Transformed data
        """
        if not self._fitted:
            raise RuntimeError("You must call fit() before transform()")

        X = np.asarray(X, dtype=object)
        outputs = []

        # -------- Numerical Columns --------
        if self.num_cols and len(self.num_cols) > 0:
            X_num = X[:, self.num_cols].astype(float)
            
            # Apply NaN handler
            X_num = self.nan_handler_num.transform(X_num)

            # Apply skew transformation if specified
            if self.skew_handler is not None:
                X_num = self.skew_handler.transform(X_num)

            # Apply outlier handler
            X_num = self.outlier_handler.transform(X_num)
            
            # Apply scaler
            X_num = self.scaler.transform(X_num)
            outputs.append(X_num)

        # -------- Categorical Columns --------
        if self.cat_cols and len(self.cat_cols) > 0:
            X_cat = X[:, self.cat_cols]
            
            # Handle NaNs using stored fill values
            X_cat = self._handle_cat_nans(X_cat, fit=False)
            
            # Apply encoder
            X_cat = self.encoder.transform(X_cat)
            outputs.append(X_cat)

        # Combine outputs
        if len(outputs) == 0:
            raise ValueError("No columns to transform. Specify num_cols or cat_cols.")
        
        return np.hstack(outputs) if len(outputs) > 1 else outputs[0]

    # ------------------ Fit & Transform ------------------
    def fit_transform(self, X):
        """
        Fit the pipeline and transform data in one step.
        
        Args:
            X: Input data (2D array-like)
        
        Returns:
            Transformed data
        """
        self.fit(X)
        return self.transform(X)