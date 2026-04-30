# app.py
# ─────────────────────────────────────────────────────────────
# Flask application entry point.
#
# REST API
# ────────
# POST /api/new        – start a new game episode
# POST /api/move       – move the agent to an adjacent cell
# POST /api/auto_step  – let the KB agent make one decision
# POST /api/reveal     – reveal ground-truth hazard positions
# ─────────────────────────────────────────────────────────────

import uuid
from flask import Flask, jsonify, request, render_template
from Game import WumpusGame

app = Flask(__name__)

# In-memory game sessions keyed by UUID string.
# For production, replace with a proper session store (Redis, DB, etc.).
_games: dict[str, WumpusGame] = {}


# ── HTML entry point ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API helpers ──────────────────────────────────────────────

def _get_game(data: dict):
    """Retrieve a game by ID or return a 404-style error dict."""
    game = _games.get(data.get("game_id", ""))
    if game is None:
        return None, (jsonify({"error": "Game not found. Call /api/new first."}), 404)
    return game, None


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


# ── Routes ───────────────────────────────────────────────────

@app.route("/api/new", methods=["POST"])
def api_new():
    """
    Body  : { "rows": int, "cols": int }
    Returns: { "game_id": str, "state": GameState }
    """
    data = request.get_json(force=True)
    rows = _clamp(int(data.get("rows", 5)), 3, 10)
    cols = _clamp(int(data.get("cols", 5)), 3, 10)

    game_id = str(uuid.uuid4())[:8]
    game = WumpusGame(rows, cols)
    _games[game_id] = game

    return jsonify({"game_id": game_id, "state": game.get_state()})


@app.route("/api/move", methods=["POST"])
def api_move():
    """
    Body  : { "game_id": str, "r": int, "c": int }
    Returns: GameState
    """
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    r = int(data.get("r", 0))
    c = int(data.get("c", 0))
    return jsonify(game.move(r, c))


@app.route("/api/auto_step", methods=["POST"])
def api_auto_step():
    """
    Body  : { "game_id": str }
    Returns: GameState
    """
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    return jsonify(game.auto_step())


@app.route("/api/reveal", methods=["POST"])
def api_reveal():
    """
    Body  : { "game_id": str }
    Returns: { "pits": [...], "wumpus": [...] | null, "gold": [...] }
    """
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    return jsonify(game.reveal_truth())


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    # debug=True is fine for development; disable in production.
    app.run(debug=True, port=5000)
