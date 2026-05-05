export class SimulationService {
    socket: WebSocket | null = null;
    // Rune for tracking if we are connected
    isConnected = $state(false);
    // Rune for storing current possibilities from the engine
    possibilities = $state([]);

    connect() {
        this.socket = new WebSocket('ws://localhost:8000/ws/simulate');

        this.socket.onopen = () => {
            this.isConnected = true;
            console.log('Connected to WebSnapse Simulation Engine');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Update reactive state with new possibilities
            this.possibilities = data.possibilities;
        };

        this.socket.onclose = () => {
            this.isConnected = false;
        };
    }

    sendState(payload: any) {
        if (this.socket && this.isConnected) {
            this.socket.send(JSON.stringify(payload));
        }
    }
}

export const simulation = new SimulationService();