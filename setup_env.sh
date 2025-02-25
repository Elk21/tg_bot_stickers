#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install python-telegram-bot Pillow requests openai
echo "Environment setup complete. To activate, run: source venv/bin/activate" 