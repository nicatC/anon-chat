package com.anonchat;

import javax.swing.*;
import java.awt.*;

class MessagePanel extends JPanel {
    private final JTextArea area = new JTextArea();

    MessagePanel() {
        setLayout(new BorderLayout());
        area.setEditable(false);
        add(new JScrollPane(area), BorderLayout.CENTER);
    }
    void addLine(String s) {
        area.append(s+"\n");
        area.setCaretPosition(area.getDocument().getLength());
    }
}
