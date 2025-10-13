"""
Adaptador de red para Tic-Tac-Toe GUI (versión unificada).
Permite conectar la interfaz gráfica (Tkinter o Pygame) con el servidor TCP.
Envía y recibe mensajes JSON terminados en salto de línea (\n).
Soporta callbacks para manejar acciones específicas del servidor.
"""

import socket
import threading
import json
import traceback
from typing import Optional, Callable, Dict


class NetworkAdapter:
    def __init__(self, host: str = "127.0.0.1", port: int = 5000,
                 on_message: Optional[Callable] = None,
                 deliver: Optional[Callable] = None,
                 debug: bool = False):
        """
        host: dirección del servidor
        port: puerto del servidor
        on_message: callback global para cada mensaje recibido
        deliver: función opcional para ejecutar callbacks en el hilo de la GUI (ej. root.after)
        debug: si True, muestra logs en consola
        self.network
        """
        self.host = host
        self.port = port
        self.on_message = on_message
        self.deliver = deliver
        self.debug = debug
        self.sock = None
        self.recv_thread = None
        self.running = False
        self.lock = threading.Lock()
        self.callbacks: Dict[str, Callable] = {}

        # Conexión automática al crearse
        self.connect(self.host, self.port)

    # --------------------------------------------------------
    # Conexión / desconexión
    # --------------------------------------------------------
    def connect(self, host: str, port: int, timeout: float = 5.0) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.settimeout(None)
            with self.lock:
                self.sock = s
                self.running = True

            # Hilo receptor
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()

            if self.debug:
                print(f"[adapter] Conectado a {host}:{port}")
            return True
        except Exception as e:
            if self.debug:
                print("[adapter] Error de conexión:", e)
            return False

    def disconnect(self):
        with self.lock:
            self.running = False
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
        if self.debug:
            print("[adapter] Desconectado")

    # --------------------------------------------------------
    # Envío de mensajes
    # --------------------------------------------------------
    def send(self, obj: dict):
        data = json.dumps(obj) + "\n"
        with self.lock:
            s = self.sock
            if not s:
                if self.debug:
                    print("[adapter] No conectado")
                return False
            try:
                s.sendall(data.encode("utf-8"))
                if self.debug:
                    print("[adapter] ->", obj)
                return True
            except Exception as e:
                if self.debug:
                    print("[adapter] Error al enviar:", e)
                return False

    # --------------------------------------------------------
    # Atajos de protocolo
    # --------------------------------------------------------
    def register(self, username: str, password: str):
        return self.send({"action": "register", "username": username, "password": password})

    def login(self, username: str, password: str):
        return self.send({"action": "login", "username": username, "password": password})

    def list_online(self):
        return self.send({"action": "list"})

    def invite(self, from_user: str, target: str):
        return self.send({"action": "invite", "from": from_user, "target": target})

    def invite_response(self, from_user: str, target: str, accepted: bool):
        return self.send({
            "action": "invite_response",
            "from": from_user,
            "target": target,
            "accepted": accepted
        })

    def move(self, game_id: str, player: str, x: int, y: int):
        return self.send({
            "action": "move",
            "game_id": game_id,
            "player": player,
            "x": x,
            "y": y
        })

    def logout(self):
        return self.send({"action": "logout"})

    # --------------------------------------------------------
    # Callbacks personalizados por acción
    # --------------------------------------------------------
    def on(self, action: str, fn: Callable):
        self.callbacks[action] = fn

    def _call_cb(self, action: str, msg: dict):
        fn = self.callbacks.get(action)
        if not fn:
            # Si no hay callback específico, usa el global
            if self.on_message:
                try:
                    if self.deliver:
                        self.deliver(self.on_message, msg)
                    else:
                        self.on_message(msg)
                except Exception:
                    traceback.print_exc()
            elif self.debug:
                print("[adapter] sin callback para acción:", action, msg)
            return
        try:
            if self.deliver:
                self.deliver(fn, msg)
            else:
                fn(msg)
        except Exception:
            traceback.print_exc()

    # --------------------------------------------------------
    # Recepción de datos
    # --------------------------------------------------------
    def _recv_loop(self):
        buf = ""
        try:
            while True:
                with self.lock:
                    if not self.running or not self.sock:
                        break
                    s = self.sock
                data = s.recv(4096)
                if not data:
                    if self.debug:
                        print("[adapter] conexión cerrada por el servidor")
                    break
                buf += data.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        if self.debug:
                            print("[adapter] JSON inválido:", line)
                        continue
                    action = obj.get("action", "_unknown")
                    if self.debug:
                        print("[adapter] <-", obj)
                    self._call_cb(action, obj)
        except Exception as e:
            if self.debug:
                print("[adapter] Error en recv_loop:", e)
        finally:
            self._call_cb("_disconnected", {"action": "_disconnected"})
            with self.lock:
                try:
                    if self.sock:
                        self.sock.close()
                except Exception:
                    pass
                self.sock = None
                self.running = False
