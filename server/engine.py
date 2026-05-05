import numpy as np

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