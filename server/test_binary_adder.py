"""
test_binary_adder.py

Standalone testing script to verify the SN P system engine's correctness
when simulating the 'Binary Adder' computational benchmark.
This test manually constructs the system's nodes and edges, runs the engine
loop, and verifies if the resulting spike train exactly matches the expected
mathematical output (0010010).
"""
import numpy as np
from engine import (
    build_rules_metadata,
    build_m_pi,
    build_adjacency,
    compute_stv_k,
    get_all_next_nondet,
)

# Define the initial network structure for the Binary Adder
nodes = [
    {'id': 'in_0',  'neuronType': 'input',   'spikes': '111',  'rules': []},
    {'id': 'in_1',  'neuronType': 'input',   'spikes': '1101', 'rules': []},
    {'id': 'add',   'neuronType': 'regular', 'spikes': 0,
     'rules': ['a \\to a; 0', 'a^2/a \\to \\lambda', 'a^3/a^2 \\to a; 0']},
    {'id': 'out',   'neuronType': 'output',  'spikes': 0,      'rules': []},
]

edges_raw = [
    {'source': 'in_0', 'target': 'add', 'weight': 1},
    {'source': 'in_1', 'target': 'add', 'weight': 1},
    {'source': 'add',  'target': 'out', 'weight': 1},
]

node_ids = [n['id'] for n in nodes]
node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
num_neurons = len(nodes)

adjacency = build_adjacency(edges_raw, node_id_to_idx)
rules_metadata, parsed_rules, rule_to_neuron = build_rules_metadata(nodes)
num_rules = len(parsed_rules)

m_pi = build_m_pi(num_rules, num_neurons, parsed_rules, rule_to_neuron, adjacency)
rule_delays = np.array([pr['delay'] for pr in parsed_rules], dtype=int)

print("=== Parsed rules ===")
for i, pr in enumerate(parsed_rules):
    print(f"  Rule {i}: regex={pr['regex_spikes']}  consumed={pr['consumed']}  produced={pr['produced']}  delay={pr['delay']}  forgetting={pr['is_forgetting']}")
print()
print("=== M_Pi ===")
print(m_pi)
print()

c_k = np.zeros(num_neurons, dtype=int)
div = np.zeros(num_rules, dtype=int)
dsv = np.zeros(num_rules, dtype=int)
st_next = np.ones(num_neurons, dtype=int)
out_idx = node_id_to_idx['out']

output_spike_train = []
prev_out_spikes = 0

MAX_TICKS = 12

# Run the simulation loop for a fixed number of ticks
for t in range(MAX_TICKS):
    stv_k = compute_stv_k(t, nodes, adjacency)

    state = {
        'c_k': c_k.copy(),
        'div': div.copy(),
        'dsv': dsv.copy(),
        'st_next': st_next.copy(),
    }

    # Simulate UI string trimming for the next tick
    for n in nodes:
        if n['neuronType'] == 'input':
            if len(n['spikes']) > 0:
                n['spikes'] = n['spikes'][1:]

    results = get_all_next_nondet(state, rules_metadata, m_pi, stv_k, rule_delays)

    if not results:
        break

    branch = results[0]
    spike_to_out = int(branch['c_k'][out_idx]) - int(c_k[out_idx])
    output_spike_train.append(max(0, spike_to_out))

    print(f"Tick {t}: stv_k={stv_k.tolist()}  c_k={c_k.tolist()} -> c_next={branch['c_k'].tolist()}  out_spike={max(0, spike_to_out)}")



    c_k = branch['c_k']
    div = branch['div']
    dsv = branch['dsv']
    
    if branch.get('is_halted'):
        print(f"  System halted at tick {t} via is_halted flag.")
        break

output_str = ''.join(str(b) for b in output_spike_train)
print(f"\n=== OUTPUT SPIKE TRAIN: {output_str} ===")
print(f"Expected:                0010010")
if output_str == '0010010':
    print("Match: YES")
else:
    print("Match: NO")
