import numpy as np
import sys
import os

# Add the server directory to sys.path so we can import engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server')))

import engine

def test_even_positive_integer_generator():
    print("Testing Even Positive Integer Generator case study non-determinism...")

    # C^(0) = <2, 1, 3>
    current_state = {
        'c_k': np.array([2, 1, 3]),
        'st_next': np.array([1, 1, 1]), # all neurons open
        'dsv': np.array([0, 0]),
        'div': np.array([0, 0])
    }

    # rules_metadata: mock so r_1 and r_2 are satisfied for sigma_1 (index 0)
    # sigma_1 has rules r_1 (idx 0), r_2 (idx 1). Both fire if c_k[0] == 2.
    rules_metadata = [
        [(0, lambda c: c[0] == 2), (1, lambda c: c[0] == 2)]
    ]

    # m_pi matrix. 2 rules, 3 neurons.
    # r_1: consumes 1 from sigma_1, adds to others. [-1, 1, 1].
    # r_2: forgetting rule, to result in 0 spikes as per specs, it consumes 2. [-2, 0, 0].
    m_pi = np.array([
        [-1, 1, 1],
        [-2, 0, 0]
    ])

    stv_k = np.array([0, 0, 0])
    rule_delays = np.array([1, 0])

    branches = engine.get_all_next_nondet(current_state, rules_metadata, m_pi, stv_k, rule_delays)

    print(f"\nNumber of branches generated: {len(branches)}")
    
    for i, branch in enumerate(branches):
        print(f"\n--- Branch {'A' if i == 0 else 'B'} ---")
        print(f"Configuration (c_k): {branch['c_k']}")
        print(f"Delay Status Vector (dsv): {branch['dsv']}")
        print(f"Delayed Indicator Vector (div): {branch['div']}")

if __name__ == '__main__':
    test_even_positive_integer_generator()
