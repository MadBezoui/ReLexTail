import os

PROBLEMS_FILE = "/Users/madanibezoui/Documents/Projects/ALUR/code/lexpr/problems.py"

with open(PROBLEMS_FILE, 'r') as f:
    content = f.read()

# Update GEOMETRIES
old_geom = 'GEOMETRIES = ("linear", "concave", "convex", "disconnected",\n              "asymmetric", "manyknee", "degenerate", "irregular", "cars", "water")'
new_geom = 'GEOMETRIES = ("linear", "concave", "convex", "disconnected",\n              "asymmetric", "manyknee", "degenerate", "irregular", "cars", "water",\n              "knapsack", "wfg2", "jobshop", "energy", "concrete")'
content = content.replace(old_geom, new_geom)

new_code = """
    elif geometry == "knapsack":
        # Knapsack approximation (simulated combinatorial front)
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        # Shift away from origin and add discrete structure
        F = F + 0.1
        F = np.round(F * 100) / 100
        F = np.clip(F, 0.01, None)
        
    elif geometry == "wfg2":
        # WFG2-like disconnected/convex front approximation
        d = rng.random((n, m)) ** 0.5
        F = d / np.linalg.norm(d, axis=1, keepdims=True)
        patch = rng.integers(0, 5, size=n)
        F[:, 0] = F[:, 0] + 0.5 * patch
        F = F ** 2
        
    elif geometry == "jobshop":
        # Jobshop epsilon-constraint approximation (combinatorial, coarse)
        F = rng.dirichlet(np.ones(m), size=n)
        F = np.round(F * 50) / 50
        F = np.clip(F, 0.02, None)
        
    elif geometry == "energy":
        # UCI Energy Efficiency surrogate
        # Criteria: Heating load, Cooling load, Surface Area, Wall Area, Roof Area
        base = rng.dirichlet(np.ones(m), size=n)
        F = base * np.array([50, 50, 800, 400, 200][:m] + [100]*max(0, m-5))
        F = F + rng.normal(0, 0.05, size=(n, m)) * F
        F = np.clip(F, 1, None)
        
    elif geometry == "concrete":
        # UCI Concrete Strength surrogate
        # Criteria: -Strength, Cement, Water, Coarse Aggr, Fine Aggr
        base = rng.dirichlet(np.ones(m), size=n)
        F = base * np.array([-80, 500, 250, 1000, 900][:m] + [100]*max(0, m-5))
        F = F + rng.normal(0, 0.05, size=(n, m)) * F
        F = np.abs(F)
        F = np.clip(F, 1, None)
"""

content = content.replace('    else:\n        raise ValueError(f"unknown geometry {geometry!r}")', new_code + '\n    else:\n        raise ValueError(f"unknown geometry {geometry!r}")')

with open(PROBLEMS_FILE, 'w') as f:
    f.write(content)
print("problems.py updated successfully.")
