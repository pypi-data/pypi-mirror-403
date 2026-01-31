import limix
import numpy as np
from scipy.stats import chi2
import statsmodels.api as sm
from statsmodels.sandbox.stats.multicomp import multipletests


"""
Note, GLM with family NegativeBinomial takes the negative binomial dispersion 
parameter as fixed, while the discrete model NegativeBinomial estimates the 
dispersion parameter by MLE jointly with the mean parameters.

https://stackoverflow.com/questions/46835123/
"""


def glm_LRT(y, X, M=None, add_intercept=True,
            family=sm.families.NegativeBinomial(), 
            **kwargs):
    """
    Likelihood ratio test for negative binomial regression test.
    
    Note, sm.GLM with family NegativeBinomial uses fixed dispersion, please fit
    it beforehand, e.g., by statsmodels.discrete.discrete_model.NegativeBinomial
    
    Parameters
    ----------
    y : array_like, (n,) or (n, 2) for binomial family
        Input endog
    X : array_like, (n, K)
        Covariants to test
    M : array_like, (n, d)
        Covariants without testing, namely always keep
    add_intercept : bool
        Whether adding intercept
    family : statsmodels.api.families
        GLM family implemeted in statsmodels
    
    Returns
    -------
    results from statsmodels.GLM.fit() on H1, with additional properties.
    "LR" : likelihood ratio at log scale for each covariate to test
    "pval" : p value from likelihood ratio test for each covariat to test    
    """
    
    if M is not None:
        if len(M.shape) < 2:
            M = M.reshape(-1, 1).copy()
        X0 = M.copy()
            
    if add_intercept:
        if M is not None:
            if np.sum((np.min(M, axis=0) == 1) * 
                      (np.max(M, axis=0) == 1)) > 0:
                print("Intercept already exists in M.")
                pass
            else:
                X0 = np.append(X0, np.ones((len(y), 1)), axis=1)
        else:
            X0 = np.ones((len(y), 1))
        
    if len(X.shape) < 2:
        X = X.reshape(-1, 1)
        
    logLR = np.zeros(X.shape[1])
    
    # Alternative model with full features
    # print(X.shape, X0.shape)
    X1 = np.append(X, X0, axis=1)
    H1_model = sm.GLM(y, X1, family=family)
    H1_res = H1_model.fit(**kwargs)
    
    # Remove each feature as Null model
    for k in range(X.shape[1]):
        _XX = np.delete(X, k, axis=1)
        _X1 = np.append(_XX, X0, axis=1)
        H0_model = sm.GLM(y, X0, family=family)
        H0_res = H0_model.fit(**kwargs)
        logLR[k] = H0_res.deviance - H1_res.deviance
        
    # Add likelihood ratio test
    H1_res.logLR = logLR / 2
    H1_res.p_LRT = chi2.sf(logLR, 1)
    return H1_res
