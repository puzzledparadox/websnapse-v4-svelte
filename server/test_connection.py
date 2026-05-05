import asyncio
import websockets
import json
import numpy as np

async def test_simulation():
    uri = "ws://localhost:8000/ws/simulate"
    async with websockets.connect(uri) as websocket:
        # Mocking the Even Positive Integer Generator system
        # n1 has 2 spikes, n2 has 1, n3 has 3
        test_payload = {
            "tick": 0,
            "state": {
                "c_k": [2, 1, 3],
                "div": [0, 0],
                "dsv": [0, 0],
                "st_next": [1, 1, 1]
            },
            "m_pi": [[-1, 1, 1], [-2, 0, 0]], # Rule 1 and Rule 2 indices
            "stv_k": [0, 0, 0],
            "rule_delays": [1, 0], # Rule 1 has delay 1, Rule 2 has 0
            "rules": [] # In a real run, lambda checks would be passed here
        }

        print("Sending system state to server...")
        await websocket.send(json.dumps(test_payload))

        response = await websocket.recv()
        result = json.loads(response)

        print(f"\nTick: {result['tick']}")
        print(f"Possibilities found: {len(result['possibilities'])}")

        for i, pos in enumerate(result['possibilities']):
            print(f"Branch {i+1} Spikes: {pos['c_k']}")
            print(f"Branch {i+1} Delay Status: {pos['dsv']}")

asyncio.run(test_simulation())