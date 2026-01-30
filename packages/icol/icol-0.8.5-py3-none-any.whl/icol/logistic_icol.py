import warnings
warnings.filterwarnings('ignore')

from time import time
from copy import deepcopy
from itertools import combinations, permutations

import numpy as np
import sympy as sp

from sklearn.linear_model import lars_path, Ridge, Lars
from sklearn.preprocessing import PolynomialFeatures
from sklearn.base import clone
from sklearn.model_selection import train_test_split

from sklearn.metrics import mean_squared_error, log_loss, zero_one_loss, hinge_loss, roc_auc_score
from sklearn.linear_model import LogisticRegression

def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

def corr(X, g):
    sigma_X = np.std(X, axis=0)
    sigma_Y = np.std(g)

    XY = X*g.reshape(-1, 1)
    E_XY = np.mean(XY, axis=0)
    E_X = np.mean(X, axis=0)
    E_Y = np.mean(g)
    cov = E_XY - E_X*E_Y
    sigma = sigma_X*sigma_Y
    pearsons = cov/sigma
    absolute_pearsons = np.abs(pearsons)
    absolute_pearsons[np.isnan(absolute_pearsons)] = 0 # setting all rows of constants to have 0 correlation
    absolute_pearsons[np.isinf(absolute_pearsons)] = 0 # setting all rows of constants to have 0 correlation
    absolute_pearsons[np.isneginf(absolute_pearsons)] = 0

    return absolute_pearsons 

def squared(X, y, model):
    y_hat = model.predict(X).ravel()
    res = y - y_hat
    return corr(X, res)

def df_log_loss(X, y, model):
    eta = model.decision_function(X).ravel()      # real-valued score
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
    g = y - p
    return corr(X, g)

def _sigmoid(z, clp=30):
    z = np.clip(z, -clp, clp)
    return 1.0 / (1.0 + np.exp(-z))

OBJECTIVE_DICT = {
    'squared': squared,
    'logistic': df_log_loss
}

LOSS_DICT = {
    'squared': rmse,
    'zero_one': zero_one_loss,
    'hinge': hinge_loss,
    'logloss': log_loss,
    'logistic': log_loss
}

OP_DICT = {
    'sin': {
        'op': sp.sin,
        'op_np': np.sin,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'cos': {
        'op': sp.cos,
        'op_np': np.cos,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'log': {
        'op': sp.log,
        'op_np': np.log,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'exp': {
        'op': sp.exp,
        'op_np': np.exp,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'abs': {
        'op': sp.Abs,
        'op_np': np.abs,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'sqrt': {
        'op': sp.sqrt,
        'op_np': np.sqrt,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'cbrt': {
        'op': lambda x: sp.Pow(x, sp.Rational(1, 3)),
        'op_np': lambda x: np.power(x, 1/3),
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'sq': {
        'op': lambda x: sp.Pow(x, 2),
        'op_np': lambda x: np.power(x, 2),
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'cb': {
        'op': lambda x: sp.Pow(x, 3),
        'op_np': lambda x: np.power(x, 3),
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'six_pow': {
        'op': lambda x: sp.Pow(x, 6),
        'op_np': lambda x: np.power(x, 6),
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'inv': {
        'op': lambda x: 1/x,
        'op_np': lambda x: 1/x,
        'inputs': 1,
        'commutative': True,
        'cares_units': False
        },
    'mul': {
        'op': sp.Mul,
        'op_np': np.multiply,
        'inputs': 2,
        'commutative': True,
        'cares_units': False
        },
    'div': {
        'op': lambda x, y: sp.Mul(x, 1/y),
        'op_np': lambda x, y: np.multiply(x, 1/y),
        'inputs': 2,
        'commutative': False,
        'cares_units': False
        },
    'add': {
        'op': sp.Add,
        'op_np': lambda x, y: x+y,
        'inputs': 2,
        'commutative': True,
        'cares_units': False
        },
    'sub': {
        'op': lambda x, y: sp.Add(x, -y),
        'op_np': lambda x, y: x-y,
        'inputs': 2,
        'commutative': False,
        'cares_units': False
        },
    'abs_diff': {
        'op': lambda x, y: sp.Abs(sp.Add(x, -y)),
        'op_np': lambda x, y: np.abs(x-y),
        'inputs': 2,
        'commutative': True,
        'cares_units': False
        },
    }

class FeatureExpansion:
    def __init__(self, ops, rung, printrate=1000):
        self.ops = ops
        self.rung = rung
        self.printrate = printrate
        self.prev_print = 0
        for i, op in enumerate(self.ops):
            if type(op) == str:
                self.ops[i] = (op, range(rung))
        
    def remove_redundant_features(self, symbols, names, X):
        sorted_idxs = np.argsort(names)
        for i, idx in enumerate(sorted_idxs):
            if i == 0:
                unique = [idx]
            elif names[idx] != names[sorted_idxs[i-1]]:
                unique += [idx]
        unique_original_order = np.sort(unique)
        
        return symbols[unique_original_order], names[unique_original_order], X[:, unique_original_order]
    
    def expand(self, X, names=None, verbose=False, f=None, check_pos=False):
        n, p = X.shape
        if (names is None) or (len(names) != p):
            names = ['x_{0}'.format(i) for i in range(X.shape[1])]
        
        if check_pos == False:
            symbols = sp.symbols(' '.join(name.replace(' ', '.') for name in names))
        else:
            symbols = []
            for i, name in enumerate(names):
                name = name.replace(' ', '.')
                if np.all(X[:, i] > 0):
                    sym = sp.symbols(name, real=True, positive=True)
                else:
                    sym = sp.symbols(name, real=True)               
                symbols.append(sym)

        symbols = np.array(symbols)
        names = np.array(names)
        
        if verbose: print('Estimating the creation of around {0} features'.format(self.estimate_workload(p=p, max_rung=self.rung, verbose=verbose>2)))
        
        names, symbols, X = self.expand_aux(X=X, names=names, symbols=symbols, crung=0, prev_p=0, verbose=verbose)

        if not(f is None):
            import pandas as pd
            df = pd.DataFrame(data=X, columns=names)
            df['y'] = y
            df.to_csv(f)

        return names, symbols, X
        
    def estimate_workload(self, p, max_rung,verbose=False):
        p0 = 0
        p1 = p
        for rung in range(max_rung):
            if verbose: print('Applying rung {0} expansion'.format(rung))
            new_u, new_bc, new_bn = 0, 0, 0
            for (op, rung_range) in self.ops:
                if rung in rung_range:
                    if verbose: print('Applying {0} to {1} features will result in approximately '.format(op, p1-p0))
                    if OP_DICT[op]['inputs'] == 1:
                        new_u += p1
                        if verbose: print('{0} new features'.format(p1))
                    elif OP_DICT[op]['commutative'] == True:
                        new_bc += (1/2)*(p1 - p0 + 1)*(p0 + p1 + 2)
                        if verbose: print('{0} new features'.format((1/2)*(p1 - p0 + 1)*(p0 + p1 + 2)))
                    else:
                        new_bn += (p1 - p0 + 1)*(p0 + p1 + 2)
                        if verbose: print('{0} new features'.format((p1 - p0 + 1)*(p0 + p1 + 2)))
            p0 = p1
            p1 = p1 + new_u + new_bc + new_bn
            if verbose: print('For a total of {0} features by rung {1}'.format(p1, rung))
        return p1
        
    def add_new(self, new_names, new_symbols, new_X, new_name, new_symbol, new_X_i, verbose=False):
        valid = (np.isnan(new_X_i).sum(axis=0) + np.isposinf(new_X_i).sum(axis=0) + np.isneginf(new_X_i).sum(axis=0)) == 0
        if new_names is None:
            new_names = np.array(new_name[valid])
            new_symbols = np.array(new_symbol[valid])
            new_X = np.array(new_X_i[:, valid])
        else:
            new_names = np.concatenate((new_names, new_name[valid]))
            new_symbols = np.concatenate((new_symbols, new_symbol[valid]))
            new_X = np.hstack([new_X, new_X_i[:, valid]])
#        if (verbose > 1) and not(new_names is None) and (len(new_names) % self.printrate == 0): print('Created {0} features so far'.format(len(new_names)))
        if (verbose > 1) and not(new_names is None) and (len(new_names) - self.prev_print >= self.printrate):
            self.prev_print = len(new_names)
            elapsed = np.round(time() - self.start_time, 2)
            print('Created {0} features so far in {1} seconds'.format(len(new_names),elapsed))
        return new_names, new_symbols, new_X

    def expand_aux(self, X, names, symbols, crung, prev_p, verbose=False):
        
        str_vectorize = np.vectorize(str)

        def simplify_nested_powers(expr):
            # Replace (x**n)**(1/n) with x
            def flatten_pow_chain(e):
                if isinstance(e, sp.Pow) and isinstance(e.base, sp.Pow):
                    base, inner_exp = e.base.args
                    outer_exp = e.exp
                    combined_exp = inner_exp * outer_exp
                    if sp.simplify(combined_exp) == 1:
                        return base
                    return sp.Pow(base, combined_exp)
                elif isinstance(e, sp.Pow) and sp.simplify(e.exp) == 1:
                    return e.base
                return e
            # Apply recursively
            return expr.replace(
                lambda e: isinstance(e, sp.Pow),
                flatten_pow_chain
            )
        
        if crung == 0:
            self.start_time = time()
            symbols, names, X = self.remove_redundant_features(X=X, names=names, symbols=symbols)
        if crung==self.rung:
            if verbose: print('Completed {0} rounds of feature transformations'.format(self.rung))
            return symbols, names, X
        else:
            if verbose: print('Applying round {0} of feature transformations'.format(crung+1))
#            if verbose: print('Estimating the creation of {0} features this iteration'.format(self.estimate_workload(p=X.shape[1], max_rung=1)))
                
            new_names, new_symbols, new_X = None, None, None
            
            for (op_key, rung_range) in self.ops:
                if crung in rung_range:
                    if verbose>1: print('Applying operator {0} to {1} features'.format(op_key, X.shape[1]))
                    op_params = OP_DICT[op_key]
                    op_sym, op_np, inputs, comm = op_params['op'], op_params['op_np'], op_params['inputs'], op_params['commutative']
                    if inputs == 1:
                        sym_vect = np.vectorize(op_sym)
                        new_op_symbols = sym_vect(symbols[prev_p:])
                        new_op_X = op_np(X[:, prev_p:])
                        new_op_names = str_vectorize(new_op_symbols)
                        new_names, new_symbols, new_X = self.add_new(new_names=new_names, new_symbols=new_symbols, new_X=new_X, 
                                                                    new_name=new_op_names, new_symbol=new_op_symbols, new_X_i=new_op_X, verbose=verbose)
                    elif inputs == 2:
                        for idx1 in range(prev_p, X.shape[1]):
                            sym_vect = np.vectorize(lambda idx2: op_sym(symbols[idx1], symbols[idx2]))
                            idx2 = range(idx1 if comm else X.shape[1])
                            if len(idx2) > 0:
                                new_op_symbols = sym_vect(idx2)
                                new_op_names = str_vectorize(new_op_symbols)
                                X_i = X[:, idx1]
                                new_op_X = X_i[:, np.newaxis]*X[:, idx2]                                                
                                new_names, new_symbols, new_X = self.add_new(new_names=new_names, new_symbols=new_symbols, new_X=new_X, 
                                                                        new_name=new_op_names, new_symbol=new_op_symbols, new_X_i=new_op_X, verbose=verbose)
            if not(new_names is None):                
                names = np.concatenate((names, new_names))
                symbols = np.concatenate((symbols, new_symbols))
                prev_p = X.shape[1]
                X = np.hstack([X, new_X])
            else:
                prev_p = X.shape[1]
                
            if verbose: print('After applying rounds {0} of feature transformations there are {1} features'.format(crung+1, X.shape[1]))
            if verbose: print('Removing redundant features leaves... ', end='')            
            symbols, names, X = self.remove_redundant_features(X=X, names=names, symbols=symbols)
            if verbose: print('{0} features'.format(X.shape[1]))

            return self.expand_aux(X=X, names=names, symbols=symbols, crung=crung+1, prev_p=prev_p, verbose=verbose)
    
class generalised_SIS:
    def __init__(self, s, obj='squared'):
        self.s=s
        self.obj=obj

    def __str__(self):
        return 'SIS(s={0}, obj={1})'.format(self.s, self.obj)
    
    def __repr__(self):
        return self.__str__()
    
    def __call__(self, X, y, model, pool):
        scores = OBJECTIVE_DICT[self.obj](X=X, y=y, model=model)
        idxs = np.argsort(scores)[::-1]

        pool_set = set(pool)
        chosen = []
        for j in idxs:
            if j not in pool_set:
                chosen.append(j)
                if len(chosen) == self.s:
                    break

        chosen = np.array(chosen, dtype=int)
        return scores[chosen], chosen
        
class LOGISTIC_LASSO:
    def __init__(self, C_grid=np.logspace(-4, 2, 100), solver="saga",
                 class_weight=None, max_iter=5000, tol=1e-4, eps_nnz=1e-12, 
                 clp=30, random_state=None):
        self.C_grid = np.sort(np.asarray(C_grid, dtype=float))
        self.solver = solver
        self.class_weight = class_weight
        self.max_iter = max_iter
        self.tol = tol
        self.eps_nnz = eps_nnz
        self.random_state = random_state
        self.clp = clp

        self.models = np.array([LogisticRegression(C=c, 
                           solver=self.solver, class_weight=self.class_weight, 
                           max_iter=self.max_iter, tol=self.tol, random_state=random_state,
                           penalty='l1', l1_ratio=1, fit_intercept=False,  
                           ) for c in self.C_grid], dtype=object)
        
    def get_params(self, deep=True):
        return {
            "C_grid": self.C_grid,
            "solver": self.solver,
            "class_weight": self.class_weight,
            "max_iter": self.max_iter,
            "tol": self.tol,
            "eps_nnz": self.eps_nnz,
            "random_state": self.random_state,
            "penalty": "l1",
            "l1_ratio": 1,
            "fit_intercept": False,
            'clp': self.clp
        }

    def __str__(self):
        params = self.get_params()
        params_str = ", ".join(f"{k}={params[k]!r}" for k in sorted(params))
        return f"LogisticLasso({params_str})"

    def fit(self, X, y, d, feature_names=None, verbose=False):
        self.feature_names = ['X_{0}'.format(i) for i in range(X.shape[1])] if feature_names is None else feature_names
        best_idx = 0
        for i, model in enumerate(self.models):
            if verbose: print('Fitting model {0} of {1} with C={2} and has '.format(i, len(self.models), model.C), end='')
            model.fit(X, y)
            nnz = self._count_nnz(model.coef_)
            if verbose: print('{0} nonzero terms'.format(nnz))
            if nnz<=d:
                best_idx = i
            else:
                break

        self.model_idx = best_idx
        self.model = self.models[self.model_idx]
        self.coef_ = self.model.coef_.ravel()
        self.coef_idx_ = np.arange(len(self.coef_))[np.abs(np.ravel(self.coef_)) > self.eps_nnz]
        return self
    
    def _count_nnz(self, coef):
        return int(np.sum(
            np.abs(np.ravel(coef)) > self.eps_nnz
            ))
    
    def __repr__(self, prec=3):
        coef = self.model.coef_.ravel()
        return ''.join([('+' if c > 0 else '') + sci(c, sig=prec) + '(' + self.feature_names[i] + ')' for i, c in enumerate(coef) if (np.abs(coef[i]) > self.eps_nnz)])  
    
    def decision_function(self, X):
        return np.dot(X, self.model.coef_.ravel())
    
    def predict_proba(self, X):
        z = self.decision_function(X)
        z = np.clip(z, -self.clp, self.clp)  # numerical stability
        p1 = 1.0 / (1.0 + np.exp(-z))
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])
    
    def predict(self, X , threshold=0.5):
        proba = self.predict_proba(X)
        p1 = proba[:, 1]
        return (p1 >= threshold).astype(int)

class GENERALISED_ICL:
    def __init__(self, sis, so, k, fit_intercept=True, normalize=True, pool_reset=False, optimize_k=True, track_intermediates=False, clp=30):
        self.sis = sis
        self.so = so
        self.k = int(k)

        self.fit_intercept = bool(fit_intercept)
        self.normalize = bool(normalize) and (self.sis.obj.lower() != 'logistic')
        self.pool_reset = bool(pool_reset)
        self.optimize_k = bool(optimize_k)
        self.track_intermediates = bool(track_intermediates)
        self.clp = clp

        self.pool_ = None
        self.feature_names_ = None
        self.intercept_ = 0.0
        self.coef_ = None

        self.beta_ = None
        self.beta_idx_ = None
        self.beta_sparse_ = None
        self.feature_names_sparse_ = None
        
        if self.optimize_k or self.track_intermediates: self.intermediates = np.empty(shape=(self.k, 5), dtype=object)

    def get_params(self, deep=True):
        params = {
            "sis": self.sis,
            "so": self.so,
            "k": self.k,
            "fit_intercept": self.fit_intercept,
            "normalize": self.normalize,
            "pool_reset": self.pool_reset,
            "optimize_k": self.optimize_k,
            "track_intermediates": self.track_intermediates,
            'clp': self.clp
        }

        return params
    
    def __str__(self):
        return 'ICL({0})'.format(self.get_params())

    def __repr__(self, prec=3):
        ret = []
        for i, name in enumerate(self.feature_names_sparse_):
            ret += [('+' if self.coef_[0, i] > 0 else '') + 
                    str(np.format_float_scientific(self.coef_[0, i], precision=prec, unique=False))
                      + ' (' + str(name) + ')' + '\n']
        ret += [('+' if self.intercept_>0 else '') + str(np.format_float_scientific(self.intercept_, precision=prec, unique=False))]

        return ''.join(ret)

    def solve_norm_coef(self, X, y):
        n, p = X.shape
        obj = self.sis.obj.lower()

        # Logistic: no y-normalization; with your init guard, normalize is already False.
        if obj == "logistic":
            self.a_x = X.mean(axis=0) if self.fit_intercept else np.zeros(p)
            self.b_x = X.std(axis=0)
            self.b_x = np.where(self.b_x == 0, 1.0, self.b_x)
            self.a_y = 0.0
            self.b_y = 1.0
            return self
        # Squared (regression): optionally normalize
        if self.fit_intercept:
            a_x = X.mean(axis=0)
            a_y = float(np.mean(y))
        else:
            a_x = np.zeros(p)
            a_y = 0.0

        if self.normalize:
            b_x = X.std(axis=0)
            b_y = float(np.std(y))
            # avoid division by zero for constant columns / constant y
            b_x = np.where(b_x == 0, 1.0, b_x)
            b_y = 1.0 if b_y == 0 else b_y
        else:
            b_x = np.ones(p)
            b_y = 1.0

        self.a_x, self.b_x, self.a_y, self.b_y = a_x, b_x, a_y, b_y
        return self     
    
    def normalize_Xy(self, X, y):
        obj = self.sis.obj.lower()

        Xn = (X - self.a_x) / self.b_x

        if obj == "logistic":
            # keep y in {0,1}
            yn = y
        else:
            yn = (y - self.a_y) / self.b_y

        return Xn, yn

    def coef(self):
        """
        Set self.coef_ (on original feature scale) and self.intercept_.
        Uses self.beta_sparse_ and self.beta_idx_ (support).
        """
        obj = self.sis.obj.lower()

        if self.beta_idx_ is None or len(self.beta_idx_) == 0:
            self.coef_ = np.zeros((1, 0))
            # intercept_ already set in loop; for squared you may want a_y too
            return self

        idx = np.asarray(self.beta_idx_, dtype=int)
        beta_s = np.asarray(self.beta_sparse_, dtype=float).ravel()

        # Logistic: no y scaling; coefficients are on the X scale after X normalization.
        # With your current design logistic has normalize=False, so this is just the native scale.
        if obj == "logistic":
            if self.normalize:
                coef = beta_s / self.b_x[idx]
                self.coef_ = coef.reshape(1, -1)
                if self.fit_intercept:
                    self.intercept_ = float(self.intercept_ - self.a_x[idx] @ coef)
                else:
                    self.intercept_ = 0.0
            else:
                self.coef_ = beta_s.reshape(1, -1)
                if not self.fit_intercept:
                    self.intercept_ = 0.0
            return self
        # Squared regression: if we normalized, undo it.
        if self.normalize:
            coef = beta_s * (self.b_y / self.b_x[idx])
            self.coef_ = coef.reshape(1, -1)
            if self.fit_intercept:
                self.intercept_ = self.a_y - float(self.coef_ @ self.a_x[idx].reshape(-1, 1))
            else:
                self.intercept_ = 0.0
        else:
            self.coef_ = beta_s.reshape(1, -1)
            # intercept_ should already be set in loop; ensure it exists
            if not self.fit_intercept:
                self.intercept_ = 0.0

        return self    

    def _set_x_transform(self, X):
        p = X.shape[1]
        if not self.fit_intercept and not self.normalize:
            self.a_x = np.zeros(p)
            self.b_x = np.ones(p)
            return
        
        if self.normalize:
            self.a_x = X.mean(axis=0) if self.fit_intercept else np.zeros(p)
            self.b_x = X.std(axis=0)
            self.b_x = np.where(self.b_x == 0, 1.0, self.b_x)
        else:
            # if not normalizing, don't change X at all
            self.a_x = np.zeros(p)
            self.b_x = np.ones(p)


    def _transform_X(self, X):
        return (X - self.a_x) / self.b_x

    def filter_invalid_cols(self, X):
        nans = np.isnan(X).sum(axis=0) > 0
        infs = np.isinf(X).sum(axis=0) > 0
        ninfs = np.isneginf(X).sum(axis=0) > 0

        nanidx = np.where(nans==True)[0]
        infidx = np.where(infs==True)[0]
        ninfidx = np.where(ninfs==True)[0]

        bad_cols = np.hstack([nanidx, infidx, ninfidx])
        bad_cols = np.unique(bad_cols)

        return bad_cols
    
    def _maybe_filter_X(self, X):
        X = np.asarray(X)
        # If already filtered, don't delete again
        if hasattr(self, "p_filtered_") and X.shape[1] == self.p_filtered_:
            return X
        return np.delete(X, self.bad_col, axis=1)
    
    def _sigmoid_stable(self, z):
        # stable sigmoid without hard clipping
        out = np.empty_like(z, dtype=float)
        pos = z >= 0
        out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
        ez = np.exp(z[~pos])
        out[~pos] = ez / (1.0 + ez)
        return out

    def update_intercept(self, X, y, beta=None, n_steps=50, eps=1e-12, tol=1e-10):
        if not self.fit_intercept:
            self.intercept_ = 0.0
            return self

        y = np.asarray(y).ravel()


        if self.sis.obj.lower() == "squared":
            if beta is None:
                self.intercept_ = float(np.mean(y))
            else:
                xb = np.asarray(X @ beta).ravel()
                self.intercept_ = float(np.mean(y - xb))
                return self

        if self.sis.obj.lower() != "logistic":
            raise ValueError(f"Unknown objective {self.sis.obj.lower()}")


    # logistic
        if beta is None:
            pbar = float(np.mean(y))
            pbar = min(max(pbar, eps), 1.0 - eps)
            self.intercept_ = float(np.log(pbar / (1.0 - pbar)))
            return self


        xb = np.asarray(X @ beta).ravel()
        b = float(getattr(self, "intercept_", 0.0)) # warm start


    # Newton-Raphson on b: solve sum(y - sigmoid(xb+b)) = 0
        for _ in range(int(n_steps)):
            eta = xb + b
            p = self._sigmoid_stable(eta)


            g = np.sum(y - p) # gradient of log-likelihood wrt b
            h = np.sum(p * (1.0 - p)) # negative second derivative (positive)


        # If h is tiny, Newton becomes unstable / ineffective -> break to bisection
            if h <= eps:
                break


            step = g / h
            b_new = b + step


            if abs(b_new - b) < tol:
                b = b_new
                self.intercept_ = float(b)
                return self

            b = b_new


    # --- Bisection fallback (monotone root find) ---
    # f(b) = sum(y - sigmoid(xb+b)) is strictly decreasing in b.
        def f(bb):
            return float(np.sum(y - self._sigmoid_stable(xb + bb)))


    # Build a bracket that spans the root.
    # Start near current b and expand.
        lo, hi = b - 1.0, b + 1.0
        flo, fhi = f(lo), f(hi)


        # We want flo >= 0 and fhi <= 0 (or vice versa); expand until sign change
        expand = 0
        while flo * fhi > 0 and expand < 60:
            lo -= 2.0 ** expand
            hi += 2.0 ** expand
            flo, fhi = f(lo), f(hi)
            expand += 1


    # If still no sign change, just keep current b (pathological separation)
        if flo * fhi > 0:
            self.intercept_ = float(b)
            return self


    # Bisection
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            fmid = f(mid)
            if abs(fmid) < 1e-12:
                b = mid
                break
            if flo * fmid > 0:
                lo, flo = mid, fmid
            else:
                hi, fhi = mid, fmid
            if abs(hi - lo) < 1e-10:
                b = 0.5 * (lo + hi)
                break
        self.intercept_ = float(b)
        return self
    
    def refit_logistic_intercept(self, xb, y, b0=0.0, max_iter=50, tol=1e-10):
        b = b0
        for _ in range(max_iter):
            eta = xb + b
            # stable sigmoid
            p = np.where(
            eta >= 0,
            1.0 / (1.0 + np.exp(-eta)),
            np.exp(eta) / (1.0 + np.exp(eta)),
            )
            g = np.mean(y - p)
            h = np.mean(p * (1 - p))
            if h < 1e-12:
                break
            step = g / h
            b += step
            if abs(step) < tol:
                break
        return b

    def fitting(self, X, y, feature_names=None, verbose=False, track_pool=False, opt_k = None):
        self.feature_names_ = feature_names
        n,p = X.shape
        stopping = self.k if opt_k is None else opt_k
        if verbose: print('Stopping after {0} iterations'.format(stopping))

        pool_ = set()
        if track_pool: self.pool = []
        beta = np.zeros(X.shape[1], dtype=float)  # empty model coefficients
        self.update_intercept(X, y, beta=None)


        res = y
        i = 0
        IC = np.infty
        while i < stopping:
            self.update_intercept(X, y, beta=beta)

            if verbose: print('.', end='')

            p, sis_i = self.sis(X=X, y=y, model=self, pool=list(pool_))
            pool_old = deepcopy(pool_)
            pool_.update(sis_i)
            pool_lst = list(pool_)
            if track_pool: self.pool = pool_lst
            if str(self.so) == 'EffAdaLASSO(gamma=1)':
                self.so(X=X, y=y, d=i+1, feature_names=feature_names[pool_lst], idx_old = list(pool_old), idx_new=sis_i, verbose=verbose)
            else:
                self.so.fit(X=X[:, pool_lst], y=y, d=i+1, feature_names=feature_names[pool_lst], verbose=verbose)
            beta_i = self.so.coef_

            beta = np.zeros(X.shape[1], dtype=float)
            beta[pool_lst] = beta_i

            # NOW update intercept using the newly solved beta
            self.update_intercept(X, y, beta=beta)

            if self.optimize_k or self.track_intermediates:
                idx = np.nonzero(beta)[0]
                if self.normalize:
                    coef = (beta[idx].reshape(1, -1)*self.b_y/self.b_x[idx].reshape(1, -1))
                    if self.fit_intercept:
                        intercept_ = self.a_y - coef.dot(self.a_x[idx])
                else:
                    coef = beta[idx]
                    if self.fit_intercept:
                        intercept_ = self.intercept_
                if len(coef.shape) > 1:
                    coef = coef[0]
                expr = ''.join([('+' if float(c) >= 0 else '') + str(np.round(float(c), 3)) + str(self.feature_names_[idx][q]) for q, c in enumerate(coef)])
                if verbose: print('Model after {0} iterations: {1}'.format(i, expr))

                self.intermediates[i, 0] = deepcopy(idx)
                self.intermediates[i, 1] = coef # deepcopy(beta[idx])
                self.intermediates[i, 2] = intercept_ if self.fit_intercept else 0
                self.intermediates[i, 3] = self.feature_names_[idx]
                self.intermediates[i, 4] = expr

            if self.pool_reset:
                idx = np.abs(beta_i) > 0 
                beta_i = beta_i[idx] 
                pool_lst = np.array(pool_lst)[idx]
                pool_lst = pool_lst.ravel().tolist()
                pool_ = set(pool_lst)

            self.beta_ = beta
            self.beta_idx_ = list(np.nonzero(self.beta_)[0])
            self.beta_sparse_ = self.beta_[self.beta_idx_]
            self.feature_names_sparse_ = np.array(self.feature_names_)[self.beta_idx_]
            self.coef()
            
            i += 1
        if self.optimize_k or self.track_intermediates: self.intermediates = self.intermediates[:, :i]
            
        if verbose: print()
        
        self.beta_ = beta
        self.update_intercept(X, y, beta=beta)

        self.beta_idx_ = list(np.nonzero(self.beta_)[0])
        self.beta_sparse_ = self.beta_[self.beta_idx_]
        self.feature_names_sparse_ = np.array(self.feature_names_)[self.beta_idx_]

        return self
    
    def fit(self, X, y, val_size=0.1, feature_names=None, timer=False, verbose=False, track_pool=False, random_state=None):
        if verbose: print('removing invalid features')
        self.bad_col = self.filter_invalid_cols(X)
        X_ = np.delete(X, self.bad_col, axis=1)
        self.p_filtered_ = X_.shape[1]

        have_valid_names = not(feature_names is None) and X.shape[1] == len(feature_names)
        feature_names_ = np.delete(np.array(feature_names), self.bad_col) if have_valid_names else np.array(['X_{0}'.format(i) for i in range(X_.shape[1])])
      
        if verbose: print('Feature normalisation')
        self.solve_norm_coef(X_, y)
        X_, y_ = self.normalize_Xy(X_, y)

        if verbose: print('Fitting ICL model')
        if timer: start=time()
        if self.optimize_k == False:
            self.fitting(X=X_, y=y_, feature_names=feature_names_, verbose=verbose, track_pool = track_pool)
        else:
            if verbose: print('Finding optimal model size')
            X_train, X_val, y_train, y_val = train_test_split(
                X_, y_, test_size=val_size, random_state=random_state
            )

            self.fitting(X=X_train, y=y_train, feature_names=feature_names_, verbose=verbose, track_pool=track_pool)

            best_k, best_loss = 0, np.inf

            for kk in range(self.intermediates.shape[0]):  # number of fitted iterations
                idx = self.intermediates[kk, 0]
                coef = np.asarray(self.intermediates[kk, 1]).ravel()
                inter = float(self.intermediates[kk, 2])

                # raw score
                eta_val = (X_val[:, idx] @ coef) + inter

                if self.sis.obj == "squared":
                    # regression prediction
                    y_pred = eta_val
                    loss_val = rmse(y_val.ravel(), y_pred.ravel())

                elif self.sis.obj == "logistic":
                    # classification probability for class 1
                    eta_val = np.clip(eta_val, -30, 30)
                    p1 = 1.0 / (1.0 + np.exp(-eta_val))
                    loss_val = log_loss(y_val.ravel(), p1.ravel())

                else:
                    raise ValueError(f"Unknown objective '{self.sis.obj}'")

                if loss_val < best_loss:
                    best_k, best_loss = kk + 1, loss_val

            if verbose: print(f'refitting with k={best_k} (val loss={best_loss})')
            self.fitting(X=X_, y=y_, feature_names=feature_names_, verbose=verbose, track_pool=track_pool, opt_k=best_k)

        if timer: self.fit_time=time()-start
        if timer and verbose: print(self.fit_time)

        self.beta_so_ = self.beta_sparse_
        self.feature_names = self.feature_names_sparse_
        obj = self.sis.obj.lower()


        if obj == "squared":
            coef_hat, _, _, _ = np.linalg.lstsq(
                a=X_[:, self.beta_idx_],
                b=y_.reshape(-1, 1),
                rcond=None
            )
            self.beta_sparse_ = coef_hat.ravel()
        elif obj == "logistic":
            if self.beta_idx_ is None or len(self.beta_idx_) == 0:
                # intercept-only fallback (no features selected)
                self.beta_sparse_ = np.zeros(0, dtype=float)
                # keep intercept_ from the iterative updates
            else:
                # eta = X_[:, self.beta_idx_] @ self.beta_so_
                # self.intercept = self.refit_logistic_intercept(xb=eta, y=y, b0=self.intercept_)
                lr = LogisticRegression(penalty=None, solver='lbfgs', fit_intercept=True)
                lr.fit(X_[:, self.beta_idx_], y_)
                coef_s = lr.coef_.ravel()
                self.intercept_ = float(lr.intercept_[0])
                self.beta_sparse_ = coef_s


        else:
            raise ValueError(f"Unknown objective '{self.sis.obj.lower()}'")
            
        self.beta_ = np.zeros(X_.shape[1], dtype=float)
        if len(self.beta_idx_) > 0:
            self.beta_[self.beta_idx_] = self.beta_sparse_

        if verbose: print('Inverse Transform of Feature Space')
        self.coef()

        return self
    
    def decision_function(self, X):
        X_ = self._maybe_filter_X(X)

        if self.beta_idx_ is None or len(self.beta_idx_) == 0:
            return np.full(X_.shape[0], self.intercept_, dtype=float)

        coef = self.coef_.ravel()
        eta = X_[:, self.beta_idx_] @ coef + self.intercept_

        return eta

    def predict_proba(self, X):
        eta = self.decision_function(X)

        # numerical stability
        eta = np.clip(eta, -30, 30)
        p1 = 1.0 / (1.0 + np.exp(-eta))
        p0 = 1.0 - p1

        return np.column_stack([p0, p1])
    
    def predict(self, X, threshold=0.5):
        obj = self.sis.obj.lower()
        if obj == "squared":
            return self.decision_function(X)
        elif obj == "logistic":
            p1 = self.predict_proba(X)[:, 1]
            return (p1 >= threshold).astype(int)
        else:
            raise ValueError(f"Unknown objective '{self.sis.obj.lower()}'")
    
    def predict_score(self, X):
        return self.decision_function(X)
    
    def negative_gradient(self, X, y):
        if self.sis.obj.lower() == "squared":
            return y - self.decision_function(X)

        elif self.sis.obj.lower() == "logistic":
            eta = self.decision_function(X)
            p = 1.0 / (1.0 + np.exp(-np.clip(eta, -self.clp, self.clp)))
            return y - p

        else:
            raise ValueError(f"Unknown objective {self.sis.obj.lower()}")
        
sci = lambda x, sig=3: f"{float(x):.{sig}e}"

if __name__ == "__main__":
    from sklearn.model_selection import train_test_split
    import pandas as pd
    import os

    random_state = 0
    np.random.seed(random_state)

    test_num = 1
    test = "SYNTHETIC" if test_num == 0 else ("DIABETES" if test_num == 1 else "EARTHQUAKE")

    if test == "DIABETES":
        df = pd.read_csv(os.path.join(os.getcwd(), "Input", "pima.csv"))
        df["DIABETES"] = df["DIABETES"].map({"Y":1, "N": 0})
        y = df['DIABETES'].values
        X = df.drop(columns=['DIABETES'])
        feature_names = X.columns
        X = X.values

        rung = 2
        small = ['sin', 'cos', 'log', 'abs', 'sqrt', 'cbrt', 'sq', 'cb', 'inv']
        big = ['six_pow', 'exp', 'add', 'mul', 'div', 'abs_diff']

        small = ['log', 'sqrt', 'cbrt', 'sq', 'cb', 'inv']
        big = ['mul', 'div']

        small  = [(op, range(rung)) for op in small]
        big = [(op, range(1)) for op in big]
        ops = small+big

        FE = FeatureExpansion(rung=rung, ops=ops)
        Phi_names, Phi_symbols, Phi_ = FE.expand(X=X, names=feature_names, check_pos=True, verbose=True)
        X_train, X_test, y_train, y_test = train_test_split(Phi_, y, test_size=0.2, random_state=random_state)

        s = 20
        k=5
        so = LOGISTIC_LASSO()
        sis = generalised_SIS(s=s, obj='logistic')
        model = GENERALISED_ICL(sis=sis, so=so, k=5, optimize_k=False, normalize=True)

        model.fit(X_train, y_train, feature_names = Phi_names, verbose=True)
        print(model.__repr__())
        print('zero_one: {0}'.format(zero_one_loss(y_test, model.predict(X_test))))
        print('logloss: {0}'.format(log_loss(y_test, model.predict_proba(X_test)[:, 1])))
        print('auc: {0}'.format(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])))


        p = model.predict_proba(X_test)[:, 1]
        print("min/max:", p.min(), p.max())
        print("quantiles:", np.quantile(p, np.linspace(start=0, stop=1, num=50)))
        print("mean:", p.mean())
        print("predicted positives @0.5:", np.mean(p >= 0.5))

    elif test == "SYNTHETIC":
        k,n,p=5,10000,1000
        rng = np.random.default_rng(random_state)
        X = rng.standard_normal((n,p))
        feature_names = np.array(['X_{0}'.format(i) for i in range(p)])
        support = range(k)
        beta = np.zeros(p, dtype=float)
        signs = rng.choice([-1.0, 1.0], size=k)
        mags = rng.uniform(0.5, 1.5, size=k)
        beta[support] = signs * mags
        eta_no_b = X @ beta
        b = float(-np.mean(eta_no_b))
        eta = eta_no_b + b
        p1 = 1.0 / (1.0 + np.exp(-np.clip(eta, -50, 50)))
        y = rng.binomial(1, p1, size=n).astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.2)

        s = 2
        so = LOGISTIC_LASSO()
        sis = generalised_SIS(s=s, obj='logistic')
        model = GENERALISED_ICL(sis=sis, so=so, k=k, optimize_k=False, normalize=False)

        model.fit(X_train, y_train, feature_names=feature_names, verbose=True)
        print(model.__repr__())
        
        print('True Coef: {0}'.format(beta[:k]))
        print('True intercept: {0}'.format(b))
    elif test == "EARTHQUAKE":
        import pickle
        from sklearn.model_selection import GroupKFold

        start_total = time()

        path = os.path.join(os.getcwd(), 'Input', 'Features_new.pkl')
        df = pickle.load(open(os.path.join(path), "rb"))

        random_state = 0
        rng = np.random.default_rng(random_state)

        use_groups = 5

        all_ids = df["ID"].unique()
        chosen_ids = rng.choice(all_ids, size=use_groups, replace=False)
        print("Chosen IDs:", chosen_ids)

        df_sub = df[df["ID"].isin(chosen_ids)].copy()
        print("Subset shape:", df_sub.shape)
        print("Class balance:", df_sub["aftershocksyn"].mean())

        y = df_sub['aftershocksyn'].values
        X = df_sub.drop(columns=['ID', 'aftershocksyn'])
        feature_names_raw = X.columns
        X = X.values

        groups = df_sub["ID"].to_numpy() 
        unique_events = np.unique(groups)

        gkf = GroupKFold(n_splits=len(unique_events))

        verbose=2
        rung = 1
        # small = ['sin', 'cos', 'log', 'abs', 'sqrt', 'cbrt', 'sq', 'cb', 'inv']
        # big = ['exp', 'six_pow', 'mul', 'div', 'abs_diff', 'add']

        small = ['sin', 'cos', 'log', 'abs', 'sqrt', 'cbrt', 'sq', 'cb', 'inv']
        big = ['exp', 'six_pow', 'mul', 'div', 'abs_diff', 'add']
        small  = [(op, range(rung)) for op in small]
        big = [(op, range(1)) for op in big]
        ops = small+big
        check_pos = True

        FE = FeatureExpansion(ops=ops, rung=rung)
        Phi_names, Phi_symbols, Phi = FE.expand(X=X, names=feature_names_raw, verbose=verbose, check_pos=check_pos)
        Phi.shape

        s=20
        k=3
        so = LOGISTIC_LASSO()
        sis = generalised_SIS(s=s, obj='logistic')
        icl_base = GENERALISED_ICL(sis=sis, so=so, k=5, optimize_k=False, normalize=False)

        aucs = []
        coefs = []   # optional: store coefficients to see recovery stability

        models = []


        for fold, (train_idx, test_idx) in enumerate(gkf.split(Phi, y, groups)):
            print(f"Fold {fold+1}/{len(unique_events)}")

            X_train, X_test = Phi[train_idx], Phi[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            n,p = X_train.shape
            print(n, p)

            model = GENERALISED_ICL(sis=generalised_SIS(s=s, obj='logistic'), so=LOGISTIC_LASSO(C_grid=np.logspace(-4, 2, 250)), k=k, optimize_k=False, normalize=False)
            # model = clone(icl_base)
            start_fit = time()
            model.fit(X_train, y_train, feature_names=Phi_names, verbose=verbose>1)
            fit_time = time() - start_fit
            total_time = time() - start_total   
            print(model.__repr__())
            models.append(model.__repr__())
            print('Fitted in {0} seconds, total time elapsed {1} seconds'.format(np.round(fit_time, 4), np.round(total_time, 4)))

            y_prob = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_prob)
            aucs.append(auc)

            # Optional: store coefficients for recovery analysis
            if hasattr(model, "coef_"):
                coefs.append(model.coef_.copy())

        print("Mean AUC:", np.mean(aucs))
        print("Std AUC :", np.std(aucs))
        for model in models:
            print(model)