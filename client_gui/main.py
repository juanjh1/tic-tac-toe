import tkinter as tk
from tkinter import messagebox
from network_adapter import NetworkAdapter
import threading
import tkinter
import traceback
import sys

# Sobreescribimos el manejador de excepciones de Tkinter
def report_callback_exception(self, exc, val, tb):
    print("\n============================")
    print("⚠️  EXCEPCIÓN EN TKINTER DETECTADA")
    traceback.print_exception(exc, val, tb)
    print("============================\n")
    input("Presiona ENTER para cerrar...")
    sys.exit(1)

tkinter.Tk.report_callback_exception = report_callback_exception

# ==========================
# CONFIGURACIÓN DEL CLIENTE
# ==========================
SERVER_HOST = "127.0.0.1"   # cambia si tu servidor está en otra PC
SERVER_PORT = 5000


# ==========================
# CLASE PRINCIPAL DEL GUI
# ==========================
class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe Online")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        # Variables del juego
        self.player_symbol = None
        self.opponent = None
        self.game_id = None
        self.turn = None
        self.board = [[" " for _ in range(3)] for _ in range(3)]

        # Adaptador de red
        self.network = NetworkAdapter(SERVER_HOST, SERVER_PORT, self.handle_server_message, debug=True)

        # Pantallas
        self.show_login_screen()

    # ==========================
    # SECCIÓN LOGIN
    # ==========================
    def show_login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Tic Tac Toe Online", font=("Arial", 20, "bold")).pack(pady=20)
        tk.Label(self.root, text="Usuario:").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        tk.Label(self.root, text="Contraseña:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Registrar", command=self.register).pack(pady=5)
        tk.Button(self.root, text="Iniciar Sesión", command=self.login).pack(pady=5)

    def register(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Error", "Debe ingresar usuario y contraseña")
            return
        self.network.send_json({"action": "register", "username": user, "password": pw})

    def login(self):
        user = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()
        if not user or not pw:
            messagebox.showwarning("Error", "Debe ingresar usuario y contraseña")
            return
        self.username = user
        self.network.send_json({"action": "login", "username": user, "password": pw})

    # ==========================
    # SECCIÓN LOBBY
    # ==========================
    def show_lobby(self):
        self.clear_screen()
        tk.Label(self.root, text=f"Conectado como {self.username}", font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Actualizar lista", command=self.request_list).pack(pady=5)

        self.users_listbox = tk.Listbox(self.root)
        self.users_listbox.pack(pady=5, fill="both", expand=True)

        tk.Button(self.root, text="Invitar a jugar", command=self.invite_selected_user).pack(pady=5)
        tk.Button(self.root, text="Cerrar sesión", command=self.logout).pack(pady=5)

        self.request_list()

    def request_list(self):
        self.network.send_json({"action": "list"})

    def invite_selected_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Seleccione un usuario.")
            return
        target = self.users_listbox.get(selection[0])
        if target == self.username:
            messagebox.showinfo("Info", "No puede invitarse a sí mismo.")
            return
        self.network.send_json({"action": "invite", "from": self.username, "target": target})
        messagebox.showinfo("Invitación", f"Invitación enviada a {target}")

    def logout(self):
        self.network.send_json({"action": "logout"})
        self.show_login_screen()

    # ==========================
    # SECCIÓN JUEGO
    # ==========================
    def show_game_screen(self):
        self.clear_screen()
        tk.Label(self.root, text=f"Jugando contra {self.opponent}", font=("Arial", 14)).pack(pady=10)
        self.status_label = tk.Label(self.root, text=f"Turno: {self.turn}", font=("Arial", 12))
        self.status_label.pack(pady=5)

        self.buttons = []
        board_frame = tk.Frame(self.root)
        board_frame.pack()

        for i in range(3):
            row = []
            for j in range(3):
                btn = tk.Button(board_frame, text=" ", font=("Arial", 24), width=4, height=2,
                                 command=lambda x=i, y=j: self.make_move(x, y))
                btn.grid(row=i, column=j)
                row.append(btn)
            self.buttons.append(row)

    def make_move(self, x, y):
        if self.board[x][y] != " ":
            return
        if self.turn != self.player_symbol:
            messagebox.showinfo("Info", "No es tu turno.")
            return
        self.network.send_json({
            "action": "move",
            "game_id": self.game_id,
            "player": self.player_symbol,
            "x": x,
            "y": y
        })

    def update_board(self):
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text=self.board[i][j])
        self.status_label.config(text=f"Turno: {self.turn}")

    # ==========================
    # MANEJO DE RESPUESTAS SERVIDOR
    # ==========================
    def handle_server_message(self, msg):
        action = msg.get("action")

        if action == "register_ok":
            messagebox.showinfo("Registro", "Registro exitoso. Inicie sesión.")
        elif action == "register_fail":
            messagebox.showerror("Error", msg.get("reason", "Registro fallido."))
        elif action == "login_ok":
            self.show_lobby()
        elif action == "login_fail":
            messagebox.showerror("Error", msg.get("reason", "Login incorrecto."))
        elif action == "list":
            users = msg.get("users", [])
            self.users_listbox.delete(0, tk.END)
            for u in users:
                self.users_listbox.insert(tk.END, u)
        elif action == "invite":
            from_user = msg.get("from")
            res = messagebox.askyesno("Invitación", f"{from_user} te invita a jugar. ¿Aceptar?")
            self.network.send_json({
                "action": "invite_response",
                "from": self.username,
                "target": from_user,
                "accepted": res
            })
        elif action == "invite_response":
            accepted = msg.get("accepted", False)
            from_user = msg.get("from")
            if accepted:
                messagebox.showinfo("Invitación", f"{from_user} aceptó tu invitación.")
            else:
                messagebox.showinfo("Invitación", f"{from_user} rechazó tu invitación.")
        elif action == "start":
            self.player_symbol = msg["player"]
            self.opponent = msg["opponent"]
            self.game_id = msg["game_id"]
            self.show_game_screen()
        elif action == "update":
            self.board = msg["board"]
            self.turn = msg["turn"]
            self.update_board()
        elif action == "end":
            self.board = msg["board"]
            self.update_board()
            winner = msg["winner"]
            if winner == "draw":
                messagebox.showinfo("Juego terminado", "Empate.")
            elif winner == self.player_symbol:
                messagebox.showinfo("Juego terminado", "¡Ganaste!")
            else:
                messagebox.showinfo("Juego terminado", "Perdiste.")
            self.show_lobby()
        elif action == "error":
            print("[ERROR SERVER]", msg.get("reason"))

    # ==========================
    # UTILIDADES
    # ==========================
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()


# ==========================
# MAIN LOOP
# ==========================
def main():
    root = tk.Tk()
    app = TicTacToeGUI(root)
    threading.Thread(target=root.mainloop, daemon=True).start()


if __name__ == "__main__":
    import traceback
    import sys

    try:
        print("[INFO] Iniciando GUI Tic-Tac-Toe...")
        main()
    except Exception as e:
        print("\n[ERROR FATAL EN MAIN]:", e)
        print("----------- TRAZA COMPLETA -----------")
        traceback.print_exc()
        print("-------------------------------------")
        input("\nPresiona ENTER para salir...")
        sys.exit(1)














