# WebSnapse v4
### A High-Performance Svelte 5 Visualization and Simulation Engine for Spiking Neural P Systems

**WebSnapse v4** represents the next generation of Spiking Neural P (SN P) system simulators. Moving beyond the legacy Vue-based *WebSnapse Reloaded*, this version leverages the cutting-edge **Svelte 5** framework and a high-performance **FastAPI** backend to provide a robust, reactive, and matrix-based simulation environment for theoretical computer science research.

---

## Abstract

Spiking Neural P systems are a class of distributed and parallel computing models inspired by the way biological neurons communicate through spikes. WebSnapse v4 transitions from traditional object-oriented simulation patterns to a **reactive matrix-based architecture**. By utilizing the Spiking Transition Matrix ($M_{\Pi}$), the engine achieves high-speed execution and deterministic/non-deterministic state exploration, all while maintaining a sleek, modern interface.

## Core Functionalities

### 1. High-Speed Matrix Engine
At the heart of WebSnapse v4 is a NumPy-powered backend that simulates SN P systems using matrix multiplication. The firing of rules and spike distribution are calculated via the product of the Spiking Transition Matrix ($M_{\Pi}$) and the current configuration vector, ensuring O(1) or O(n) complexity relative to the system size.

### 2. Interactive Designer
A full-suite designer toolbar built on **XYFlow (Svelte Flow)** allows researchers to:
- **Select**: Inspect and modify neuron properties.
- **Node**: Add new neurons (Regular, Input, or Output).
- **Edge**: Establish synapses with weighted connections.
- **Clear**: Reset the workspace for new experiments.

### 3. Guided State Exploration
Handle non-determinism with ease. When multiple rule combinations are valid, the engine presents a **Branch Modal**, allowing the user to select the computation path or explore all possibilities in a guided manner.

### 4. Theoretical Judger
A batch-processing tool for formal language theory. The **String Judge** allows users to input a set of bitstrings and verify if the current SN P system accepts or rejects them based on defined halting conditions.

### 5. Research Templates
An integrated **Gallery** containing pre-built templates of famous SN P systems, such as:
- Binary Adders
- Bit Comparators
- Even Parity Checkers
- 2N Generators

---

## Tech Stack

- **Frontend**: [Svelte 5](https://svelte.dev/) (Runes) for granular reactivity.
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python) for asynchronous matrix computation.
- **Graph Engine**: [XYFlow](https://xyflow.com/) (Svelte Flow) for interactive canvas management.
- **Mathematics**: [KaTeX](https://katex.org/) for beautiful LaTeX rule rendering.
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) for a modern, responsive UI.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup
1. Navigate to the `server` directory: `cd server`
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. Install dependencies: `pip install fastapi uvicorn numpy`
5. Start the engine: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to the `client` directory: `cd client`
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`
4. Access the UI at `http://localhost:5173`

---

## Academic Attribution

This project is the terminal thesis work of **Arturo Miguel V. Saquilayan** in partial fulfillment of the requirements for the **CS 199 (Special Problems II)** course at the **University of the Philippines Diliman**. 

**Adviser**: Francis George C. Cabarle
**Department**: Department of Computer Science, College of Engineering.

---

## License

MIT
