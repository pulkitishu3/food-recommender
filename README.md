# Food Recommender System

A Python-based food recommendation web application built with Flask and SQLite. The app allows users to get personalized food recommendations based on their preferences.

## Features
- Interactive web interface for exploring food options.
- Backend powered by **Flask**.
- Data stored locally in an **SQLite** database (`food_hub.db`).

## Prerequisites
- Python 3.x
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pulkitishu3/food-recommender.git
   cd food-recommender
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the Flask development server:
```bash
python app.py
```

Then, open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

## Project Structure
- `app.py`: Main Flask application.
- `template/`: HTML templates (`index.html`, `result.html`).
- `static/`: Static assets (`style.css`, `app.js`).
- `food_hub.db`: SQLite database containing food data.
- `requirements.txt`: Python package dependencies.
