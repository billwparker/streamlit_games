# Streamlit Games

A collection of interactive games built using Streamlit.

## Getting Started

1. Clone this repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Run the application:
```
streamlit run Home.py
```

## Available Games

- **Asteroids**: Navigate your spaceship through an asteroid field, shoot lasers to destroy asteroids, and avoid collisions.
- **Minesweeper**: Classic puzzle game where you reveal cells and avoid hidden mines. Available in both emoji and ASCII display modes.
- **Stratego**: Strategic board game where you capture the opponent's flag using pieces with different ranks.

## Project Structure

- `Home.py`: Main landing page for the games collection
- `pages/`: Directory containing individual game pages
  - `🚀_Asteroids.py`: The Asteroids game implementation
  - `💣_Minesweeper.py`: The Minesweeper game implementation
  - `🎯_Stratego.py`: The Stratego game implementation

## Adding New Games

To add a new game, create a new Python file in the `pages` directory with an emoji prefix (e.g. `🐍_Snake.py`).