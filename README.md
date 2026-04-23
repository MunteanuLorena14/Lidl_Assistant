# The Seed Project

A Python application combining AI assistant and SQLite database for Lidl inventory management.

## Setup

1. Clone the repository
2. Create a virtual environment:
   python -m venv virtual_env
   
3. Activate it:
   virtual_env\Scripts\activate
   
4. Install dependencies:
   pip install -r requirements.txt
   
5. Create a .env file based on .env.example and add your Gemini API key

## Run

# Terminal UI
python main.py

# Graphical UI
python ui.py

## Project Structure

- main.py — terminal menu interface
- ui.py — graphical interface (PySide6)
- llm.py — Gemini AI integration
- memory.py — conversation memory
- database.py — SQLite database