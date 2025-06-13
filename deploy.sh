#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create a systemd service file
sudo tee /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Job Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot 