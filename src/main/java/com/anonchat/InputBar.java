package com.anonchat;

import javax.swing.*;
import java.awt.*;
import java.util.function.Consumer;

class InputBar extends JPanel {
    InputBar(Consumer<String> onSend) {
        setLayout(new BorderLayout(8,0));

        JLabel label = new JLabel("Enter a message:");
        label.setFont(new Font("Arial", Font.BOLD, 14));
        JTextField field = new JTextField();
        JButton send   = new JButton("send");

        add(label, BorderLayout.WEST);
        add(field, BorderLayout.CENTER);
        add(send,  BorderLayout.EAST);

        Runnable fire = () -> {
            String txt = field.getText().trim();
            if (!txt.isEmpty()) {
                onSend.accept(txt);
                field.setText("");
            }
        };
        send.addActionListener(e -> fire.run());

        field.addActionListener(e -> fire.run());
    }
}