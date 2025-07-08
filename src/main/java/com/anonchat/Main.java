package com.anonchat;

import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.net.Socket;
import java.util.Scanner;
import java.util.function.Consumer;

public class Main {

    private static boolean connected   = false;
    private static String BRIDGE_HOST;
    private static int    BRIDGE_PORT;

    public static void main(String[] args) {
        
        if(args.length >=2){
            BRIDGE_HOST = args[0];
            BRIDGE_PORT = Integer.parseInt(args[1]);
        } else {
            BRIDGE_HOST = "127.0.0.1";
            BRIDGE_PORT = 5555;
        }
        SwingUtilities.invokeLater(() -> {
            createGui();
        });
    }

    private static void createGui() {
        JFrame frame = new JFrame("Chat App");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(900, 620);

        JLabel title = new JLabel("Anonymous Encrypted Chat App", SwingConstants.CENTER);
        title.setFont(new Font("Arial", Font.BOLD, 20));
        title.setBorder(BorderFactory.createEmptyBorder(10, 0, 10, 0));
        frame.add(title, BorderLayout.NORTH);


        MessagePanel messages = new MessagePanel();
        UsersPanel   users    = new UsersPanel();     
        startListener(messages, users);                

        JMenuBar bar = new JMenuBar();
        JMenu modeMenu = new JMenu("Mode");

        modeMenu.add(createModeItem("set as gateway", "gateway"));
        modeMenu.add(createModeItem("set as client", "client"));

        bar.add(modeMenu);
        JMenu file = new JMenu("File");

        file.add(menu("Generate keys", () -> {
            String resp = sendToPython("{\"cmd\":\"gen_keys\",\"payload\":{}}");
            JOptionPane.showMessageDialog(frame, "python:" + resp);
        }));

        file.add(menu("Connect", () -> {
            if (connected == true){
                JOptionPane.showMessageDialog(frame, "youre already connected");
                return;
            }else{

                String nick = JOptionPane.showInputDialog(frame, "take a nickname:");
                if (nick == null || nick.isBlank()) return;
                
                String json = String.format(
                    "{\"cmd\":\"connect\",\"payload\":{\"nick\":\"%s\"}}",
                    makeJsonSafe(nick));
                String resp = sendToPython(json);
                JOptionPane.showMessageDialog(frame, "python:" + resp);

                connected   = true;
            } 
            
        }));

        file.add(menu("Disconnect", () -> {
            if (connected == false){
                JOptionPane.showMessageDialog(frame, "youre not even connected");
                return;
            }else{
                String resp = sendToPython("{\"cmd\":\"disconnect\",\"payload\":{}}");
                JOptionPane.showMessageDialog(frame, "python:" + resp);
                connected = false;
            }
            
        }));

        bar.add(file);

        JMenu help = new JMenu("Help");
        help.add(menu("about", () -> JOptionPane.showMessageDialog(frame,"""
                Nicat Caliskan
                20210702113
                """)));

        
        bar.add(help);
        frame.setJMenuBar(bar);

        file.addSeparator();
        file.add(menu("Exit", () -> System.exit(0)));
        

        // mesaj gonderme
        Consumer<String> onSend = txt -> {
            if (connected == false) {
                JOptionPane.showMessageDialog(frame, "you should first connect to the network");
                return;
            }else{
                messages.addLine("me: " + txt);
                String json = "{\"cmd\":\"chat\",\"payload\":{\"msg\":\"" + makeJsonSafe(txt) + "\"}}";
                sendToPython(json);
            }
            
        };



        frame.add(messages, BorderLayout.CENTER);
        frame.add(new InputBar(onSend), BorderLayout.SOUTH);
        frame.add(users,    BorderLayout.EAST);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    private static void startListener(MessagePanel chatArea, UsersPanel userList) {
        Thread thread = new Thread(() -> {
            try (Socket socket = new Socket(BRIDGE_HOST, BRIDGE_PORT);
                PrintWriter writer = new PrintWriter(socket.getOutputStream(), true);
                BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {

                writer.println("{\"cmd\":\"subscribe\",\"payload\":{}}");
                reader.readLine(); // "status":ok cevabı

                String line;
                while ((line = reader.readLine()) != null) 
                {
                    if(line.startsWith("CHAT|")){
                        String[] splited = line.split("\\|", 3);
                        chatArea.addLine(splited[1] + ": " + splited[2]);
                    }
                    else if(line.startsWith("HELLO|"))
                    {
                        String nick = line.split("\\|", 2)[1];
                        chatArea.addLine("* " + nick + " joined *");
                    } 
                    else if(line.startsWith("QUIT|"))
                    {
                        String nick = line.split("\\|", 2)[1];
                        chatArea.addLine("* " + nick + " left *");
                    }else if(line.startsWith("USER_ADD|")) {
                        String nick = line.split("\\|", 2)[1];
                        userList.addUser(nick);
                    }else if(line.startsWith("USER_DEL|")) {
                        String nick = line.split("\\|", 2)[1];
                        userList.removeUser(nick);
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        });

        thread.setName("bridge-listener");
        thread.start();
    }

    //founded
    private static JMenuItem menu(String text, Runnable action) {
        JMenuItem item = new JMenuItem(text);
        item.addActionListener(e -> action.run());
        return item;
    }

    //founded 
    private static String makeJsonSafe(String string){
        return string.replace("\"", "\\\"");
    } 
    
    private static String sendToPython(String json) {
        try (Socket sock = new Socket(BRIDGE_HOST, BRIDGE_PORT);
             PrintWriter out = new PrintWriter(sock.getOutputStream(), true);
             Scanner     in  = new Scanner(sock.getInputStream())) {

            out.println(json);
            return in.nextLine();

        } catch (Exception exception1) {
            exception1.printStackTrace();
            return String.format("{\"status\":\"error\",\"message\":\"%s\"}", exception1.getMessage());
        }
    }
    private static JMenuItem createModeItem(String title, String mode) {
            
        JMenuItem item = new JMenuItem(title);

        item.addActionListener(e -> {
            var payload = String.format("{\"cmd\":\"set_mode\",\"payload\":{\"mode\":\"%s\"}}", mode);
            var resp = sendToPython(payload);
            JOptionPane.showMessageDialog(null, "Bridge response:\n" + resp);
        });

        return item;
    }
}
