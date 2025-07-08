package com.anonchat;

import javax.swing.*;
import java.awt.*;
import java.util.HashSet;
import java.util.Set;

class UsersPanel extends JPanel {

    private final DefaultListModel<String> model = new DefaultListModel<>();
    private final JList<String> list            = new JList<>(model);
    private final Set<String>    knownNicks     = new HashSet<>();

    UsersPanel() {
        setLayout(new BorderLayout());
        list.setFixedCellWidth(120);
        add(new JScrollPane(list), BorderLayout.CENTER);
        setBorder(BorderFactory.createTitledBorder("Online Users"));
    }
    void addUser(String nick) {
        if (knownNicks.add(nick)) {
            SwingUtilities.invokeLater(() -> model.addElement(nick));
        }
    }

    void removeUser(String nick) {
        if (knownNicks.remove(nick)) {
            SwingUtilities.invokeLater(() -> model.removeElement(nick));
        }
    }
}
