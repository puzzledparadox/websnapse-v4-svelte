import numpy as np
from fastapi import FastAPI, WebSocket
from engine import get_all_next_nondet, get_configs_iterative
import json

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "WebSnapse v4 Simulation Engine Online"}

@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Receive the system state and rules from the Svelte client
            data = await websocket.receive_text()
            message = json.loads(data)

            # 2. Check message type
            if message.get('type') == 'judge':
                string_val = message['string']
                time_limit = message['timeLimit']
                
                state = {
                    'c_k': np.array(message['state']['c_k']),
                    'div': np.array(message['state']['div']),
                    'dsv': np.array(message['state']['dsv']),
                    'st_next': np.array(message['state']['st_next'])
                }
                m_pi = np.array(message['m_pi'])
                rule_delays = np.array(message['rule_delays'])
                
                # Mock rule: consume 2 spikes
                mock_rules = [
                    [(0, lambda c: c[0] >= 2)], # Rule 0: requires at least 2 spikes
                    [],
                    []
                ]
                
                reachable = get_configs_iterative(state, time_limit, string_val, mock_rules, m_pi, rule_delays)
                
                # Check the state at the maximum time reached
                # Accepted if the final state has 0 spikes in neuron 0
                max_t = max([r[0] for r in reachable]) if reachable else 0
                final_states = [r[1] for r in reachable if r[0] == max_t]
                
                is_accepted = any(fs['c_k'][0] == 0 for fs in final_states)
                
                await websocket.send_json({
                    "type": "judge_result",
                    "string": string_val,
                    "status": "accepted" if is_accepted else "rejected"
                })
                continue

            # 3. Regular simulation flow
            state = {
                'c_k': np.array(message['state']['c_k']),
                'div': np.array(message['state']['div']),
                'dsv': np.array(message['state']['dsv']),
                'st_next': np.array(message['state']['st_next'])
            }
            m_pi = np.array(message['m_pi'])
            stv_k = np.array(message['stv_k'])
            rule_delays = np.array(message['rule_delays'])

            # 4. Mocking rules_metadata for the test
            # For now, we mock the Even Positive Integer Generator behavior.
            mock_rules = [
                [(0, lambda c: True), (1, lambda c: True)], # Neuron 1 has 2 rules satisfied
                [], # Neuron 2
                [] # Neuron 3
            ]

            # 5. Calculate branches using the iterative engine (assuming a single step wrapper here for simulation)
            from engine import get_all_next_nondet
            results = get_all_next_nondet(state, mock_rules, m_pi, stv_k, rule_delays)
            
            # Convert NumPy results back to lists so JSON can handle them
            output_possibilities = []
            for res in results:
                output_possibilities.append({
                    'c_k': res['c_k'].tolist(),
                    'div': res['div'].tolist(),
                    'dsv': res['dsv'].tolist()
                })

            await websocket.send_json({
                "tick": message['tick'] + 1,
                "possibilities": output_possibilities
            })
    except Exception as e:
        print(f"Server error: {e}")