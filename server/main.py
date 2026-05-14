import numpy as np
from fastapi import FastAPI, WebSocket
from engine import (
    build_rules_metadata,
    build_m_pi,
    build_adjacency,
    compute_stv_k,
    get_all_next_nondet,
    parse_rule,
)
import json

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "WebSnapse v4 Simulation Engine Online"}


def _prepare_system(message):
    """
    Common helper: take a frontend message containing nodes + edges
    and return everything the engine needs for one step.
    """
    raw_nodes = message['nodes']      # [{id, neuronType, spikes, rules}, ...]
    raw_edges = message['edges']      # [{source, target, weight}, ...]
    tick = message.get('tick', 0)

    # Map node id → sequential index
    node_ids = [n['id'] for n in raw_nodes]
    node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    num_neurons = len(raw_nodes)

    # Build adjacency from edge list
    adjacency = build_adjacency(raw_edges, node_id_to_idx)

    # Build rules_metadata, parsed_rules, rule_to_neuron
    rules_metadata, parsed_rules, rule_to_neuron = build_rules_metadata(raw_nodes)
    num_rules = len(parsed_rules)

    # Build M_Pi matrix
    m_pi = build_m_pi(num_rules, num_neurons, parsed_rules, rule_to_neuron, adjacency)

    # Build rule_delays vector
    rule_delays = np.array([pr['delay'] for pr in parsed_rules], dtype=int) if parsed_rules else np.array([], dtype=int)

    # Build stv_k for this tick (input neuron spike trains → target neurons)
    stv_k = compute_stv_k(tick, raw_nodes, adjacency)

    # Build current configuration vectors
    c_k = np.zeros(num_neurons, dtype=int)
    for i, n in enumerate(raw_nodes):
        ntype = n.get('neuronType', 'regular')
        spikes_val = n.get('spikes', 0)
        if ntype in ('input', 'Input'):
            c_k[i] = 0  # input neurons feed via stv_k, not c_k
        elif isinstance(spikes_val, str):
            # Output neurons store spike trains as strings like "001"
            # Their c_k is the accumulated count of 1s
            c_k[i] = spikes_val.count('1')
        else:
            c_k[i] = int(spikes_val)

    # Delay vectors — sized to num_rules
    div_raw = message.get('div', [0] * num_rules)
    dsv_raw = message.get('dsv', [0] * num_rules)
    # Ensure correct length
    div = np.zeros(num_rules, dtype=int)
    dsv = np.zeros(num_rules, dtype=int)
    for i in range(min(len(div_raw), num_rules)):
        div[i] = int(div_raw[i])
    for i in range(min(len(dsv_raw), num_rules)):
        dsv[i] = int(dsv_raw[i])

    # Status vector: a neuron is CLOSED (st_next=0) if any of its rules
    # is currently in a delay countdown (div[r]=1 and dsv[r]>0).
    # Closed neurons cannot receive spikes this tick.
    st_next = np.ones(num_neurons, dtype=int)
    rule_idx = 0
    for neuron_idx, node in enumerate(raw_nodes):
        ntype = node.get('neuronType', 'regular')
        if ntype in ('input', 'Input', 'output', 'Output'):
            continue
        rule_count = len(node.get('rules', []))
        for r in range(rule_count):
            global_r = rule_idx + r
            if global_r < num_rules and div[global_r] == 1:
                st_next[neuron_idx] = 0
                break
        rule_idx += rule_count

    state = {
        'c_k': c_k,
        'div': div,
        'dsv': dsv,
        'st_next': st_next,
    }

    return state, rules_metadata, m_pi, stv_k, rule_delays, node_ids


@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # ── Reset ──
            if message.get('type') == 'reset':
                await websocket.send_json({
                    "type": "reset_ack",
                    "status": "Engine synchronized and reset."
                })
                continue

            # ── Regular simulation step ──
            if message.get('type') == 'step':
                state, rules_metadata, m_pi, stv_k, rule_delays, node_ids = _prepare_system(message)

                results = get_all_next_nondet(state, rules_metadata, m_pi, stv_k, rule_delays)

                output_possibilities = []
                for res in results:
                    output_possibilities.append({
                        'c_k': res['c_k'].tolist(),
                        'div': res['div'].tolist(),
                        'dsv': res['dsv'].tolist(),
                        'rule_contribution': res['rule_contribution'].tolist(),
                        'iv': res['iv'].tolist(),
                        'dv': res['dv'].tolist(),
                        'is_halted': res.get('is_halted', False)
                    })

                await websocket.send_json({
                    "type": "step_result",
                    "tick": message.get('tick', 0) + 1,
                    "possibilities": output_possibilities,
                    "node_ids": node_ids,
                })
                continue

            # ── Fallback: treat as legacy step (backward compat) ──
            # If no 'type' field, try to handle old-format messages
            await websocket.send_json({
                "type": "error",
                "message": "Unknown message type. Send {type: 'step', ...} or {type: 'reset'}."
            })

    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()