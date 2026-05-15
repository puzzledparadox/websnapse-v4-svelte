import numpy as np
import re
from itertools import product


# ─────────────────────────────────────────────
# Rule Parsing  (LaTeX → executable metadata)
# ─────────────────────────────────────────────

def normalize_latex(latex: str) -> str:
    """
    Strips LaTeX markup from a rule string to allow for simple regex parsing.

    This function removes formatting like '\\to', '\\lambda', and curly braces
    around exponents, and strips all whitespaces, producing a uniform format
    that is easier to process computationally.

    Args:
        latex (str): The raw LaTeX string representing an SN P system rule.

    Returns:
        str: A normalized, compressed string representation of the rule.

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
    Parses a spike token like 'a', 'a2', 'a3' into its integer exponent.

    Args:
        token (str): The spike representation token (e.g., 'a', 'a2', 'a^3').

    Returns:
        int: The integer number of spikes represented by the token.

    Examples:
        'a' → 1,  'a2' → 2,  'a10' → 10
    """
    token = token.strip()
    if token == 'a':
        return 1
    m = re.match(r'^a\^?(\d+)$', token)
    if m:
        return int(m.group(1))
    return 1  # fallback


def normalize_latex(latex: str):
    """
    Normalizes LaTeX rule strings to a consistent format for the parser.
    Handles common LaTeX commands like \\to, \\lambda, and exponents.
    """
    norm = latex.replace('\\to', '→').replace('\\lambda', 'λ').replace(' ', '')
    # Handle ^ exponents
    import re
    norm = re.sub(r'a\^\{?(\d+)\}?', r'a\1', norm)
    return norm


def _extract_spike_count(token: str):
    """
    Helper to extract numeric spike counts from 'a', 'a^n', or 'n'.
    'a' -> 1
    'a^n' -> n
    'n' -> n
    """
    token = token.strip()
    if token == 'λ' or token == '0':
        return 0
    if token == 'a':
        return 1
    # Check for 'a' followed by a number (e.g. a2 from a^2)
    if token.startswith('a'):
        num_part = token[1:]
        return int(num_part) if num_part else 1
    # Fallback for plain numbers
    try:
        return int(token)
    except ValueError:
        return 1


def parse_rule(latex: str):
    """
    Parses a single SN P rule string into structured metadata.

    The function normalizes the LaTeX input and extracts the necessary
    properties defining the rule's behavior, including consumption, production,
    delay, and whether it's a forgetting rule.

    Supported forms (after normalisation):
        a→a;0          (regex=1, consumed=1, produced=1, delay=0)
        a2/a→λ         (regex=2, consumed=1, produced=0, delay=0)
        a3/a2→a;0      (regex=3, consumed=2, produced=1, delay=0)
        a2/a→a;1       (regex=2, consumed=1, produced=1, delay=1)

    Args:
        latex (str): The raw LaTeX string representing the rule.

    Returns:
        dict: A dictionary containing rule metadata:
            - regex_spikes (int): Spikes required in the neuron to trigger the rule.
            - consumed (int): Spikes removed from the neuron when fired.
            - produced (int): Spikes sent to downstream neurons.
            - delay (int): The number of time steps before the rule finishes firing.
            - is_forgetting (bool): True if the rule produces nothing ('λ').

    Raises:
        ValueError: If the rule string cannot be parsed (e.g., lacks an arrow '→').
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
    Builds the structured rules metadata required for the simulation matrix engine.

    Iterates over all neuron nodes in the system, parses their associated rules,
    and constructs a callable list of functions that evaluate whether a rule
    can be satisfied given a neuron's current spike count.

    Args:
        nodes (list of dict): A list of dictionary objects representing the neurons.

    Returns:
        tuple:
            - rules_metadata (list of list of tuples): Aligned to neurons. Each inner list
              holds `(global_rule_index, check_fn)` pairs where `check_fn` determines
              if the rule is satisfied by a given number of spikes.
            - parsed_rules (list of dict): A flat list of parsed rule dictionaries
              (one per global rule index).
            - rule_to_neuron (list of int): A mapping from `global_rule_index` to
              its owner `neuron_idx`.
    """
    rules_metadata = []  # per-neuron list of (rule_idx, check_fn)
    parsed_rules = []    # flat list of parsed dicts
    rule_to_neuron = []  # rule_idx → neuron_idx
    global_idx = 0

    for neuron_idx, node in enumerate(nodes):
        neuron_type = node.get('neuronType', 'regular')
        raw_rules = node.get('rules', [])

        # Input neurons currently bypass rules as they are driven by stv_k trains.
        # Output neurons are allowed to have rules in theoretical models.
        if neuron_type in ('input', 'Input') or not raw_rules:
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
            neuron_rule_list.append((global_idx, check, parsed['consumed'], parsed['produced']))
            global_idx += 1

        rules_metadata.append(neuron_rule_list)

    return rules_metadata, parsed_rules, rule_to_neuron


def build_m_pi(num_rules, num_neurons, parsed_rules, rule_to_neuron, adjacency):
    """
    Builds the Spiking Transition Matrix (M_Pi).

    This matrix encodes the topology and weight distribution of the SN P system.
    Each row corresponds to a rule and each column corresponds to a neuron.
    The matrix defines how firing a rule alters the spike counts of the
    surrounding network.

    For rule `r` owned by neuron `i`:
        - `M_Pi[r, i] = -consumed` (spikes removed from the firing neuron)
        - `M_Pi[r, j] = +produced * weight` (spikes sent to downstream neuron `j`)

    Args:
        num_rules (int): Total number of rules in the system.
        num_neurons (int): Total number of neurons in the system.
        parsed_rules (list of dict): The flat list of parsed rules.
        rule_to_neuron (list of int): Mapping from rule index to neuron index.
        adjacency (dict): Adjacency list mapping `neuron_idx → [(target_idx, weight), ...]`.

    Returns:
        numpy.ndarray: The `M_Pi` matrix of shape `(num_rules, num_neurons)`.
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
    Builds the Spike Train Vector (stv_k) for a given tick in the simulation.

    For each input neuron, this function reads the bit (0 or 1) at position `tick`
    from its pre-defined spike train. It then distributes that spike to connected
    neurons, scaled by the respective edge weights.

    Args:
        tick (int): The current simulation time step (0-indexed).
        nodes (list of dict): The list of node objects in the system.
        adjacency_input (dict): Adjacency list mapping input neurons
            `input_neuron_idx → [(target_idx, weight), ...]`.

    Returns:
        tuple:
            - stv (numpy.ndarray): The `stv_k` array of length `num_neurons` representing
              the externally injected spikes at this tick.
            - inputs_active (bool): True if any input neuron still has bits remaining
              in its spike train (including the current bit).
    """
    num_neurons = len(nodes)
    stv = np.zeros(num_neurons, dtype=int)
    inputs_active = False

    for n_idx, node in enumerate(nodes):
        neuron_type = node.get('neuronType', 'regular')
        if neuron_type not in ('input', 'Input'):
            continue

        train = str(node.get('spikes', ''))
        if len(train) > 0:
            inputs_active = True
            bit = int(train[0]) if train[0] in ('0', '1') else 0
            for (target, weight) in adjacency_input.get(n_idx, []):
                stv[target] += bit * weight

    return stv, inputs_active


def build_adjacency(edges, node_id_to_idx):
    """
    Builds adjacency dictionary mappings from the raw edge list.

    Translates string-based edge connections into index-based structures to
    be used efficiently during matrix generation.

    Args:
        edges (list of dict): List of edge objects from the frontend.
        node_id_to_idx (dict): Mapping from a node's string ID to its integer index.

    Returns:
        dict: A combined adjacency mapping `neuron_idx → [(target_idx, weight)]`.
        The caller is responsible for filtering by neuron type (e.g., input vs. regular).
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
    Computes the next configuration of spike counts in the system.

    Consumption and production are conceptually separate due to delays.
    Consumption happens instantly when a rule is fired (`iv == 1`).
    Production from other neurons (and external inputs) is gated by `st_k_plus_1`
    (the openness/closure state of the neuron on the NEXT tick).

    Args:
        c_k (numpy.ndarray): Current spike counts for each neuron.
        st_k_plus_1 (numpy.ndarray): Open/closed status for neurons on the next tick.
            `1` means open (can receive spikes), `0` means closed.
        iv (numpy.ndarray): Indicator vector indicating which rules are firing.
        m_pi (numpy.ndarray): The Spiking Transition Matrix.
        stv_k (numpy.ndarray): Spike Train Vector (external inputs for this tick).

    Returns:
        numpy.ndarray: The next spike count configuration `c_{k+1}`.
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
    Computes the Indicator Vector (iv) to determine which rules produce output this tick.

    - Immediate rules (`delay == 0`): Produce output when selected (`dv == 1`).
    - Delayed rules (`delay > 0`): Produce output ONLY when their countdown expires
      (`div == 1` from a prior selection, and `dsv == 0` now). They do NOT produce
      on the tick they are selected, even if `dsv` was `0` prior.

    Args:
        dv (numpy.ndarray): The decision vector (rules selected to start this tick).
        div (numpy.ndarray): The delayed indicator vector (rules currently waiting).
        dsv (numpy.ndarray): The delay status vector (current countdown values).
        rule_delay_values (list of int): Static delay values for all rules.

    Returns:
        numpy.ndarray: The calculated Indicator Vector `iv` for the current tick.
    """
    rule_delays = np.array(rule_delay_values, dtype=int)
    # Delayed rule whose countdown has run out (was previously selected, now dsv=0)
    delayed_fires   = (div == 1) & (dsv == 0)
    # Immediate rule just selected with zero delay
    immediate_fires = (dv == 1) & (rule_delays == 0)
    return (delayed_fires | immediate_fires).astype(int)


def update_delayed_indicator(div_prev, iv, dv, dsv):
    """
    Updates the status of rules waiting to fire (Algorithm 2).

    Determines which rules should remain in a delayed/waiting state. A rule is
    delayed if it was previously delayed but hasn't fired yet, or if it was
    just selected and has a delay greater than 0.

    Args:
        div_prev (numpy.ndarray): Previous Delayed Indicator Vector.
        iv (numpy.ndarray): Current Indicator Vector (rules that just fired).
        dv (numpy.ndarray): Decision Vector (rules just selected).
        dsv (numpy.ndarray): Updated Delay Status Vector (countdowns).

    Returns:
        numpy.ndarray: The newly updated Delayed Indicator Vector `div`.
    """
    still_delayed = div_prev & np.logical_not(iv)
    newly_delayed = dv & (dsv > 0)
    return (still_delayed | newly_delayed).astype(int)


def update_delay_status(dv, dsv, rule_delay_values):
    """
    Updates the delay countdowns for all rules (Algorithm 4).

    Decrements the countdown for currently active delayed rules. If a new rule
    is selected (`dv == 1`), its countdown is reset to its initial delay value.

    Args:
        dv (numpy.ndarray): Decision Vector (rules selected this tick).
        dsv (numpy.ndarray): Current Delay Status Vector (countdowns).
        rule_delay_values (list of int): Static delay values for all rules.

    Returns:
        numpy.ndarray: The newly updated Delay Status Vector `dsv`.
    """
    new_dsv = np.maximum(0, dsv - 1)
    new_dsv = np.where(dv == 1, rule_delay_values, new_dsv)
    return new_dsv


# ─────────────────────────────────────────────
# Non-deterministic step
# ─────────────────────────────────────────────

def get_satisfied_rules(c_k, rules_metadata, div, dsv):
    """
    Determines which rules can be fired for each neuron based on current spikes.

    For each neuron, this checks which of its rules are satisfied by the
    neuron's current spike count `c_k`.
    Critically, a neuron is considered 'CLOSED' if any of its rules has an active
    delay countdown (`div[r] == 1` and `dsv[r] > 0`). Closed neurons cannot
    select new rules.

    Args:
        c_k (numpy.ndarray): Current configuration (spike counts).
        rules_metadata (list of list of tuples): Structured rule evaluation functions.
        div (numpy.ndarray): Delayed Indicator Vector.
        dsv (numpy.ndarray): Delay Status Vector.

    Returns:
        list of list of int/None: A list where each element represents the applicable
        global rule indices for a specific neuron. Returns `[None]` if no rules
        are applicable or if the neuron is closed.
    """
    satisfied = []
    for neuron_idx, neuron_rules in enumerate(rules_metadata):
        if not neuron_rules:
            satisfied.append([None])
            continue

        # Closed = neuron has active delay with dsv > 1 (still counting down).
        # On the tick it spikes (dsv == 1, about to decrement to 0), it is OPEN.
        is_closed = any(
            div[r_idx] == 1 and dsv[r_idx] > 1
            for r_idx, rc, rcons, rprod in neuron_rules
        )
        if is_closed:
            satisfied.append([None])
            continue

        spikes = c_k[neuron_idx]
        applicable = [r_idx for r_idx, r_check, r_cons, r_prod in neuron_rules if r_check(spikes)]
        satisfied.append(applicable if applicable else [None])
    return satisfied


def get_all_next_nondet(current_state, rules_metadata, m_pi, stv_k, rule_delays, adjacency, inputs_active=False):
    """
    Generates all possible next configurations considering non-determinism.

    When multiple rules can be fired within the same neuron, the SN P system
    can branch into multiple possible futures. This function evaluates all valid
    combinations of rule selections across the entire network and computes
    the resulting next states for each branch.

    Args:
        current_state (dict): The state of the system at tick `k` (includes `c_k`,
            `div`, `dsv`, `st_next`).
        rules_metadata (list of list of tuples): Structured rule evaluation logic.
        m_pi (numpy.ndarray): The Spiking Transition Matrix.
        stv_k (numpy.ndarray): Spike Train Vector (external inputs).
        rule_delays (list of int): Static delay values for all rules.

    Returns:
        list of dict: A list representing all valid next state objects. Each
        state contains updated `c_k`, `dsv`, `div`, rule contributions, and
        information about whether the system has halted.
    """
    num_rules = m_pi.shape[0]
    num_neurons = len(rules_metadata)

    # st_next: a neuron is closed (st_next=0) ONLY if it has an active delay
    # with dsv > 1 (still counting down). On the tick it spikes (dsv==1,
    # about to decrement to 0), it is OPEN and can receive spikes.
    st_next = np.ones(num_neurons, dtype=int)
    for neuron_idx, neuron_rules in enumerate(rules_metadata):
        for r_idx, rc, rcons, rprod in neuron_rules:
            if current_state['div'][r_idx] == 1 and current_state['dsv'][r_idx] > 1:
                st_next[neuron_idx] = 0
                break

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

        new_dsv = update_delay_status(dv, current_state['dsv'], rule_delays)
        iv = get_indicator_vector(dv, current_state['div'], new_dsv, rule_delays)

        # This-tick openness: closed only if
        #   (a) neuron has active delay with dsv > 1 (still counting), OR
        #   (b) neuron just selected a NEW delayed rule this tick
        # Neurons that spike this tick (dsv was 1, now 0) are OPEN.
        this_tick_st_next = np.ones(num_neurons, dtype=int)
        for n_idx, n_rules in enumerate(rules_metadata):
            for r_idx, rc, rcons, rprod in n_rules:
                if current_state['div'][r_idx] == 1 and current_state['dsv'][r_idx] > 1:
                    this_tick_st_next[n_idx] = 0
                    break
            else:
                # Check if a NEW delayed rule was just selected
                for r_idx, rc, rcons, rprod in n_rules:
                    if dv[r_idx] == 1 and rule_delays[r_idx] > 0:
                        this_tick_st_next[n_idx] = 0
                        break

        # Consumption: spikes are removed immediately on selection (dv)
        consumption = np.zeros(num_neurons, dtype=int)
        for n_idx, n_rules in enumerate(rules_metadata):
            for r_idx, r_check, r_cons, r_prod in n_rules:
                if dv[r_idx] == 1:
                    consumption[n_idx] -= r_cons

        # Production: spikes arrive from fired rules (iv) and external inputs (stv_k)
        # Blocked if the neuron is closed in THIS tick
        production = np.zeros(num_neurons, dtype=int)
        for r_idx, fired in enumerate(iv):
            if fired == 1:
                source_neuron_idx = -1
                # Find which neuron this rule belongs to
                for n_idx, n_rules in enumerate(rules_metadata):
                    if any(r[0] == r_idx for r in n_rules):
                        source_neuron_idx = n_idx
                        break
                if source_neuron_idx >= 0:
                    produced_count = 0
                    for r in rules_metadata[source_neuron_idx]:
                        if r[0] == r_idx:
                            produced_count = r[3]
                            break
                    for (target_idx, weight) in adjacency.get(source_neuron_idx, []):
                        production[target_idx] += produced_count * weight

        new_c = current_state['c_k'] + consumption + (production + stv_k) * this_tick_st_next
        new_c = np.maximum(0, new_c) # Safety

        new_div = update_delayed_indicator(current_state['div'], iv, dv, new_dsv)

        # rule_contribution: net change per neuron
        rule_contribution = np.dot(iv, m_pi)

        all_possible_next.append({
            'c_k': new_c,
            'dsv': new_dsv,
            'div': new_div,
            'rule_contribution': rule_contribution,
            'iv': iv,
            'dv': dv
        })

    # ── Halting detection ──────────────────────────────────────────────────
    # The system has halted when ALL of the following hold:
    #   1. No more external input is coming (inputs_active is False).
    #   2. No delay countdowns are pending in any next state (dsv == 0).
    #   3. Every possible next config is a fixed-point (c_k and div unchanged).
    all_halted = False

    if not inputs_active:
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
    Performs an iterative depth-first search for valid system configurations.

    Used primarily in the 'String Judge' mode, this iteratively applies
    non-deterministic rule transitions up to a specified `time_limit`. It injects
    bits from `string_val` one at a time into the input neuron.

    Args:
        initial_config (dict): The starting state dictionary of the SN P system.
        time_limit (int): Maximum depth/ticks to explore.
        string_val (str): The bitstring to feed into the input neuron over time.
        rules_metadata (list of list of tuples): Structured rule evaluation logic.
        m_pi (numpy.ndarray): The Spiking Transition Matrix.
        rule_delays (list of int): Static delay values for all rules.

    Returns:
        list of tuple: A list of `(tick, configuration_dict)` representing
        all reachable states throughout the depth-first search up to the limit.
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