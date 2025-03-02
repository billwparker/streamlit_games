import streamlit as st
import numpy as np
import time
import random
from dataclasses import dataclass
from typing import List, Tuple, Set

# Initialize Streamlit page
st.set_page_config(
    page_title="Minesweeper",
    page_icon="💣",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Now import and initialize the autorefresh for timer updates
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=1000, key="minesweeper_autorefresh")  # 1 second refresh

# Game constants
BEGINNER = {"rows": 9, "cols": 9, "mines": 10}
INTERMEDIATE = {"rows": 16, "cols": 16, "mines": 40}
EXPERT = {"rows": 16, "cols": 30, "mines": 99}

# Emoji display characters
EMOJI_DISPLAY = {
    "hidden": "🟦",
    "flag": "🚩",
    "mine": "💣",
    "explosion": "💥",
    "0": "⬜",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣"
}

@dataclass
class MinesweeperGame:
    rows: int
    cols: int
    mines: int
    grid: np.ndarray = None  # Will store mine values (-1 for mines, 0-8 for number of adjacent mines)
    revealed: np.ndarray = None  # Boolean grid to track revealed cells
    flagged: np.ndarray = None  # Boolean grid to track flagged cells
    game_over: bool = False
    game_won: bool = False
    start_time: float = None
    end_time: float = None
    first_move: bool = True
    
    def __post_init__(self):
        """Initialize the game grid after object creation"""
        self.grid = np.zeros((self.rows, self.cols), dtype=int)
        self.revealed = np.zeros((self.rows, self.cols), dtype=bool)
        self.flagged = np.zeros((self.rows, self.cols), dtype=bool)
        self.start_time = time.time()
        self.first_move = True
    
    def place_mines(self, first_x: int, first_y: int):
        """Place mines randomly, ensuring first click is not a mine"""
        # Create a flattened list of all possible cell indices
        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        
        # Remove cells around first click (3x3 area)
        safe_zone = []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                safe_r, safe_c = first_y + dr, first_x + dc
                if 0 <= safe_r < self.rows and 0 <= safe_c < self.cols:
                    safe_zone.append((safe_r, safe_c))
        
        # Remove safe zone from possible mine locations
        for cell in safe_zone:
            if cell in all_cells:
                all_cells.remove(cell)
        
        # Randomly select cells for mines
        mine_cells = random.sample(all_cells, min(self.mines, len(all_cells)))
        
        # Place mines
        for r, c in mine_cells:
            self.grid[r, c] = -1
        
        # Calculate adjacent mine counts
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r, c] != -1:  # Skip cells with mines
                    mine_count = 0
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            if dr == 0 and dc == 0:
                                continue  # Skip the cell itself
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr, nc] == -1:
                                mine_count += 1
                    self.grid[r, c] = mine_count
    
    def reveal(self, x: int, y: int) -> bool:
        """
        Reveal a cell. Returns False if the game is over, True otherwise.
        """
        # If first move, place mines to ensure first click is safe
        if self.first_move:
            self.place_mines(x, y)
            self.first_move = False
        
        # Can't reveal flagged cells
        if self.flagged[y, x]:
            return True
        
        # Already revealed
        if self.revealed[y, x]:
            return True
        
        # Clicked on a mine - game over
        if self.grid[y, x] == -1:
            self.revealed[y, x] = True
            self.game_over = True
            self.end_time = time.time()
            return False
        
        # Reveal this cell
        self.revealed[y, x] = True
        
        # If it's a 0, reveal all adjacent cells
        if self.grid[y, x] == 0:
            self.reveal_adjacent(x, y)
        
        # Check for win
        if np.sum(~self.revealed) == self.mines:
            self.game_won = True
            self.game_over = True
            self.end_time = time.time()
            # Flag all remaining mines on win
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid[r, c] == -1 and not self.flagged[r, c]:
                        self.flagged[r, c] = True
        
        return True
    
    def reveal_adjacent(self, x: int, y: int):
        """Recursively reveal adjacent cells for a 0 value cell"""
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue  # Skip the cell itself
                nr, nc = y + dr, x + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if not self.revealed[nr, nc] and not self.flagged[nr, nc]:
                        self.revealed[nr, nc] = True
                        if self.grid[nr, nc] == 0:
                            self.reveal_adjacent(nc, nr)
    
    def toggle_flag(self, x: int, y: int):
        """Toggle flag on a cell"""
        if not self.revealed[y, x]:  # Can only flag unrevealed cells
            self.flagged[y, x] = not self.flagged[y, x]
    
    def chord(self, x: int, y: int):
        """
        Chord action: when clicking on a revealed number where all mines are correctly flagged,
        reveal all adjacent cells
        """
        # Check if the cell is revealed and has a number
        if not self.revealed[y, x] or self.grid[y, x] <= 0:
            return  # Can only chord on revealed numbered cells
        
        # Count adjacent flags
        adjacent_flags = 0
        adjacent_cells = []
        
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue  # Skip the cell itself
                nr, nc = y + dr, x + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    adjacent_cells.append((nr, nc))
                    if self.flagged[nr, nc]:
                        adjacent_flags += 1
        
        # If the number of flags equals the cell value, reveal all unflagged and unrevealed adjacent cells
        if adjacent_flags == self.grid[y, x]:
            for nr, nc in adjacent_cells:
                if not self.flagged[nr, nc] and not self.revealed[nr, nc]:
                    # Use the reveal method to handle possible cascades and game over conditions
                    self.reveal(nc, nr)
    
    def get_game_duration(self):
        """Return elapsed game time in seconds"""
        end = self.end_time if self.end_time else time.time()
        return int(end - self.start_time)

# Initialize session state for game
if 'minesweeper_game' not in st.session_state:
    st.session_state.minesweeper_game = None
    st.session_state.difficulty = "beginner"  # Default difficulty
    st.session_state.last_refresh_time = time.time()
    st.session_state.show_rules = False  # Default rules visibility

def create_new_game(difficulty):
    """Create a new game with the specified difficulty"""
    if difficulty == "beginner":
        config = BEGINNER
    elif difficulty == "intermediate":
        config = INTERMEDIATE
    else:
        config = EXPERT
    
    st.session_state.minesweeper_game = MinesweeperGame(**config)
    st.session_state.difficulty = difficulty

def render_cell(col, row_idx, col_idx, game: MinesweeperGame):
    """Render a single cell in the game grid"""
    cell_value = game.grid[row_idx, col_idx] if game.grid is not None else 0
    is_revealed = game.revealed[row_idx, col_idx] if game.revealed is not None else False
    is_flagged = game.flagged[row_idx, col_idx] if game.flagged is not None else False
    
    if is_revealed:
        if cell_value == -1:  # Mine
            if game.game_over and not game.game_won:
                cell_display = EMOJI_DISPLAY["explosion"]  # Exploded mine
            else:
                cell_display = EMOJI_DISPLAY["mine"]  # Regular mine
        else:
            cell_display = EMOJI_DISPLAY[str(cell_value)]  # Number
    elif is_flagged:
        cell_display = EMOJI_DISPLAY["flag"]
    else:
        cell_display = EMOJI_DISPLAY["hidden"]
    
    # Use a clickable button to represent each cell
    cell_key = f"cell_{row_idx}_{col_idx}"
    
    if col.button(cell_display, key=cell_key, disabled=game.game_over):
        handle_cell_click(row_idx, col_idx)

def handle_cell_click(row_idx, col_idx):
    """Handle clicks on the Minesweeper grid"""
    game = st.session_state.minesweeper_game
    
    # Check if shift key is pressed (for flagging)
    shift_pressed = st.session_state.get('shift_pressed', False)
    
    # Get cell state for debugging
    cell_value = game.grid[row_idx, col_idx] if game.grid is not None else 0
    is_revealed = game.revealed[row_idx, col_idx] if game.revealed is not None else False
    is_flagged = game.flagged[row_idx, col_idx] if game.flagged is not None else False
    
    if shift_pressed:
        # Flag mode
        game.toggle_flag(col_idx, row_idx)
    elif is_revealed and cell_value > 0:
        # This is a chord action - clicking on a revealed number
        # Count adjacent flags for debugging
        adjacent_flags = 0
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row_idx + dr, col_idx + dc
                if 0 <= nr < game.rows and 0 <= nc < game.cols and game.flagged[nr, nc]:
                    adjacent_flags += 1
        
        # Only call chord if the number of adjacent flags matches the cell value
        if adjacent_flags == cell_value:
            game.chord(col_idx, row_idx)
    else:
        # Regular reveal
        game.reveal(col_idx, row_idx)
    
    # Always rerun to update the display
    st.rerun()

def main():
    st.title("💣 Minesweeper")
    
    # Display options in the sidebar
    st.sidebar.title("Game Options")
    
    # Display a preview of tiles
    st.sidebar.markdown("### Tiles Preview")
    st.sidebar.markdown(
        f"{EMOJI_DISPLAY['hidden']} {EMOJI_DISPLAY['flag']} {EMOJI_DISPLAY['1']} {EMOJI_DISPLAY['mine']}"
    )
    
    # Difficulty selection - changed to vertical layout (horizontal=False)
    difficulty = st.sidebar.radio(
        "Difficulty:",
        ["Beginner", "Intermediate", "Expert"],
        index=["beginner", "intermediate", "expert"].index(st.session_state.difficulty),
        horizontal=False
    )
    
    # New game button
    if st.sidebar.button("New Game", use_container_width=True):
        create_new_game(difficulty.lower())
    
    # Initialize game if needed
    if st.session_state.minesweeper_game is None:
        create_new_game(difficulty.lower())
    
    game = st.session_state.minesweeper_game
    
    # Track current time for timer display
    current_time = time.time()
    
    # Show game statistics with timer in real-time
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mines", game.mines - np.sum(game.flagged))
    with col2:
        timer_value = game.get_game_duration()
        st.metric("Time", timer_value)
    with col3:
        if game.game_over:
            if game.game_won:
                st.success("You win! 🎉")
                st.balloons()
            else:
                st.error("Game Over! 💥")
    
    # Add game info in expander
    with st.expander("Game Info", expanded=False):
        st.write(f"Game Active: {'No' if game.game_over else 'Yes'}")
        st.write(f"First Move: {'Yes' if game.first_move else 'No'}")
        st.write(f"Flags Placed: {np.sum(game.flagged)}/{game.mines}")
        st.write(f"Cells Revealed: {np.sum(game.revealed)}/{game.rows * game.cols}")
    
    # Add checkbox for shift key
    shift_col1, shift_col2 = st.columns([1, 10])
    with shift_col1:
        st.checkbox("Shift", key="shift_pressed", label_visibility="collapsed")
    with shift_col2:
        st.markdown("👈 Check this box to enable flagging mode")
    
    # Create container for the game grid
    game_container = st.container()
    
    # Render the actual game
    with game_container:
        # Create rows of columns for the game grid
        for row_idx in range(game.rows):
            cols = st.columns(game.cols)
            for col_idx, col in enumerate(cols):
                render_cell(col, row_idx, col_idx, game)
    
    # Add Rules to the sidebar bottom
    st.sidebar.markdown("---")
    show_rules = st.sidebar.checkbox("Show Rules", value=st.session_state.show_rules)
    st.session_state.show_rules = show_rules
    
    if show_rules:
        st.sidebar.markdown("""
        ### Rules
        1. The goal is to reveal all cells without mines.
        2. Numbers show how many mines are adjacent to that cell.
        3. Use flags to mark cells you think contain mines.
        4. If you reveal a mine, the game is over!
        
        ### Strategy Tips
        - Start by clicking in the middle of the board.
        - If you reveal a "0" cell, all adjacent cells will be revealed automatically.
        - Use the chord action (click on a number) to quickly reveal adjacent cells when all mines are flagged.
        """)
    
    # Handle autorefresh logic
    st.session_state.last_refresh_time = current_time

if __name__ == "__main__":
    main()
