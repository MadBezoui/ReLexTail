import yaml

CONFIG_FILE = "/Users/madanibezoui/Documents/Projects/ALUR/code/configs/pilot_config.yaml"

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

config['candidate_sizes'] = [100, 300, 500]
config['criteria'] = [3, 5, 8, 10, 15]
config['geometries'].extend(["knapsack", "wfg2", "jobshop", "energy", "concrete"])

with open(CONFIG_FILE, 'w') as f:
    yaml.dump(config, f, sort_keys=False)

print("config updated successfully.")
