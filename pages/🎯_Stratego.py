import streamlit as st
import numpy import np
import random
import time
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# Initialize Streamlit page
st.set_page_config(
    page_title="Stratego",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh for AI moves and state updates
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=2000, key="stratego_autorefresh")

# Game constants
BOARD_SIZE = 10
WATER_CELLS = [(4, 2), (4, 3), (5, 2), (5, 3), (4, 6), (4, 7), (5, 6), (5, 7)]

# Piece emojis and values - Updated with better single character emojis
PIECE_DATA = {
    # Red pieces (Player 1)
    "🚩": {"name": "Flag", "rank": 0, "movable": False, "emoji": "🚩", "player": 1},
    "💣": {"name": "Bomb", "rank": 0, "movable": False, "emoji": "💣", "player": 1},
    "🕵": {"name": "Spy", "rank": 1, "movable": True, "emoji": "🕵", "player": 1},
    "🏃": {"name": "Scout", "rank": 2, "movable": True, "emoji": "🏃", "player": 1, "special": "move_multiple"},
    "⛏": {"name": "Miner", "rank": 3, "movable": True, "emoji": "⛏", "player": 1, "special": "defuse_bomb"},
    "🪖": {"name": "Sergeant", "rank": 4, "movable": True, "emoji": "🪖", "player": 1},
    "👮": {"name": "Lieutenant", "rank": 5, "movable": True, "emoji": "👮", "player": 1},
    "🎖": {"name": "Captain", "rank": 6, "movable": True, "emoji": "🎖", "player": 1},
    "✰": {"name": "Major", "rank": 7, "movable": True, "emoji": "✰", "player": 1},
    "✯": {"name": "Colonel", "rank": 8, "movable": True, "emoji": "✯", "player": 1},
    "✪": {"name": "General", "rank": 9, "movable": True, "emoji": "✪", "player": 1},
    "⚔": {"name": "Marshal", "rank": 10, "movable": True, "emoji": "⚔", "player": 1},
    
    # Blue pieces (Player 2 / AI)
    "🏁": {"name": "Flag", "rank": 0, "movable": False, "emoji": "🏁", "player": 2},
    "💥": {"name": "Bomb", "rank": 0, "movable": False, "emoji": "💥", "player": 2},
    "🥷": {"name": "Spy", "rank": 1, "movable": True, "emoji": "🥷", "player": 2},
    "🏇": {"name": "Scout", "rank": 2, "movable": True, "emoji": "🏇", "player": 2, "special": "move_multiple"},
    "⚒": {"name": "Miner", "rank": 3, "movable": True, "emoji": "⚒", "player": 2, "special": "defuse_bomb"},
    "🛡": {"name": "Sergeant", "rank": 4, "movable": True, "emoji": "🛡", "player": 2},
    "👨‍✈️": {"name": "Lieutenant", "rank": 5, "movable": True, "emoji": "👨‍✈️", "player": 2},
    "🏅": {"name": "Captain", "rank": 6, "movable": True, "emoji": "🏅", "player": 2},
    "★": {"name": "Major", "rank": 7, "movable": True, "emoji": "★", "player": 2},
    "🎯": {"name": "Colonel", "rank": 8, "movable": True, "emoji": "🎯", "player": 2},
    "👑": {"name": "General", "rank": 9, "movable": True, "emoji": "👑", "player": 2},
    "🗡": {"name": "Marshal", "rank": 10, "movable": True, "emoji": "🗡", "player": 2},
    
    # Special cells
    "🌊": {"name": "Water", "rank": -1, "movable": False, "emoji": "🌊", "player": 0},
    "⬜": {"name": "Empty", "rank": -1, "movable": False, "emoji": "⬜", "player": 0},
    "🔍": {"name": "Unknown", "rank": -1, "movable": True, "emoji": "🔍", "player": 0},  # For fog of war
}

# Starting piece counts for each player
INITIAL_PIECES = {
    "Flag": 1,
    "Bomb": 6,
    "Spy": 1,
    "Scout": 8,
    "Miner": 5,
    "Sergeant": 4,
    "Lieutenant": 4,
    "Captain": 4,
    "Major": 3,
    "Colonel": 2,
    "General": 1,
    "Marshal": 1
}

# Mapping from piece name to emoji for each player - Updated with improved emojis
PIECE_EMOJIS = {
    1: {  # Player 1 (Red)
        "Flag": "🚩",
        "Bomb": "💣",
        "Spy": "🕵",
        "Scout": "🏃",
        "Miner": "⛏",
        "Sergeant": "🪖",
        "Lieutenant": "👮",
        "Captain": "🎖",
        "Major": "✰",
        "Colonel": "✯",
        "General": "✪",
        "Marshal": "⚔",
    },
    2: {  # Player 2 (Blue)
        "Flag": "🏁",
        "Bomb": "💥",
        "Spy": "🥷",
        "Scout": "🏇",
        "Miner": "⚒",
        "Sergeant": "🛡",
        "Lieutenant": "👨‍✈️",
        "Captain": "🏅",
        "Major": "★",
        "Colonel": "🎯",
        "General": "👑",
        "Marshal": "🗡",
    }
}

@dataclass
class GamePiece:
    name: str
    rank: int
    movable: bool
    emoji: str
    player: int
    special: str = None
    revealed_to_opponent: bool = False
    
    def can_defeat(self, other):
        # Spy can defeat Marshal if spy attacks
        if self.name == "Spy" and other.name == "Marshal":
            return True
        # Miner can defeat Bomb
        if self.name == "Miner" and other.name == "Bomb":
            return True
        # Higher rank defeats lower rank
        return self.rank > other.rank
    
    def can_move_to(self, board, from_pos, to_pos):
        if not self.movable:
            return False
            
        from_x, from_y = from_pos
        to_x, to_y = to_pos
        
        # Check if destination is water
        if (to_y, to_x) in WATER_CELLS:
            return False
            
        # Check if in the same row or column (must move orthogonally)
        if from_x != to_x and from_y != to_y:
            return False
            
        # Scout can move multiple spaces in a straight line
        if self.name == "Scout":
            # Check if path is clear (no pieces in between)
            if from_x == to_x:  # Moving vertically
                start, end = (from_y, to_y) if from_y < to_y else (to_y, from_y)
                for y in range(start+1, end):
                    if board[y][from_x] != "⬜":
                        return False
            else:  # Moving horizontally
                start, end = (from_x, to_x) if from_x < to_x else (to_x, from_x)
                for x in range(start+1, end):
                    if board[from_y][x] != "⬜":
                        return False
            return True
                
        # Non-scout pieces can only move 1 space
        if abs(from_x - to_x) + abs(from_y - to_y) != 1:
            return False
            
        return True

@dataclass
class GameState:
    board: List[List[str]]  # Contains emojis
    turn: int = 1  # 1 for player 1, 2 for player 2/AI
    selected_piece_pos: Optional[Tuple[int, int]] = None
    game_phase: str = "setup"  # setup, play, gameover
    winner: int = 0  # 0 for no winner yet, 1 or 2 for player
    revealed_pieces: Dict[Tuple[int, int], bool] = None
    ai_thinking: bool = False
    ai_think_start_time: float = 0
    player_pieces_to_place: Dict[str, int] = None
    ai_pieces_placed: bool = False
    last_move: Dict = None  # Store info about the last move
    battle_log: List[Dict] = None  # Store battle results
    
    def __post_init__(self):
        if self.revealed_pieces is None:
            self.revealed_pieces = {}
        if self.player_pieces_to_place is None:
            self.player_pieces_to_place = INITIAL_PIECES.copy()
        if self.last_move is None:
            self.last_move = {}
        if self.battle_log is None:
            self.battle_log = []

    def get_piece(self, pos):
        row, col = pos
        emoji = self.board[row][col]
        if emoji == "⬜" or emoji == "🌊":
            return None
        piece_data = PIECE_DATA.get(emoji, None)
        if piece_data:
            return GamePiece(**piece_data)
        return None
    
    def is_valid_move(self, from_pos, to_pos):
        """Check if a move is valid"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Check if positions are within bounds
        if not (0 <= from_row < BOARD_SIZE and 0 <= from_col < BOARD_SIZE and 
                0 <= to_row < BOARD_SIZE and 0 <= to_col < BOARD_SIZE):
            return False
        
        # Get pieces
        moving_piece = self.get_piece((from_row, from_col))
        target_cell = self.get_piece((to_row, to_col))
        
        # Check if piece exists and belongs to current player
        if not moving_piece:
            return False
            
        if moving_piece.player != self.turn:
            return False
        
        # Check if target is empty or opponent piece
        if target_cell and target_cell.player == self.turn:
            return False
        
        # Check if piece can move to destination based on its movement rules
        if not moving_piece.can_move_to(self.board, (from_col, from_row), (to_col, to_row)):
            return False
            
        return True
    
    def move_piece(self, from_pos, to_pos):
        """Move a piece from one position to another"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Double-check that this is a valid move
        if not self.is_valid_move(from_pos, to_pos):
            return False
        
        moving_piece = self.get_piece((from_row, from_col))
        target_cell = self.get_piece((to_row, to_col))
        
        # Store info about this move
        self.last_move = {
            "player": self.turn,
            "piece": moving_piece.name,
            "from": (from_row, from_col),
            "to": (to_row, to_col)
        }
        
        # Handle combat if target cell is not empty
        if target_cell:
            # Create battle report
            battle_result = {
                "attacker": {
                    "player": moving_piece.player,
                    "piece": moving_piece.name,
                    "emoji": moving_piece.emoji,
                    "rank": moving_piece.rank
                },
                "defender": {
                    "player": target_cell.player,
                    "piece": target_cell.name,
                    "emoji": target_cell.emoji,
                    "rank": target_cell.rank
                },
                "winner": None,
                "timestamp": time.time()
            }
            
            if moving_piece.can_defeat(target_cell):
                # Attacker wins
                self.board[to_row][to_col] = self.board[from_row][from_col]
                self.board[from_row][from_col] = "⬜"
                # Reveal winning piece to opponent
                self.revealed_pieces[(to_row, to_col)] = True
                battle_result["winner"] = "attacker"
            else:
                # Defender wins or tie
                self.board[from_row][from_col] = "⬜"
                # Reveal defending piece
                self.revealed_pieces[(to_row, to_col)] = True
                battle_result["winner"] = "defender"
            
            # Add battle to the log
            self.battle_log.append(battle_result)
            
            # Update last move with battle info
            self.last_move["battle"] = battle_result
                
            # Check if flag was captured
            if target_cell.name == "Flag":
                self.game_phase = "gameover"
                self.winner = moving_piece.player
                self.last_move["flag_capture"] = True
        else:
            # Move to empty cell
            self.board[to_row][to_col] = self.board[from_row][from_col]
            self.board[from_row][from_col] = "⬜"
        
        # Switch turns
        self.turn = 3 - self.turn  # Toggle between 1 and 2
        
        # If next turn is AI, start AI thinking
        if self.turn == 2 and self.game_phase == "play":
            self.ai_thinking = True
            self.ai_think_start_time = time.time()
        
        self.selected_piece_pos = None
        return True
    
    def place_piece(self, piece_name, pos):
        row, col = pos
        
        # Only allow placement in player's setup area
        if row < 6 or self.board[row][col] != "⬜":
            return False
        
        # Check if player has pieces of this type left
        if self.player_pieces_to_place.get(piece_name, 0) <= 0:
            return False
            
        # Place the piece
        self.board[row][col] = PIECE_EMOJIS[1][piece_name]
        self.player_pieces_to_place[piece_name] -= 1
        
        # Check if setup is complete
        if sum(self.player_pieces_to_place.values()) == 0:
            if self.ai_pieces_placed:
                self.game_phase = "play"
                
        return True
    
    def setup_ai_pieces(self):
        """Place AI pieces randomly on the board"""
        available_positions = [(row, col) for row in range(4) 
                              for col in range(BOARD_SIZE) 
                              if (row, col) not in WATER_CELLS and self.board[row][col] == "⬜"]
        
        pieces_to_place = []
        for piece_name, count in INITIAL_PIECES.items():
            pieces_to_place.extend([piece_name] * count)
        
        random.shuffle(pieces_to_place)
        random.shuffle(available_positions)
        
        # Place flag in back row for better strategy
        flag_pos = random.choice([(0, col) for col in range(BOARD_SIZE) if self.board[0][col] == "⬜"])
        self.board[flag_pos[0]][flag_pos[1]] = PIECE_EMOJIS[2]["Flag"]
        available_positions.remove(flag_pos)
        pieces_to_place.remove("Flag")
        
        # Place remaining pieces
        for i, piece_name in enumerate(pieces_to_place):
            if i < len(available_positions):
                row, col = available_positions[i]
                self.board[row][col] = PIECE_EMOJIS[2][piece_name]
        
        self.ai_pieces_placed = True
        
        # Check if player has also finished setup
        if sum(self.player_pieces_to_place.values()) == 0:
            self.game_phase = "play"
            self.turn = 1  # Player goes first
            
    def ai_make_move(self):
        """Make a random valid move for the AI"""
        # Find all AI pieces
        ai_pieces = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.get_piece((row, col))
                if piece and piece.player == 2 and piece.movable:
                    ai_pieces.append((row, col, piece))
        
        # Find all possible moves
        possible_moves = []
        for row, col, piece in ai_pieces:
            # Check adjacent cells for scout
            if piece.name == "Scout":
                # Check entire rows and columns
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
                for dx, dy in directions:
                    for steps in range(1, BOARD_SIZE):
                        new_row, new_col = row + dy*steps, col + dx*steps
                        if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                            if self.is_valid_move((row, col), (new_row, new_col)):
                                possible_moves.append(((row, col), (new_row, new_col)))
                            # Stop at first piece or invalid cell
                            if self.board[new_row][new_col] != "⬜":
                                break
                        else:
                            break
            else:
                # Check adjacent cells for normal pieces
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
                for dx, dy in directions:
                    new_row, new_col = row + dy, col + dx
                    if 0 <= new_row < BOARD_SIZE and 0 <= new_col < BOARD_SIZE:
                        if self.is_valid_move((row, col), (new_row, new_col)):
                            possible_moves.append(((row, col), (new_row, new_col)))
        
        # If there are valid moves, make one
        if possible_moves:
            # Simple AI: prioritize attacking, then moving forward
            attack_moves = []
            forward_moves = []
            other_moves = []
            
            for from_pos, to_pos in possible_moves:
                to_row, to_col = to_pos
                target = self.get_piece((to_row, to_col))
                
                if target and target.player == 1:
                    # Prioritize attacking pieces
                    attack_moves.append((from_pos, to_pos))
                elif to_row > from_pos[0]:
                    # Moving toward player's side
                    forward_moves.append((from_pos, to_pos))
                else:
                    other_moves.append((from_pos, to_pos))
            
            # Choose a move based on priorities
            if attack_moves:
                from_pos, to_pos = random.choice(attack_moves)
            elif forward_moves:
                from_pos, to_pos = random.choice(forward_moves)
            else:
                from_pos, to_pos = random.choice(other_moves)
                
            self.move_piece(from_pos, to_pos)
        
        self.ai_thinking = False
        return True

# Initialize game state in session state
if 'stratego_game' not in st.session_state:
    # Create empty board
    board = [["⬜" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    # Add water cells
    for row, col in WATER_CELLS:
        board[row][col] = "🌊"
    
    st.session_state.stratego_game = GameState(board=board)
    st.session_state.last_refresh = time.time()
    st.session_state.show_rules = False
    st.session_state.selected_piece_type = None

def reset_game():
    # Create empty board
    board = [["⬜" for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    # Add water cells
    for row, col in WATER_CELLS:
        board[row][col] = "🌊"
    
    st.session_state.stratego_game = GameState(board=board)
    st.session_state.selected_piece_type = None

def render_board(game_state):
    for row in range(BOARD_SIZE):
        cols = st.columns(BOARD_SIZE)
        for col in range(BOARD_SIZE):
            cell = game_state.board[row][col]
            
            # Get piece info for tooltip
            piece_info = ""
            piece = game_state.get_piece((row, col))
            if piece:
                # Only show detailed info for player's pieces or revealed opponent pieces
                if piece.player == 1 or (row, col) in game_state.revealed_pieces:
                    piece_info = f"{piece.name} ({piece.rank})"
                    if piece.special:
                        special_abilities = {
                            "move_multiple": "Can move multiple spaces",
                            "defuse_bomb": "Can defuse bombs"
                        }
                        piece_info += f" - {special_abilities.get(piece.special, '')}"
                elif piece.player == 0:  # Water
                    piece_info = "Water - Cannot pass through"
            
            # Handle fog of war - show opponent pieces as unknown unless revealed
            # Modified to always show AI pieces as unknown regardless of battle outcome
            if game_state.game_phase == "play" and cell != "⬜" and cell != "🌊":
                if piece and piece.player == 2:
                    # Always show AI pieces as unknown to maintain fog of war
                    # Only exception is if explicitly revealed through battle
                    if (row, col) not in game_state.revealed_pieces:
                        cell = "🔍"  # Show unknown piece for opponent
                        piece_info = "Unknown opponent piece"
            
            # Highlight selected piece
            if game_state.selected_piece_pos == (row, col):
                # Use custom styling to highlight the selected piece
                cols[col].markdown(
                    f'<div style="background-color: rgba(255,255,0,0.3); '
                    f'border: 2px solid yellow; border-radius: 5px; padding: 5px; '
                    f'display: flex; justify-content: center; align-items: center; '
                    f'height: 40px; font-size: 24px;">{cell}</div>', 
                    unsafe_allow_html=True
                )
            else:
                # Check if this is a valid move for the selected piece
                is_valid_move = False
                if (game_state.selected_piece_pos and 
                    game_state.is_valid_move(game_state.selected_piece_pos, (row, col))):
                    is_valid_move = True
                    if piece_info:
                        piece_info += " - Valid move destination"
                    else:
                        piece_info = "Valid move destination"
                
                # Regular cell or valid move highlight
                button_key = f"cell_{row}_{col}"
                if is_valid_move:
                    # For valid moves, use a distinctive background
                    if cols[col].button(cell, key=button_key, 
                                       use_container_width=True, 
                                       help=f"Move to: {piece_info}"):
                        # Direct click handler for valid moves
                        from_row, from_col = game_state.selected_piece_pos
                        # Force the move and immediately rerun - this is key to fixing the issue
                        if game_state.move_piece(game_state.selected_piece_pos, (row, col)):
                            # Force a full rerun to update the UI immediately
                            st.session_state.last_action = "move"
                            st.rerun()
                else:
                    # On click, select the piece or move to this position
                    help_text = piece_info if piece_info else f"Row {row+1}, Column {col+1}"
                    if cols[col].button(cell, key=button_key, 
                                       use_container_width=True, 
                                       help=help_text):
                        handle_cell_click(game_state, row, col)

def handle_cell_click(game_state, row, col):
    """Handle clicks on the game board cells"""
    # Setup phase - place selected piece
    if game_state.game_phase == "setup":
        if st.session_state.selected_piece_type:
            # Try to place the selected piece
            if game_state.place_piece(st.session_state.selected_piece_type, (row, col)):
                # Default behavior: keep the piece type selected (don't clear selection)
                # Only clear selection when no more of this piece type is available
                if game_state.player_pieces_to_place.get(st.session_state.selected_piece_type, 0) <= 0:
                    st.session_state.selected_piece_type = None
                    
                # If player is done and AI hasn't placed pieces yet, do that now
                if (sum(game_state.player_pieces_to_place.values()) == 0 and 
                    not game_state.ai_pieces_placed):
                    game_state.setup_ai_pieces()
        return
    
    # Play phase - select or move pieces
    if game_state.game_phase == "play" and game_state.turn == 1:  # Player's turn
        piece = game_state.get_piece((row, col))
        
        # If no piece is selected and clicked on player's piece, select it
        if game_state.selected_piece_pos is None:
            if piece and piece.player == 1 and piece.movable:
                game_state.selected_piece_pos = (row, col)
                st.session_state.last_action = "select"
                st.rerun()  # Force rerun to update UI and show highlighted piece
            else:
                # Do nothing if clicked on invalid selection
                pass
        else:
            # If a piece is already selected
            from_row, from_col = game_state.selected_piece_pos
            
            # If clicked on the same piece, deselect it
            if (row, col) == game_state.selected_piece_pos:
                game_state.selected_piece_pos = None
                st.session_state.last_action = "deselect"
                st.rerun()
            # If clicked on another of player's pieces, select that instead
            elif piece and piece.player == 1:
                game_state.selected_piece_pos = (row, col)
                st.session_state.last_action = "select"
                st.rerun()
            # If clicked on a valid move destination, move the piece
            elif game_state.is_valid_move(game_state.selected_piece_pos, (row, col)):
                result = game_state.move_piece(game_state.selected_piece_pos, (row, col))
                st.session_state.last_action = "move"
                st.rerun()  # Force rerun to update UI after move
            # If clicked on an invalid destination, deselect
            else:
                game_state.selected_piece_pos = None
                st.session_state.last_action = "deselect"
                st.rerun()

def format_position(pos):
    """Format a board position to be more human-readable (letter + number)"""
    row, col = pos
    return f"{chr(65+col)}{row+1}"  # A1, B2, etc.

def render_move_history(game_state):
    """Display the move history in a readable format"""
    st.markdown("### Game History")
    
    # Display the last AI move if available
    if game_state.last_move and game_state.last_move.get("player") == 2:
        from_pos = game_state.last_move.get("from")
        to_pos = game_state.last_move.get("to")
        piece_name = game_state.last_move.get("piece")
        
        if from_pos and to_pos and piece_name:
            from_str = format_position(from_pos)
            to_str = format_position(to_pos)
            
            # Don't reveal AI piece name
            st.info(f"**AI last move:** {from_str} to {to_str}")
    
    # Display recent battles (limit to last 5)
    if game_state.battle_log:
        st.markdown("#### Recent Battles")
        
        # Create a container for battles with fixed height and scrolling
        battle_container = st.container()
        
        with battle_container:
            for battle in reversed(game_state.battle_log[-5:]):  # Show most recent first, limit to 5
                attacker = battle["attacker"]
                defender = battle["defender"]
                winner = battle["winner"]
                
                # Determine player names
                attacker_name = "Your" if attacker["player"] == 1 else "AI"
                defender_name = "Your" if defender["player"] == 1 else "AI"
                
                # Create a rich battle description that respects fog of war
                if winner == "attacker":
                    # If AI attacks and wins, hide its piece identity
                    if attacker["player"] == 2:
                        result_markdown = (
                            f"AI 🔍 **Unknown Piece** "
                            f"defeated {defender_name} {defender['emoji']} **{defender['piece']}**"
                        )
                        st.error(result_markdown)
                    else:
                        # Player attacker - show full info
                        result_markdown = (
                            f"{attacker_name} {attacker['emoji']} **{attacker['piece']}** "
                            f"defeated {defender_name} {defender['emoji']} **{defender['piece']}**"
                        )
                        st.success(result_markdown)
                else:
                    # If AI defends and wins, hide its piece identity
                    if defender["player"] == 2:
                        result_markdown = (
                            f"AI 🔍 **Unknown Piece** "
                            f"defeated {attacker_name} {attacker['emoji']} **{attacker['piece']}**"
                        )
                        st.error(result_markdown)
                    else:
                        # Player defender - show full info
                        result_markdown = (
                            f"{defender_name} {defender['emoji']} **{defender['piece']}** "
                            f"defeated {attacker_name} {attacker['emoji']} **{attacker['piece']}**"
                        )
                        st.success(result_markdown)

def main():
    
    # Initialize last_action if needed
    if 'last_action' not in st.session_state:
        st.session_state.last_action = None
    
    # Add New Game button prominently at the top
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 New Game", key="top_new_game", use_container_width=True):
            reset_game()
            st.session_state.last_action = "new_game"
            st.rerun()
    
    game_state = st.session_state.stratego_game
    
    # AI move logic
    current_time = time.time()
    
    # If it's AI's turn and AI is thinking and enough time has passed
    if (game_state.turn == 2 and game_state.ai_thinking and 
            current_time - game_state.ai_think_start_time > 1.0):
        game_state.ai_make_move()
        st.session_state.last_action = "ai_move"
        st.rerun()  # Make sure we rerun after AI moves
    
    # Sidebar with game controls and piece selection (for setup phase)
    with st.sidebar:
        
        if game_state.game_phase == "setup":
            
            # Show remaining pieces to place
            st.subheader("Place Your Pieces")
            
            # Grid of piece types for selection
            piece_cols = 3
            pieces_rows = [list(game_state.player_pieces_to_place.keys())[i:i+piece_cols] 
                         for i in range(0, len(game_state.player_pieces_to_place), piece_cols)]
            
            for row in pieces_rows:
                cols = st.columns(piece_cols)
                for i, piece_name in enumerate(row):
                    if i < len(row):  # Make sure we don't exceed the row length
                        count = game_state.player_pieces_to_place[piece_name]
                        emoji = PIECE_EMOJIS[1][piece_name]
                        
                        # Add piece rank info to the help text
                        rank_info = ""
                        if piece_name == "Flag":
                            rank_info = "(Flag - Must protect!)"
                        elif piece_name == "Bomb":
                            rank_info = "(Bomb - Immovable)"
                        elif piece_name == "Spy":
                            rank_info = "(1 - Can defeat Marshal when attacking)"
                        elif piece_name == "Scout":
                            rank_info = "(2 - Can move multiple spaces)"
                        elif piece_name == "Miner":
                            rank_info = "(3 - Can defuse bombs)"
                        else:
                            # Get numeric rank for other pieces
                            for key, data in PIECE_DATA.items():
                                if data["name"] == piece_name and data["player"] == 1:
                                    rank_info = f"(Rank {data['rank']})"
                                    break
                        
                        # Skip if no pieces left
                        if count <= 0:
                            cols[i].write(f"{emoji} {piece_name}: 0")
                            continue
                        
                        # Highlight if selected
                        if st.session_state.selected_piece_type == piece_name:
                            cols[i].markdown(f"**→ {emoji} {piece_name}: {count} ←**")
                        else:
                            if cols[i].button(f"{emoji} {piece_name}: {count}", 
                                             key=f"select_{piece_name}", 
                                             help=f"{piece_name} {rank_info}"):
                                st.session_state.selected_piece_type = piece_name
                                st.rerun()  # Force rerun to show selection immediately
    
            # Clear selection button is always available when a piece is selected
            if st.session_state.selected_piece_type:
                if st.button("Clear Selection", key="clear_selection", use_container_width=True):
                    st.session_state.selected_piece_type = None
                    st.rerun()
            
            # Quick placement options
            
            if st.button("Auto-Arrange Remaining Pieces", use_container_width=True):
                # Auto-arrange remaining pieces
                available_positions = [(row, col) for row in range(6, BOARD_SIZE) 
                                      for col in range(BOARD_SIZE) 
                                      if game_state.board[row][col] == "⬜"]
                
                if available_positions:
                    random.shuffle(available_positions)
                    
                    # Place flag in back row first if available
                    if game_state.player_pieces_to_place.get("Flag", 0) > 0:
                        back_row_positions = [(9, col) for col in range(BOARD_SIZE) 
                                             if game_state.board[9][col] == "⬜"]
                        if back_row_positions:
                            flag_pos = random.choice(back_row_positions)
                            game_state.board[flag_pos[0]][flag_pos[1]] = PIECE_EMOJIS[1]["Flag"]
                            game_state.player_pieces_to_place["Flag"] -= 1
                            available_positions.remove(flag_pos)
                    
                    # Place remaining pieces
                    i = 0
                    for piece_name, count in list(game_state.player_pieces_to_place.items()):
                        for _ in range(count):
                            if i < len(available_positions):
                                row, col = available_positions[i]
                                game_state.board[row][col] = PIECE_EMOJIS[1][piece_name]
                                i += 1
                    
                    # Clear remaining pieces
                    for piece_name in game_state.player_pieces_to_place:
                        game_state.player_pieces_to_place[piece_name] = 0
                    
                    # If AI hasn't placed pieces, do that now
                    if not game_state.ai_pieces_placed:
                        game_state.setup_ai_pieces()
            
            if st.button("Reset Setup", use_container_width=True):
                reset_game()
            
        elif game_state.game_phase == "play":
            if game_state.turn == 1:
                st.info("**Your turn!** Select a piece to move.")
            else:
                st.warning("**AI is thinking...**")
            
            st.markdown("---")
            st.subheader("Game Stats")
            st.write(f"**Turn:** {'Your turn' if game_state.turn == 1 else 'AI turn'}")
            
            # Count captured pieces by each player
            player1_pieces = sum(1 for row in range(BOARD_SIZE) for col in range(BOARD_SIZE) 
                               if game_state.get_piece((row, col)) and 
                               game_state.get_piece((row, col)).player == 1)
            
            player2_pieces = sum(1 for row in range(BOARD_SIZE) for col in range(BOARD_SIZE) 
                               if game_state.get_piece((row, col)) and 
                               game_state.get_piece((row, col)).player == 2)
            
            st.write(f"**Your pieces:** {player1_pieces}")
            st.write(f"**AI pieces:** {player2_pieces}")
        
        elif game_state.game_phase == "gameover":
            if game_state.winner == 1:
                st.success("**You won!** 🎉")
            else:
                st.error("**AI won!** Try again?")
        
        if game_state.game_phase == "gameover":
            if st.button("New Game", use_container_width=True):
                reset_game()
        
        # Add piece rank reference to sidebar - Updated to include new emojis with piece names
        st.markdown("---")
        with st.expander("Piece Rank Reference", expanded=False):
            st.markdown("""
            | Piece | Rank | Special Ability |
            |-------|------|-----------------|
            | Marshal ⚔/🗡 | 10 | Highest rank |
            | General ✪/👑 | 9 | |
            | Colonel ✯/🎯 | 8 | |
            | Major ✰/★ | 7 | |
            | Captain 🎖/🏅 | 6 | |
            | Lieutenant 👮/👨‍✈️ | 5 | |
            | Sergeant 🪖/🛡 | 4 | |
            | Miner ⛏/⚒ | 3 | Can defuse bombs |
            | Scout 🏃/🏇 | 2 | Can move multiple spaces |
            | Spy 🕵/🥷 | 1 | Can defeat Marshal when attacking |
            | Bomb 💣/💥 | - | Immovable, defeats any attacker except Miners |
            | Flag 🚩/🏁 | - | Immovable, game ends if captured |
            """)
        
        # Toggle rules display
        st.markdown("---")
        show_rules = st.checkbox("Show Rules", value=st.session_state.show_rules)
        st.session_state.show_rules = show_rules  # Fix the variable name
        
        # Display game rules
        if st.session_state.show_rules:
            st.markdown("""
            ### Stratego Rules
            
            #### Objective
            Capture the opponent's flag or eliminate all movable pieces.
            
            #### Pieces (from highest to lowest rank)
            1. Marshal (10) - Highest rank
            2. General (9)
            3. Colonel (8)
            4. Major (7)
            5. Captain (6)
            6. Lieutenant (5)
            7. Sergeant (4)
            8. Miner (3) - Can defuse bombs
            9. Scout (2) - Can move any number of spaces in a straight line
            10. Spy (1) - Can defeat the Marshal if it attacks
            11. Bomb (B) - Immovable, defeats any attacker except Miners
            12. Flag (F) - Immovable, game ends if captured
            
            #### Movement
            - Most pieces move one space horizontally or vertically
            - Scouts can move any number of spaces in a straight line
            - Bombs and flags cannot move
            - Cannot move through water or other pieces
            
            #### Combat
            - Higher rank defeats lower rank
            - Spy defeats Marshal only if Spy attacks
            - Miners can defuse bombs
            - Equal ranks both get eliminated
            """)
    
    # Main board area
    game_container, info_container = st.columns([3, 1])
    
    with game_container:
        st.markdown("### Game Board")
        
        # Show helper text based on game phase
        if game_state.game_phase == "setup":
            st.info("Place your pieces on the bottom rows of the board. Place the Flag in a safe position!")
        elif game_state.game_phase == "play":
            if game_state.turn == 1:
                st.success("Your turn - Select a piece to move")
            else:
                st.warning("AI thinking...")
        elif game_state.game_phase == "gameover":
            if game_state.winner == 1:
                st.success("You won! You captured the flag!")
            else:
                st.error("Game over - AI captured your flag!")
        
        # Render the game board
        render_board(game_state)
    
    # Render move history and battle info in the right column
    with info_container:
        render_move_history(game_state)

if __name__ == "__main__":
    main()




