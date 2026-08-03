import numpy as np
from lexpr.continuous import continuous_lexpr

for m in [3, 4, 5, 6, 8]:
    # random polytope setup just to run the counter
    np.random.seed(42)
    n = 10
    C = np.random.rand(m, n)
    A = np.random.rand(5, n)
    b = np.ones(5)
    
    try:
        x, info = continuous_lexpr(C, A, b)
        print(f"m={m}: total={info['solver_calls']}, bounds={info['bound_calls']}, anchors={info['anchor_calls']}, stages={info['stage_calls']}")
    except Exception as e:
        pass
