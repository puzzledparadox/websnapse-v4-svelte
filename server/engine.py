import numpy as np
from itertools import product

def get_next_configuration(c_k, st_k_plus_1, iv_k, m_pi, stv_k):
    """
    Computes the system configuration for the next time step (k+1).
    Based on Definition 10 in WebSnapse Reloaded.

    Args:
        c_k: Configuration Vector (current spikes in neurons)
        st_k_plus_1: Status Vector (1 if neuron is open, 0 if closed)
        iv_k: Indicator Vector (1 if rule is satisfied and firing)
        m_pi: Spiking Transition Matrix (rule-to-neuron relationships)
        stv_k: Spike Train Vector (incoming spikes from environment)
    """
    # 1. Compute the net gain from rule firing and external spike trains
    # Corresponds to (Iv * M_Pi + STv) in the paper
    net_gain = np.dot(iv_k, m_pi) + stv_k

    # 2. Apply the Status Vector via element-wise multiplication (Hadamard product)
    # Spikes are only added/consumed if the neuron is open
    effective_gain = st_k_plus_1 * net_gain

    # 3. Calculate the next configuration
    c_next = c_k + effective_gain

    return c_next

def get_indicator_vector(dv, div, dsv):
    """
    Algorithm 1: Computes which rules actually fire.
    A rule fires if it's chosen (dv) or was already delayed (div),
    provided the neuron isn't currently closed (dsv == 0).
    """
    # Logical OR of chosen and delayed, AND NOT currently in delay cooldown
    return (np.logical_or(dv, div) & (dsv == 0)).astype(int)

def update_delayed_indicator(div_prev, iv, dv, dsv):
    """
    Algorithm 2: Updates the status of rules waiting to fire.
    A rule stays delayed if it hasn't fired yet, or starts being delayed if it was chosen but has a delay > 0.
    """
    still_delayed = div_prev & np.logical_not(iv)
    newly_delayed = dv & (dsv > 0)
    return (still_delayed | newly_delayed).astype(int)

def update_delay_status(dv, dsv, rule_delay_values):
    """
    Algorithm 4: The 'Countdown' logic.
    Decrements existing delays and sets new ones for chosen rules.
    """
    # 1. Decrement all active delays (don't go below 0)
    new_dsv = np.maximum(0, dsv - 1)

    # 2. For rules chosen in this tick (dv), set their initial delay values
    # If a rule with delay 2 is picked, it starts at 2 ticks.
    new_dsv = np.where(dv == 1, rule_delay_values, new_dsv)

    return new_dsv

def get_configs_iterative(initial_config, time_limit):
    """
    Iterative configuration search from WebSnapse 4 Everyone.
    Avoids Python's recursion limit for large inputs like n=1000.
    """
    stack = [(0, initial_config)]
    reachable_configs = []

    while stack:
        t, current_sys = stack.pop()
        reachable_configs.append(current_sys)

        if t < time_limit:
            # In a real run, we'd calculate ALL possible next configurations here to handle non-determinism.
            for next_possibility in get_all_next_nondet(current_sys):
                stack.append((t + 1, next_possibility))

    return reachable_configs

def get_satisfied_rules(c_k, rules_metadata):
    """
    Checks each neuron's spike count against its rules' regular expressions.
    Returns a list of lists, where each sublist contains indices of satisfied rules for that neuron.
    """
    satisfied = []
    for neuron_rules in rules_metadata:
        # Each rule index that meets its firing/forgetting condition
        applicable = [r_idx for r_idx, r_check in neuron_rules if r_check(c_k)]
        satisfied.append(applicable)
    return satisfied

def get_all_next_nondet(current_state, rules_metadata, m_pi, stv_k, rule_delays):
    """
    Generates every possible next configuration based on rule non-determinism.
    """
    # 1. Find which rules *could* fire in each neuron
    choices_per_neuron = get_satisfied_rules(current_state['c_k'], rules_metadata)

    # 2. Generate the Cartesian product of all valid choices
    # This creates every valid Decision Vector (Dv) for the whole system
    all_possible_next = []
    for chosen_indices in product(*choices_per_neuron):
        # Create a zeroed Decision Vector for this specific branch
        dv = np.zeros(m_pi.shape[0], dtype=int)
        for idx in chosen_indices:
            dv[idx] = 1

        # 3. Use existing matrix math to compute this specific branch
        # This implements: C(k+1) = C(k) + St(k+1) * (Iv * M + STv)
        iv = get_indicator_vector(dv, current_state['div'], current_state['dsv'])
        new_c = get_next_configuration(
            current_state['c_k'],
            current_state['st_next'],
            iv, m_pi, stv_k
        )

        # Update delays for this branch
        new_dsv = update_delay_status(dv, current_state['dsv'], rule_delays)
        new_div = update_delayed_indicator(current_state['div'], iv, dv, new_dsv)

        all_possible_next.append({
            'c_k': new_c,
            'dsv': new_dsv,
            'div': new_div
        })

    return all_possible_next