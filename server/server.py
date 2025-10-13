
import socket
import threading
import json
import hashlib
import uuid
import os
import traceback
import time

USERS_FILE = "users.json"
HOST = "0.0.0.0"
PORT = 5000

lock = threading.Lock()

# In-memory state
# users: username -> password_hash (loaded at startup)
users = {}
# clients: username -> {conn, addr, wfile, fileno}
clients = {}
# conns: fileno -> username
conns = {}
# games
games = {}

# -------------------- Persistence helpers --------------------

def load_users_file():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Warning: could not load users file:", e)
        return {}


def persist_users_atomic(snapshot):
    # write to temp then replace to avoid partial writes
    try:
        tmp = USERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)
        os.replace(tmp, USERS_FILE)
    except Exception as e:
        print("Error persisting users file:", e)


def hash_password(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# -------------------- Game helpers --------------------

def empty_board():
    return [[" " for _ in range(3)] for _ in range(3)]


def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != " ":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    return None


def is_full(board):
    return all(board[i][j] != " " for i in range(3) for j in range(3))

# -------------------- Networking helpers --------------------

def send_json_writer(wfile, obj):
    try:
        wfile.write(json.dumps(obj) + "\n")
        wfile.flush()
    except Exception as e:
        # writing failed; caller should handle connection cleanup
        print("Warning: send_json_writer failed:", e)


def safe_send_to_user(username, obj):
    try:
        info = clients.get(username)
        if not info:
            return False
        send_json_writer(info["wfile"], obj)
        return True
    except Exception as e:
        print("safe_send_to_user error:", e)
        return False


def broadcast_to_players(game_id, obj):
    g = games.get(game_id)
    if not g:
        return
    with lock:
        for u in list(g["players"]):
            safe_send_to_user(u, obj)

# -------------------- Notifications --------------------

def notify_online():
    with lock:
        online = list(clients.keys())
    for u in online:
        safe_send_to_user(u, {"action": "online", "users": online})

# -------------------- Client handler --------------------

def handle_client(conn, addr):
    fileno = conn.fileno()
    rfile = conn.makefile(mode="r", encoding="utf-8", newline="")
    wfile = conn.makefile(mode="w", encoding="utf-8", newline="")
    username = None
    print(f"[INFO] New connection {addr} fileno={fileno}")
    try:
        while True:
            line = rfile.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                send_json_writer(wfile, {"action": "error", "reason": "invalid_json"})
                continue

            action = msg.get("action")
            # ------------------ REGISTER ------------------
            if action == "register":
                user = msg.get("username")
                pw = msg.get("password")
                if not user or not pw:
                    send_json_writer(wfile, {"action": "register_fail", "reason": "missing fields"})
                    continue
                with lock:
                    if user in users:
                        send_json_writer(wfile, {"action": "register_fail", "reason": "user exists"})
                        continue
                    users[user] = hash_password(pw)
                    snapshot = users.copy()
                # persist outside lock
                persist_users_atomic(snapshot)
                send_json_writer(wfile, {"action": "register_ok"})

            # ------------------ LOGIN ------------------
            elif action == "login":
                user = msg.get("username")
                pw = msg.get("password")
                if not user or not pw:
                    send_json_writer(wfile, {"action": "login_fail", "reason": "missing fields"})
                    continue
                with lock:
                    expected = users.get(user)
                if not expected or expected != hash_password(pw):
                    send_json_writer(wfile, {"action": "login_fail", "reason": "invalid creds"})
                    continue

                # login ok: register client mapping, kick previous session if needed
                with lock:
                    prev = clients.get(user)
                    if prev:
                        try:
                            prev_conn = prev.get("conn")
                            prev_w = prev.get("wfile")
                            send_json_writer(prev_w, {"action": "kicked", "reason": "login elsewhere"})
                            try:
                                prev_conn.shutdown(socket.SHUT_RDWR)
                            except Exception:
                                pass
                            try:
                                prev_conn.close()
                            except Exception:
                                pass
                            try:
                                del conns[prev.get("fileno")]
                            except Exception:
                                pass
                        except Exception:
                            pass
                    clients[user] = {"conn": conn, "addr": addr, "wfile": wfile, "fileno": fileno}
                    conns[fileno] = user
                    username = user
                send_json_writer(wfile, {"action": "login_ok"})
                notify_online()

            # ------------------ LIST ------------------
            elif action == "list":
                with lock:
                    online = list(clients.keys())
                send_json_writer(wfile, {"action": "list", "users": online})

            # ------------------ INVITE ------------------
            elif action == "invite":
                target = msg.get("target")
                from_user = msg.get("from")
                if not target or not from_user:
                    send_json_writer(wfile, {"action": "error", "reason": "missing fields"})
                    continue
                with lock:
                    info = clients.get(target)
                if info:
                    send_json_writer(info["wfile"], {"action": "invite", "from": from_user})
                    send_json_writer(wfile, {"action": "invite_sent", "target": target})
                else:
                    send_json_writer(wfile, {"action": "error", "reason": "target offline"})

            # ------------------ INVITE RESPONSE ------------------
            elif action == "invite_response":
                target = msg.get("target")
                from_user = msg.get("from")
                accepted = msg.get("accepted", False)
                if not target or not from_user:
                    send_json_writer(wfile, {"action": "error", "reason": "missing fields"})
                    continue
                with lock:
                    info = clients.get(target)
                if info:
                    send_json_writer(info["wfile"], {"action": "invite_response", "from": from_user, "accepted": accepted})
                    if accepted:
                        gid = str(uuid.uuid4())[:8]
                        board = empty_board()
                        players = [target, from_user]
                        games[gid] = {"players": players, "board": board, "turn": "X"}
                        # notify both
                        send_json_writer(clients[target]["wfile"], {"action": "start", "game_id": gid, "player": "X", "opponent": from_user})
                        send_json_writer(clients[from_user]["wfile"], {"action": "start", "game_id": gid, "player": "O", "opponent": target})
                        broadcast_to_players(gid, {"action": "update", "game_id": gid, "board": board, "turn": "X"})
                else:
                    send_json_writer(wfile, {"action": "error", "reason": "target offline"})

            # ------------------ MOVE ------------------
            elif action == "move":
                gid = msg.get("game_id")
                player_symbol = msg.get("player")
                x = msg.get("x")
                y = msg.get("y")
                user = conns.get(fileno)
                if not gid or gid not in games:
                    send_json_writer(wfile, {"action": "error", "reason": "invalid game"})
                    continue
                g = games[gid]
                p1, p2 = g["players"]
                symbol_map = {p1: "X", p2: "O"}
                if user not in symbol_map or symbol_map[user] != player_symbol:
                    send_json_writer(wfile, {"action": "error", "reason": "not your symbol"})
                    continue
                if g["turn"] != player_symbol:
                    send_json_writer(wfile, {"action": "error", "reason": "not your turn"})
                    continue
                if not (isinstance(x, int) and isinstance(y, int) and 0 <= x <= 2 and 0 <= y <= 2):
                    send_json_writer(wfile, {"action": "error", "reason": "invalid coords"})
                    continue
                if g["board"][x][y] != " ":
                    send_json_writer(wfile, {"action": "error", "reason": "cell occupied"})
                    continue
                g["board"][x][y] = player_symbol
                winner = check_winner(g["board"])
                if winner:
                    broadcast_to_players(gid, {"action": "end", "game_id": gid, "winner": winner, "board": g["board"]})
                    try:
                        del games[gid]
                    except Exception:
                        pass
                elif is_full(g["board"]):
                    broadcast_to_players(gid, {"action": "end", "game_id": gid, "winner": "draw", "board": g["board"]})
                    try:
                        del games[gid]
                    except Exception:
                        pass
                else:
                    g["turn"] = "O" if g["turn"] == "X" else "X"
                    broadcast_to_players(gid, {"action": "update", "game_id": gid, "board": g["board"], "turn": g["turn"]})

            # ------------------ LOGOUT ------------------
            elif action == "logout":
                if username:
                    with lock:
                        try:
                            del conns[clients[username]["fileno"]]
                        except Exception:
                            pass
                        try:
                            del clients[username]
                        except Exception:
                            pass
                    send_json_writer(wfile, {"action": "logout_ok"})
                    notify_online()
                    break

            else:
                send_json_writer(wfile, {"action": "error", "reason": "unknown action"})

    except Exception as e:
        print("Excepción en handle_client:", e)
        traceback.print_exc()
    finally:
        # cleanup: remove mapping if present
        try:
            if username:
                with lock:
                    try:
                        del conns[clients[username]["fileno"]]
                    except Exception:
                        pass
                    try:
                        del clients[username]
                    except Exception:
                        pass
                notify_online()
        except Exception:
            pass
        try:
            rfile.close()
        except Exception:
            pass
        try:
            wfile.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        print(f"[INFO] Connection closed {addr}")

# -------------------- Main --------------------

def main():
    global users
    users = load_users_file()
    print(f"[INFO] Loaded {len(users)} users")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(50)
    print(f"[INFO] Server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("[INFO] Shutting down server")
        # persist users on shutdown
        try:
            with lock:
                snapshot = users.copy()
            persist_users_atomic(snapshot)
        except Exception as e:
            print("Error persisting users on shutdown:", e)
    finally:
        server.close()

if __name__ == "__main__":
    main()

