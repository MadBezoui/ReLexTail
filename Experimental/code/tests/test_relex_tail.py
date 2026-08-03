import numpy as np
import pytest
from lexpr.orders.relex_tail import compute_profile, compare_profiles

def generate_random_profiles(n, k, rng):
    return rng.uniform(0, 1, size=(n, k))

def test_relex_tail_properties():
    # Run 10^5 random property tests
    rng = np.random.default_rng(42)
    n_tests = 100000
    
    # We can do this vectorized or loop. A loop of 100_000 might take a few seconds.
    # To speed up, we will generate batch and check.
    K = 5
    resolutions = {
        "maximum": "0.05",
        "tail_025": "0.05",
        "tail_050": "0.05",
        "tail_100": "0.05"
    }
    
    # Generate d and e
    D = generate_random_profiles(n_tests, K, rng)
    E = generate_random_profiles(n_tests, K, rng)
    
    completeness_passed = True
    transitivity_passed = True
    pareto_passed = True
    strict_pareto_passed = True
    permutation_passed = True
    uniform_replication_passed = True
    
    for i in range(n_tests):
        d = D[i]
        e = E[i]
        
        pd = compute_profile(d, resolutions)
        pe = compute_profile(e, resolutions)
        
        cmp_de = compare_profiles(pd, pe)
        
        # 1. Completeness: d <= e or e <= d is always true since compare_profiles returns -1, 0, or 1.
        if cmp_de not in (-1, 0, 1):
            completeness_passed = False
            
        # 2. Transitivity: d <= e and e <= f -> d <= f
        # We'll just generate an f for a subset to save time, or do it for all.
        f = rng.uniform(0, 1, size=K)
        pf = compute_profile(f, resolutions)
        cmp_ef = compare_profiles(pe, pf)
        cmp_df = compare_profiles(pd, pf)
        
        if cmp_de <= 0 and cmp_ef <= 0:
            if cmp_df > 0:
                transitivity_passed = False
                
        # 3. Pareto: if d <= e componentwise -> pd <= pe
        # We can construct a guaranteed dominated e'
        e_dominated = d + rng.uniform(0, 0.1, size=K)
        pe_dom = compute_profile(e_dominated, resolutions)
        if compare_profiles(pd, pe_dom) > 0:
            pareto_passed = False
            
        # 4. Strict Pareto: if d <= e and d != e -> pd < pe
        # e_dominated is strictly greater (since we add uniform(0, 0.1) which has 0 prob of being all 0)
        if compare_profiles(pd, pe_dom) >= 0:
            strict_pareto_passed = False
            
        # 5. Permutation: d ~ sigma(d)
        d_perm = rng.permutation(d)
        pd_perm = compute_profile(d_perm, resolutions)
        if compare_profiles(pd, pd_perm) != 0:
            permutation_passed = False
            
        # 6. Uniform replication: d <= e <=> r*d <= r*e
        # r is replicating elements. e.g. np.repeat
        r = 3
        d_rep = np.repeat(d, r)
        e_rep = np.repeat(e, r)
        pd_rep = compute_profile(d_rep, resolutions)
        pe_rep = compute_profile(e_rep, resolutions)
        cmp_rep = compare_profiles(pd_rep, pe_rep)
        
        if cmp_de != cmp_rep:
            uniform_replication_passed = False
            
    assert completeness_passed, "Completeness failed"
    assert transitivity_passed, "Transitivity failed"
    assert pareto_passed, "Pareto failed"
    assert strict_pareto_passed, "Strict Pareto failed"
    assert permutation_passed, "Permutation failed"
    assert uniform_replication_passed, "Uniform replication failed"
