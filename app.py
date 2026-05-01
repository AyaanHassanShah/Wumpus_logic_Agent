# app.py
# ─────────────────────────────────────────────────────────────
# Flask application entry point (Render-ready)
# ─────────────────────────────────────────────────────────────

import uuid
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from Game import WumpusGame

app = Flask(__name__)

# ✅ Enable CORS (IMPORTANT for Vercel frontend)
CORS(app)

# In-memory game sessions
_games: dict[str, WumpusGame] = {}


# ── HTML entry point ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API helpers ──────────────────────────────────────────────

def _get_game(data: dict):
    """Retrieve a game by ID or return error."""
    game = _games.get(data.get("game_id", ""))
    if game is None:
        return None, (jsonify({"error": "Game not found. Call /api/new first."}), 404)
    return game, None


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


# ── Routes ───────────────────────────────────────────────────

@app.route("/api/new", methods=["POST"])
def api_new():
    data = request.get_json(force=True)

    rows = _clamp(int(data.get("rows", 5)), 3, 10)
    cols = _clamp(int(data.get("cols", 5)), 3, 10)

    game_id = str(uuid.uuid4())[:8]
    game = WumpusGame(rows, cols)
    _games[game_id] = game

    return jsonify({
        "game_id": game_id,
        "state": game.get_state()
    })


@app.route("/api/move", methods=["POST"])
def api_move():
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    r = int(data.get("r", 0))
    c = int(data.get("c", 0))

    return jsonify(game.move(r, c))


@app.route("/api/auto_step", methods=["POST"])
def api_auto_step():
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    return jsonify(game.auto_step())


@app.route("/api/reveal", methods=["POST"])
def api_reveal():
    data = request.get_json(force=True)
    game, err = _get_game(data)
    if err:
        return err

    return jsonify(game.reveal_truth())


# ── Entry point (Render compatible) ──────────────────────────

if __name__ == "__main__":
    # Render requires host + dynamic port
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
