// TicTacToeClient.java
import java.io.*;
import java.net.*;
import java.util.Scanner;
import org.json.*;

public class TicTacToeClient {
    private Socket socket;
    private BufferedReader in;
    private PrintWriter out;
    private String username;
    private String gameId;
    private String mySymbol;

    public TicTacToeClient(String host, int port) throws Exception {
        socket = new Socket(host, port);
        in = new BufferedReader(new InputStreamReader(socket.getInputStream()));
        out = new PrintWriter(socket.getOutputStream(), true);
        // start listener thread
        new Thread(this::listen).start();
    }

    private void listen() {
        try {
            String line;
            while ((line = in.readLine()) != null) {
                JSONObject msg = new JSONObject(line);
                handleMessage(msg);
            }
        } catch (Exception e) {
            System.out.println("Conexión cerrada o error: " + e.getMessage());
        }
    }

    private void handleMessage(JSONObject msg) {
        String action = msg.optString("action", "");
        switch (action) {
            case "register_ok":
                System.out.println("[SERVER] Registro exitoso. Ya puedes logearte.");
                break;
            case "register_fail":
                System.out.println("[SERVER] Registro falló: " + msg.optString("reason"));
                break;
            case "login_ok":
                System.out.println("[SERVER] Login OK.");
                break;
            case "login_fail":
                System.out.println("[SERVER] Login FALLÓ: " + msg.optString("reason"));
                break;
            case "list":
                System.out.println("[SERVER] Usuarios online: " + msg.optJSONArray("users"));
                break;
            case "online":
                System.out.println("[SERVER] Actualización usuarios online: " + msg.optJSONArray("users"));
                break;
            case "invite":
                System.out.println("[INVITATION] Invitación de: " + msg.optString("from"));
                System.out.println("Escribe 'accept " + msg.optString("from") + "' o 'reject " + msg.optString("from") + "'");
                break;
            case "invite_response":
                System.out.println("[INVITE RESP] " + msg.optString("from") + " responded, accepted=" + msg.optBoolean("accepted"));
                break;
            case "start":
                this.gameId = msg.optString("game_id");
                this.mySymbol = msg.optString("player");
                System.out.println("[GAME START] game_id=" + gameId + " you=" + mySymbol + " opponent=" + msg.optString("opponent"));
                break;
            case "update":
                System.out.println("[UPDATE] Turn: " + msg.optString("turn"));
                printBoard(msg.optJSONArray("board"));
                break;
            case "end":
                System.out.println("[GAME END] Winner: " + msg.optString("winner"));
                printBoard(msg.optJSONArray("board"));
                this.gameId = null;
                this.mySymbol = null;
                break;
            case "error":
                System.out.println("[SERVER ERROR] " + msg.optString("reason"));
                break;
            default:
                System.out.println("[MSG] " + msg.toString());
        }
    }

    private void printBoard(JSONArray board) {
        System.out.println("Tablero:");
        for (int i = 0; i < board.length(); i++) {
            JSONArray row = board.getJSONArray(i);
            System.out.print("|");
            for (int j = 0; j < row.length(); j++) {
                System.out.print(" " + row.getString(j) + " |");
            }
            System.out.println();
        }
    }

    // Sending helper
    private void send(JSONObject o) {
        out.println(o.toString());
    }

    // CLI loop
    public void cliLoop() {
        Scanner sc = new Scanner(System.in);
        System.out.println("Comandos: register <user> <pass> | login <user> <pass> | list | invite <user> | accept <user> | reject <user> | move x y");
        while (true) {
            String line = sc.nextLine();
            if (line == null) break;
            String[] parts = line.trim().split("\\s+");
            if (parts.length == 0) continue;
            String cmd = parts[0];
            try {
                if (cmd.equalsIgnoreCase("register") && parts.length >= 3) {
                    JSONObject o = new JSONObject();
                    o.put("action","register");
                    o.put("username", parts[1]);
                    o.put("password", parts[2]);
                    send(o);
                } else if (cmd.equalsIgnoreCase("login") && parts.length >= 3) {
                    JSONObject o = new JSONObject();
                    o.put("action","login");
                    o.put("username", parts[1]);
                    o.put("password", parts[2]);
                    this.username = parts[1];
                    send(o);
                } else if (cmd.equalsIgnoreCase("list")) {
                    JSONObject o = new JSONObject();
                    o.put("action","list");
                    send(o);
                } else if (cmd.equalsIgnoreCase("invite") && parts.length >= 2) {
                    JSONObject o = new JSONObject();
                    o.put("action","invite");
                    o.put("from", this.username);
                    o.put("target", parts[1]);
                    send(o);
                    System.out.println("Invitación enviada a " + parts[1]);
                } else if (cmd.equalsIgnoreCase("accept") && parts.length >= 2) {
                    JSONObject o = new JSONObject();
                    o.put("action","invite_response");
                    o.put("from", this.username);      // quien responde
                    o.put("target", parts[1]);         // quien invitó originalmente
                    o.put("accepted", true);
                    send(o);
                } else if (cmd.equalsIgnoreCase("reject") && parts.length >= 2) {
                    JSONObject o = new JSONObject();
                    o.put("action","invite_response");
                    o.put("from", this.username);
                    o.put("target", parts[1]);
                    o.put("accepted", false);
                    send(o);
                } else if (cmd.equalsIgnoreCase("move") && parts.length >= 3) {
                    if (this.gameId == null || this.mySymbol == null) {
                        System.out.println("No estás en partida.");
                        continue;
                    }
                    int x = Integer.parseInt(parts[1]);
                    int y = Integer.parseInt(parts[2]);
                    JSONObject o = new JSONObject();
                    o.put("action","move");
                    o.put("game_id", this.gameId);
                    o.put("player", this.mySymbol);
                    o.put("x", x);
                    o.put("y", y);
                    send(o);
                } else if (cmd.equalsIgnoreCase("quit")) {
                    break;
                } else {
                    System.out.println("Comando desconocido");
                }
            } catch (Exception e) {
                System.out.println("Error procesando comando: " + e.getMessage());
            }
        }
        sc.close();
        try { socket.close(); } catch (Exception e) {}
    }

    public static void main(String[] args) throws Exception {
        String host = "127.0.0.1";
        int port = 5000;
        if (args.length >= 1) host = args[0];
        if (args.length >= 2) port = Integer.parseInt(args[1]);
        TicTacToeClient c = new TicTacToeClient(host, port);
        c.cliLoop();
    }
}
