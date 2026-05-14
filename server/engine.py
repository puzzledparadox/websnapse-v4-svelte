import numpy as np
import re
from itertools import product


# ─────────────────────────────────────────────
# Rule Parsing  (LaTeX → executable metadata)
# ─────────────────────────────────────────────

def normalize_latex(latex: str) -> str:
    """
    Strip LaTeX markup so we can apply simple regex parsing.
    Examples:
        'a^{2}/a \\to a; 1'  →  'a2/a→a;1'
        'a^3/a^2 \\to a; 0'  →  'a3/a2→a;0'
        'a \\to \\lambda'     →  'a→λ'
    """
    s = latex.strip()
    s = s.replace('\\to', '→')
    s = s.replace('\\lambda', 'λ')
    s = s.replace('\\Lambda', 'λ')
    # Remove braces: a^{2} → a^2
    s = re.sub(r'\{(\d+)\}', r'\1', s)
    # Remove all remaining spaces
    s = s.replace(' ', '')
    return s


def _extract_spike_count(token: str) -> int:
    """
    Parse a spike token like 'a', 'a2', 'a3' into the exponent integer.
    'a' → 1,  'a2' → 2,  'a10' → 10
    """
    token = token.strip()
    if token == 'a':
        return 1
    m = re.match(r'^a\^?(\d+)$', token)
    if m:
        return int(m.group(1))
    return 1  # fallback


def parse_rule(latex: str):
    """
    Parse one SN P rule string into structured metadata.

    Supported forms (after normalisation):
        a→a;0          (regex=1, consumed=1, produced=1, delay=0)
        a2/a→λ         (regex=2, consumed=1, produced=0, delay=0)
        a3/a2→a;0      (regex=3, consumed=2, produced=1, delay=0)
        a2/a→a;1       (regex=2, consumed=1, produced=1, delay=1)

    Returns dict:
        { regex_spikes, consumed, produced, delay, is_forgetting }
    """
    norm = normalize_latex(latex)

    # Split on →
    parts = norm.split('→')
    if len(parts) != 2:
        raise ValueError(f"Cannot parse rule (no arrow): {latex}")

    left, right = parts[0].strip(), parts[1].strip()

    # ── Left side: E/a^c  or just E (shorthand: consumed = regex) ──
    if '/' in left:
        regex_tok, consumed_tok = left.split('/', 1)
        regex_spikes = _extract_spike_count(regex_tok)
        consumed = _extract_spike_count(consumed_tok)
    else:
        regex_spikes = _extract_spike_count(left)
        consumed = regex_spikes  # shorthand

    # ── Right side: a^p; d  or  λ  or  a^p ──
    is_forgetting = ('λ' in right)
    if is_forgetting:
        produced = 0
        delay = 0
    elif ';' in right:
        prod_tok, delay_tok = right.split(';', 1)
        produced = _extract_spike_count(prod_tok)
        delay = int(delay_tok.strip())
    else:
        produced = _extract_spike_count(right)
        delay = 0

    return {
        'regex_spikes': regex_spikes,
        'consumed': consumed,
        'produced': produced,
        'delay': delay,
        'is_forgetting': is_forgetting,
    }


def build_rules_metadata(nodes):
    """
    Build rules_metadata: list-of-lists aligned to neurons.
    Each inner list holds (global_rule_index, check_fn) pairs.

    Also returns:
      - parsed_rules: flat list of parsed rule dicts (one per global rule index)
      - rule_to_neuron: maps global rule index → neuron index
    """
    rules_metadata = []  # per-neuron list of (rule_idx, check_fn)
    parsed_rules = []    # flat list of parsed dicts
    rule_to_neuron = []  # rule_idx → neuron_idx
    global_idx = 0

    for neuron_idx, node in enumerate(nodes):
        neuron_type = node.get('neuronType', 'regular')
        raw_rules = node.get('rules', [])

        if neuron_type in ('input', 'Input', 'output', 'Output') or not raw_rules:
            rules_metadata.append([])
            continue

        neuron_rule_list = []
        for rule_str in raw_rules:
            parsed = parse_rule(rule_str)
            parsed_rules.append(parsed)
            rule_to_neuron.append(neuron_idx)

            # Create a check function that captures regex_spikes
            req = parsed['regex_spikes']
            check = (lambda r: (lambda c, _r=r: int(c) == _r))(req)
            neuron_rule_list.append((global_idx, check))
            global_idx += 1

        rules_metadata.append(neuron_rule_list)

    return rules_metadata, parsed_rules, rule_to_neuron


def build_m_pi(num_rules, num_neurons, parsed_rules, rule_to_neuron, adjacency):
    """
    Build the Spiking Transition Matrix M_Pi.

    M_Pi shape: (num_rules, num_neurons)
    For rule r owned by neuron i:
        M_Pi[r, i] = -consumed      (spikes removed from owning neuron)
        M_Pi[r, j] = +produced * w  (spikes sent to each downstream neuron j with weight w)

    adjacency: dict  neuron_idx → [(target_idx, weight), ...]
    """
    m_pi = np.zeros((num_rules, num_neurons), dtype=int)

    for r_idx, pr in enumerate(parsed_rules):
        owner = rule_to_neuron[r_idx]
        m_pi[r_idx, owner] = -pr['consumed']

        if not pr['is_forgetting']:
            for (target, weight) in adjacency.get(owner, []):
                m_pi[r_idx, target] += pr['produced'] * weight

    return m_pi


def compute_stv_k(tick, nodes, adjacency_input):
    """
    Build the Spike Train Vector for a given tick.

    For each input neuron, read bit at position `tick` from its spike train,
    then distribute to connected neurons scaled by edge weight.

    adjacency_input: dict  input_neuron_idx → [(target_idx, weight), ...]
    Returns: stv_k array of length num_neurons
    """
    num_neurons = len(nodes)
    stv = np.zeros(num_neurons, dtype=int)

    for n_idx, node in enumerate(nodes):
        neuron_type = node.get('neuronType', 'regular')
        if neuron_type not in ('input', 'Input'):
            continue

        train = str(node.get('spikes', ''))
        bit = int(train[0]) if len(train) > 0 and train[0] in ('0', '1') else 0

        for (target, weight) in adjacency_input.get(n_idx, []):
            stv[target] += bit * weight

    return stv


def build_adjacency(edges, node_id_to_idx):
    """
    Build adjacency dicts from the edge list.
    Returns two dicts:
      adjacency_all:   neuron_idx → [(target_idx, weight)]  (for all non-input neurons)
      adjacency_input: neuron_idx → [(target_idx, weight)]  (only input neurons — used for stv_k)
    We return one combined adjacency; the caller filters by neuron type.
    """
    adj = {}
    for e in edges:
        src = node_id_to_idx.get(e['source'])
        tgt = node_id_to_idx.get(e['target'])
        if src is None or tgt is None:
            continue
        w = e.get('weight', 1)
        adj.setdefault(src, []).append((tgt, w))
    return adj


# ─────────────────────────────────────────────
# Core Matrix Engine  (unchanged from original)
# ─────────────────────────────────────────────

def get_next_configuration(c_k, st_k_plus_1, iv, m_pi, stv_k):
    """
    Computes next configuration. Consumption and production happen atomically
    when a rule fires (iv == 1).  st_next only gates INCOMING spikes
    (production from other neurons + stv_k), NOT consumption from a neuron's
    own firing rule.
    """
    m_consume = np.minimum(0, m_pi)   # negative entries: spikes removed from firing neuron
    m_produce = np.maximum(0, m_pi)   # positive entries: spikes sent to targets

    consumption = np.dot(iv, m_consume)            # always applied
    production  = np.dot(iv, m_produce)            # gated by st_next
    incoming    = st_k_plus_1 * (production + stv_k)

    c_next = np.maximum(0, c_k + consumption + incoming)
    return c_next


def get_indicator_vector(dv, div, dsv, rule_delay_values):
    """
    Computes which rules produce output this tick.
    - Immediate rules (delay == 0): produce when selected (dv == 1).
    - Delayed rules (delay > 0): produce ONLY when their countdown expires
      (div == 1 from a prior selection, dsv == 0 now). They do NOT produce
      on the tick they are selected, even if dsv happened to be 0.
    """
    rule_delays = np.array(rule_delay_values, dtype=int)
    # Delayed rule whose countdown has run out (was previously selected, now dsv=0)
    delayed_fires   = (div == 1) & (dsv == 0)
    # Immediate rule just selected with zero delay
    immediate_fires = (dv == 1) & (rule_delays == 0)
    return (delayed_fires | immediate_fires).astype(int)


def update_delayed_indicator(div_prev, iv, dv, dsv):
    """
    Algorithm 2: Updates the status of rules waiting to fire.
    """
    still_delayed = div_prev & np.logical_not(iv)
    newly_delayed = dv & (dsv > 0)
    return (still_delayed | newly_delayed).astype(int)


def update_delay_status(dv, dsv, rule_delay_values):
    """
    Algorithm 4: The 'Countdown' logic.
    """
    new_dsv = np.maximum(0, dsv - 1)
    new_dsv = np.where(dv == 1, rule_delay_values, new_dsv)
    return new_dsv


# ─────────────────────────────────────────────
# Non-deterministic step
# ─────────────────────────────────────────────

def get_satisfied_rules(c_k, rules_metadata, div, dsv):
    """
    For each neuron, check which of its rules are satisfied by the
    neuron's current spike count.  Returns list-of-lists of global rule indices.

    A neuron is CLOSED if any of its rules has an active delay countdown
    (div[r] == 1 and dsv[r] > 0).  Closed neurons cannot select new rules.
    """
    satisfied = []
    for neuron_idx, neuron_rules in enumerate(rules_metadata):
        if not neuron_rules:
            satisfied.append([None])
            continue

        # Closed = any rule for this neuron has div==1 (active delayed rule,
        # whether still counting down OR about to fire on this tick)
        is_closed = any(div[r_idx] == 1 for r_idx, _ in neuron_rules)
        if is_closed:
            satisfied.append([None])
            continue

        spikes = c_k[neuron_idx]
        applicable = [r_idx for r_idx, r_check in neuron_rules if r_check(spikes)]
        satisfied.append(applicable if applicable else [None])
    return satisfied


def get_all_next_nondet(current_state, rules_metadata, m_pi, stv_k, rule_delays):
    """
    Generates every possible next configuration based on rule non-determinism.
    """
    num_rules = m_pi.shape[0]
    choices_per_neuron = get_satisfied_rules(
        current_state['c_k'], rules_metadata,
        current_state['div'], current_state['dsv']
    )

    all_possible_next = []
    for chosen_indices in product(*choices_per_neuron):
        dv = np.zeros(num_rules, dtype=int)
        for idx in chosen_indices:
            if idx is not None:
                dv[idx] = 1

        # Decrement dsv FIRST, then check iv against the new dsv.
        # This ensures delay=d means exactly d ticks of being closed.
        new_dsv = update_delay_status(dv, current_state['dsv'], rule_delays)
        iv = get_indicator_vector(dv, current_state['div'], new_dsv, rule_delays)
        new_c = get_next_configuration(
            current_state['c_k'],
            current_state['st_next'],
            iv, m_pi, stv_k
        )

        new_div = update_delayed_indicator(current_state['div'], iv, dv, new_dsv)

        # rule_contribution: net change per neuron
        rule_contribution = np.dot(iv, m_pi)

        all_possible_next.append({
            'c_k': new_c,
            'dsv': new_dsv,
            'div': new_div,
            'rule_contribution': rule_contribution,
            'iv': iv,
            'dv': dv,
        })

    # ── Halting detection ──────────────────────────────────────────────────
    # The system has halted when ALL of the following hold:
    #   1. No external input is arriving (stv_k is the zero vector).
    #   2. No delay countdowns are pending in any next state (dsv == 0).
    #   3. Every possible next config is a fixed-point (c_k and div unchanged).
    # Condition 2 prevents premature halting while neurons are still counting
    # down their delays; the system is only done once all delays expire and
    # nothing new can fire.
    is_stv_empty = np.all(stv_k == 0)
    all_halted = False

    if is_stv_empty:
        all_halted = True
        for nxt in all_possible_next:
            delays_clear = np.all(np.array(nxt['dsv']) == 0)
            config_same  = np.array_equal(nxt['c_k'], current_state['c_k'])
            div_same     = np.array_equal(nxt['div'], current_state['div'])
            if not (delays_clear and config_same and div_same):
                all_halted = False
                break

    for nxt in all_possible_next:
        nxt['is_halted'] = all_halted

    return all_possible_next



# ─────────────────────────────────────────────
# Iterative search  (for string judging)
# ─────────────────────────────────────────────

def get_configs_iterative(initial_config, time_limit, string_val, rules_metadata, m_pi, rule_delays):
    """
    Iterative configuration search from WebSnapse 4 Everyone.
    """
    stack = [(0, initial_config)]
    reachable_configs = []

    while stack:
        t, current_sys = stack.pop()
        reachable_configs.append((t, current_sys))

        if t < time_limit:
            bit = int(string_val[t]) if t < len(string_val) else 0
            num_neurons = m_pi.shape[1]
            stv_k = np.zeros(num_neurons, dtype=int)
            stv_k[0] = bit  # feed into first neuron for judge mode

            if 'st_next' not in current_sys:
                current_sys['st_next'] = np.ones(num_neurons, dtype=int)

            for next_possibility in get_all_next_nondet(current_sys, rules_metadata, m_pi, stv_k, rule_delays):
                next_possibility['st_next'] = current_sys['st_next']
                stack.append((t + 1, next_possibility))

    return reachable_configs