import numpy as np

def get_PCA(X, n_components=5):
    """
    Calculate PCA for a given matrix 
    
    Parameters
    ----------
    
    X : array_like, (var, obs)
        Input matrix
    n_components : int
        Number of component to return; should be <= X.shape[1]
    """
    from sklearn.decomposition import PCA

    n_comp = min(X.shape[0], n_components)

    pca = PCA(n_components=n_comp)
    pca.fit(X)
    PC_mat = pca.components_
    
    return PC_mat

# , min_sum=None
#     n_comp = min(X.shape[0], n_components)
#     PC_mat = np.zeros((n_components, X.shape[1]))
#     PC_mat[:, :] = None
    
#     if min_sum is not None:
#         idx = np.where(np.sum(X, axis=0) >= min_sum)[0]
#     else:
#         idx = range(X.shape[1])
        
#     pca = PCA(n_components=n_comp)
#     pca.fit(X[:, idx])
#     PC_mat[:, idx] = pca.components_
    
#     return PC_mat
