# 🎮 Wumpus Logic Agent

A sophisticated implementation of the **Wumpus World** game featuring an **intelligent Knowledge-Based Agent** that uses propositional logic and resolution refutation to navigate a dangerous cave system and hunt the Wumpus.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🌟 Overview

This project implements the classic **Wumpus World** problem from artificial intelligence, where an agent must:

- **Navigate** a grid-based cave system
- **Avoid hazards**: pits and the deadly Wumpus
- **Collect gold** using logical reasoning
- **Make intelligent decisions** based on percepts (stench, breeze, glitter)

The agent employs a **Knowledge Base** with propositional logic and **Resolution Refutation** to derive safe cells and make optimal moves.

---

## ✨ Features

### Intelligent Agent System
- **Propositional Logic Engine**: Full CNF (Conjunctive Normal Form) implementation
- **Resolution Refutation**: Logical proof system to determine safe cells and hazard locations
- **Knowledge Base**: Persistent storage of deduced facts about the world
- **Autonomous Decision Making**: Agent automatically explores and hunts for gold

### Game Features
- **Configurable Grid Size**: Play on any board dimensions
- **Random Hazard Placement**: Pits, Wumpus, and gold positioned randomly
- **Real-time Percepts**: Stench (Wumpus nearby), Breeze (pit nearby), Glitter (gold present)
- **Two Play Modes**:
  - **Manual Control**: Direct the agent's movements
  - **Autonomous Mode**: Let the AI agent decide next actions

### Web Interface
- **Interactive Dashboard**: Visual grid representation of the cave
- **Live Status Updates**: Real-time game state and percept display
- **Move History**: Track agent decisions and reasoning
- **Game Controls**: Start, move, auto-play, and restart options

---

## 📁 Project Structure

```
Wumpus_Project/
├── app.py                    # Flask REST API server
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── LICENSE                   # MIT License
│
├── Game/
│   ├── __init__.py
│   ├── wumpus_game.py        # Core game logic & state management
│   ├── knowledge_base.py     # Propositional logic KB & resolution refutation
│   └── utils.py              # Helper functions (pathfinding, parsing)
│
├── Templates/
│   └── index.html            # Web UI
│
└── Static/
    ├── css/
    │   └── style.css         # Styling
    └── js/
        └── main.js           # Client-side logic
```

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/AyaanHassanShah/Wumpus_Logic_Agent.git
   cd Wumpus_Project
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎯 Usage

### Running the Application

1. **Start the Flask server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to: `http://localhost:5000`

3. **Play the game**
   - Click "New Game" to start an episode
   - Use "Move" to manually control the agent
   - Click "Auto Step" to let the AI make a decision
   - Click "Reveal" to show all hazard locations

---

## 📡 API Reference

### REST Endpoints

#### `POST /api/new`
Start a new game episode.

**Request Body:**
```json
{
  "rows": 4,
  "cols": 4
}
```

**Response:**
```json
{
  "game_id": "uuid-string",
  "state": { /* game state */ }
}
```

---

#### `POST /api/move`
Move the agent in a specified direction.

**Request Body:**
```json
{
  "game_id": "uuid-string",
  "direction": "north" | "south" | "east" | "west"
}
```

**Response:**
```json
{
  "state": { /* updated game state */ },
  "message": "Moved north"
}
```

---

#### `POST /api/auto_step`
Let the KB agent make one autonomous decision.

**Request Body:**
```json
{
  "game_id": "uuid-string"
}
```

**Response:**
```json
{
  "state": { /* updated game state */ },
  "decision": "Moved to safe cell"
}
```

---

#### `POST /api/reveal`
Reveal all hazard positions (for debugging/validation).

**Request Body:**
```json
{
  "game_id": "uuid-string"
}
```

**Response:**
```json
{
  "pits": [[1, 2], [2, 3]],
  "wumpus": [3, 1],
  "gold": [2, 2]
}
```

---

## 🧠 How the AI Agent Works

### 1. Knowledge Base Foundation
The agent maintains a propositional logic knowledge base where:
- `P_r_c` = "Pit at row r, column c"
- `W_r_c` = "Wumpus at row r, column c"
- `B_r_c` = "Breeze in cell r, c" (indicates pit nearby)
- `S_r_c` = "Stench in cell r, c" (indicates Wumpus nearby)

### 2. Inference Engine
Using **Resolution Refutation**, the agent:
1. Converts all rules to CNF (Conjunctive Normal Form)
2. Negates queries and searches for contradictions
3. Derives facts about safe and dangerous cells

### 3. Decision Making
The agent uses the KB to:
- Identify guaranteed safe cells
- Narrow down Wumpus/pit locations
- Plan optimal paths to gold or unexplored areas
- Avoid known hazards

### 4. Exploration Strategy
- **Phase 1**: Explore all safe cells while gathering information
- **Phase 2**: Use logic to deduce remaining hazard positions
- **Phase 3**: Plan path to gold
- **Phase 4**: Execute retrieval and escape

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, JavaScript |
| Logic Engine | Custom propositional logic implementation |
| Inference | Resolution Refutation algorithm |

---

## 📚 Key Algorithms

### Resolution Refutation
- Converts clauses to CNF
- Applies resolution rule to derive new clauses
- Detects contradictions (empty clause derivation)
- Proves queries through reductio ad absurdum

### Breadth-First Search (BFS)
- Used for pathfinding to gold or safe cells
- Finds shortest unvisited path

### Propositional Logic Clause Generation
- Automatically generates logical rules from percepts
- Manages clause implications and simplifications

---

## 🎮 Game Rules

### Hazards
- **Pits**: Agent dies instantly on contact
- **Wumpus**: Agent dies on contact (can only kill with arrow if implemented)
- **Gold**: Objective - collect and return to start

### Percepts
- **Stench (S)**: Wumpus is in an adjacent cell
- **Breeze (B)**: Pit is in an adjacent cell
- **Glitter (G)**: Gold is in current cell
- **Scream**: Wumpus was killed (if implemented)
- **Bump**: Agent hit a wall (tried to move out of bounds)

### Scoring
- +1000 points for collecting gold
- -1 point per step taken
- -10000 points for dying
- Game ends when agent dies, gets gold, or gives up

---

## 🔮 Future Enhancements

- [ ] Arrow mechanism to kill the Wumpus
- [ ] Multi-agent scenarios
- [ ] Larger grid optimization (with heuristics)
- [ ] Advanced pathfinding algorithms (A*)
- [ ] Game statistics and analytics dashboard
- [ ] Difficulty levels
- [ ] Mobile-responsive UI improvements

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📖 References

- Russell, S. J., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
- Wumpus World: A classic AI problem from the above textbook
- Propositional Logic: Foundations of knowledge representation and reasoning

---

## 👤 Author

**Ayaan Hassan Shah**
- GitHub: [@AyaanHassanShah](https://github.com/AyaanHassanShah)
- Project: [Wumpus Logic Agent](https://github.com/AyaanHassanShah/Wumpus_Logic_Agent)

---

## ⭐ Show Your Support

If you find this project interesting or useful, please consider:
- Starring the repository ⭐
- Sharing with others 🤝
- Contributing improvements 💡

---

**Happy hunting in the Wumpus World! 🎯**