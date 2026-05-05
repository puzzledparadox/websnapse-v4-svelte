import numpy as np
from fastapi import FastAPI, WebSocket
from engine import get_all_next_nondet
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

            # 2. Cast lists to NumPy arrays for Matrix Math
            state = {
                'c_k': np.array(message['state']['c_k']),
                'div': np.array(message['state']['div']),
                'dsv': np.array(message['state']['dsv']),
                'st_next': np.array(message['state']['st_next'])
            }
            m_pi = np.array(message['m_pi'])
            stv_k = np.array(message['stv_k'])
            rule_delays = np.array(message['rule_delays'])

            # 3. Mocking rules_metadata for the test
            # For now, we mock the Even Positive Integer Generator behavior.
            mock_rules = [
                [(0, lambda c: True), (1, lambda c: True)], # Neuron 1 has 2 rules satisfied
                [], # Neuron 2
                [] # Neuron 3
            ]

            # 4. Calculate branches using the iterative engine
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