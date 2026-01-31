# some basic functions

import numpy as np

def match(ref_ids, new_ids, uniq_ref_only=True):
    """
    Mapping new_ids to ref_ids. ref_ids can have repeated values, but new_ids 
    can only have unique ids or values. Therefore, new_ids[RT_idx] will be 
    the same as ref_ids. Note, 
    
    Parameters
    ----------
    ref_ids : array_like or list
        ids for reference with type of int, float, or string
    new_ids : array_like or list
        ids waiting to map.
        
    Returns
    -------
    RV_idx : array_like, the same length of ref_ids
        The index for new_ids mapped to ref_ids. If an id in ref_ids does not 
        exist in new_ids, then return a None for that id. 
    Examples
    --------
    >>> x1 = [5, 9, 1]
    >>> x2 = [1, 2, 5, 7, 9]
    >>> hilearn.match(x1, x2)
    array([2, 4, 0])
    >>> hilearn.match(x2, x1)
    array([2, None, 0, None, 1], dtype=object)
    >>> RT_idx = hilearn.match(x2, x1)
    >>> idx1 = np.where(RT_idx != None)[0]
    >>> idx1
    array([0, 2, 4])
    >>> idx2 = RT_idx[idx1].astype(int)
    >>> idx2
    array([2, 0, 1])
    """
    idx1 = np.argsort(ref_ids)
    idx2 = np.argsort(new_ids)
    RT_idx1, RT_idx2 = [], []
    
    i, j = 0, 0
    while i < len(idx1):
        if j == len(idx2) or ref_ids[idx1[i]] < new_ids[idx2[j]]:
            RT_idx1.append(idx1[i])
            RT_idx2.append(None)
            i += 1
        elif ref_ids[idx1[i]] == new_ids[idx2[j]]:
            RT_idx1.append(idx1[i])
            RT_idx2.append(idx2[j])
            i += 1
            if uniq_ref_only: j += 1
        elif ref_ids[idx1[i]] > new_ids[idx2[j]]:
            j += 1
            
    origin_idx = np.argsort(RT_idx1)
    RT_idx = np.array(RT_idx2)[origin_idx]
    return RT_idx


def downsample(labels, out_count, balanced_out=True):
    """Subset a list of labels to a specific number
    
    Parameters
    ----------
    labels: list or numpy.array
        A label list to down sample
    out_count: int
        The count of samples to return
    balanced_out: bool
        If True, keep each group as balanced. In the mode,
        a cutoff will detected to retain the small groups,
        and the largest group may have a few sample more than
        others to fill the gap till out_count.
        If False, a sample numpy.random.choice is in use.
        
    Return
    ------
    The index of labels that are kept.
    """
    if balanced_out:
        if type(labels) is list:
            labels = np.array(labels)
        
        id_uniq, id_count = np.unique(labels, return_counts=True)
        
        # find the min_counts
        id_uniq_sorted = id_uniq[np.argsort(id_count)]
        id_count_sorted = np.sort(id_count)
        
        ii_next = len(id_count)
        idx_out = []
        for i in range(len(id_count)):
            if id_count_sorted[i] * (len(id_count) - i) < out_count - len(idx_out):
                idx_matched = np.where(labels == id_uniq_sorted[i])[0]
                idx_out = np.append(idx_out, idx_matched)
            else:
                n_count = int((out_count - len(idx_out)) / (len(id_count) - i))
                ii_next = i
                break
            
        print("min_count: %d. %d out of %d groups below it" 
              %(n_count, ii_next, len(id_count)))
        
        for i in range(ii_next, len(id_count)):
            if i == len(id_count) - 1:
                n_count = out_count - len(idx_out)
            
            idx_matched = np.where(labels == id_uniq_sorted[i])[0]
            idx_sampled = np.random.choice(idx_matched, n_count, replace=False)
            idx_out = np.append(idx_out, idx_sampled)
            
            # print(i, len(idx_matched), id_uniq_sorted[i])
            
    else:
        idx_out = np.random.choice(len(labels), out_count, replace=False)
                
    return idx_out.astype(int)
