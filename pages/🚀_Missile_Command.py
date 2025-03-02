import streamlit as st
import random
import time
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
import copy

# Update the page config to hide the default header
st.set_page_config(
    page_title="Missile Command",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/streamlit/streamlit/issues',
        'Report a bug': "https://github.com/streamlit/streamlit/issues/new",
        'About': "# 🚀 Missile Command\nDefend your cities from incoming missiles!"
    }
)

# Custom CSS for dark mode and better game appearance
st.markdown("""
<style>
    /* Reduce top padding/margin */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* Hide default title/header */
    .css-18ni7ap {
        display: none !important;
    }
    
    /* Make the container for the game slimmer */
    .stButton button {
        height: 38px;  /* Slightly smaller buttons */
        min-height: 0;
    }
    
    /* Compact headers */
    h1, h2, h3 {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
    }
    
    /* Streamlit container padding reduction */
    div.css-1r6slb0.e1tzin5v2 {
        padding: 1px !important;
    }
    
    /* Make game board more compact */
    .row-widget.stButton {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Additional styles from before */
    /* Dark mode styles */
    
    /* Button styling for game grid */
    .stButton button {
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
        background-color: transparent;
        border: none;
        transition: transform 0.1s;
    }
    
    .stButton button:hover {
        transform: scale(1.1);
    }
    
    /* Make emoji bigger in buttons */
    .stButton button p {
        font-size: 1.5rem;
        margin: 0;
    }
    
    /* Game grid container */
    .game-grid {
        background-color: #111827;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5);
    }
    
    /* Game status header */
    .game-header {
        color: #00BFFF;
        text-align: center;
        margin-bottom: 10px;
    }
    
    /* Score displays */
    .score-display {
        font-size: 1.8rem;
        font-weight: bold;
        color: #FFD700;
    }
    
    /* Explosions */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    
    .explosion-effect {
        animation: pulse 0.5s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Import auto-refresh for game loop
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=250, key="missile_command_refresh")  # Faster refresh rate: ~4 FPS

# Game constants
BOARD_WIDTH = 15
BOARD_HEIGHT = 12
GROUND_ROW = BOARD_HEIGHT - 1

# Game emojis - More vibrant and distinguishable
EMPTY = "⬛"  # Empty sky
CITY = "🏙️"  # City
CITY_DESTROYED = "🔥"  # Destroyed city
BASE = "🚀"  # Missile base
BASE_EMPTY = "🧱"  # Empty missile base
ENEMY_MISSILE = "💣"  # Enemy missile
ENEMY_MISSILE_FAST = "⚡"  # Fast enemy missile
ENEMY_MISSILE_SPLIT = "🧨"  # Splitting missile
PLAYER_MISSILE = "⤴️"  # Player missile
EXPLOSION = "💥"  # Explosion
FADING_EXPLOSION = "✨"  # Fading explosion
LARGE_EXPLOSION = "🌟"  # Large explosion
BACKGROUND_STAR = "✧"  # Background star
BACKGROUND_STAR = EMPTY
POWERUP = "🎁"  # Powerup

# Adjust these constants for much slower gameplay
ENEMY_SPAWN_INTERVAL_BASE = 4.0  # Significantly increase base spawn interval (was 5.0)
MIN_MISSILE_STEPS = 25  # Much higher minimum steps for slower movement
MAX_MISSILE_STEPS = 35  # Much higher maximum steps
SPLIT_MISSILE_STEPS = 28  # Medium speed for split missiles
FAST_MISSILE_STEPS = 15  # Fast missiles still faster than others 
PLAYER_MISSILE_STEPS = 6  # Player missiles should still be relatively quick

# Game difficulty constants - adjust for better gameplay
MAX_ENEMY_MISSILES = 5  # Limit the number of enemy missiles on screen
LEVEL_SPEED_FACTOR = 0.1  # How much each level increases missile speed (lower = gentler progression)
COMBO_TIMEOUT = 3.0  # Seconds before combo resets

@dataclass
class City:
    col: int
    alive: bool = True

@dataclass
class Base:
    col: int
    missiles: int = 10
    alive: bool = True

@dataclass
class Missile:
    start_col: int
    start_row: int
    target_col: int
    target_row: int
    current_col: float
    current_row: float
    is_enemy: bool
    missile_type: str = "normal"  # normal, fast, split
    steps: int = 0
    max_steps: int = 8  # How many steps to reach target
    
    def update(self) -> bool:
        """Update missile position. Return True if reached target."""
        self.steps += 1
        progress = min(1.0, self.steps / self.max_steps)
        
        # Use curved trajectory for more realistic movement
        # Add slight curve to missiles by using sine wave
        if self.is_enemy:
            curve_factor = 0.2 * math.sin(progress * math.pi)
            dx = self.target_col - self.start_col
            # Add curve based on horizontal distance
            curve_adjustment = curve_factor * dx
        else:
            curve_adjustment = 0  # Player missiles go straight
        
        # Calculate position with curve adjustment
        self.current_col = self.start_col + (self.target_col - self.start_col) * progress
        self.current_row = self.start_row + (self.target_row - self.start_row) * progress + curve_adjustment
        
        # Check if reached target
        return self.steps >= self.max_steps

@dataclass
class Explosion:
    col: int
    row: int
    radius: int = 1
    max_radius: int = 2
    duration: int = 3  # How many frames to stay at max size
    current_duration: int = 0
    growing: bool = True
    fading: bool = False
    explosion_type: str = "normal"  # normal, large
    
    def update(self) -> bool:
        """Update explosion state. Return True if explosion is finished."""
        if self.growing:
            self.radius += 1
            if self.radius >= self.max_radius:
                self.growing = False
        elif not self.fading:
            self.current_duration += 1
            if self.current_duration >= self.duration:
                self.fading = True
        else:
            self.radius -= 1
            
        # Explosion is finished when radius becomes 0 during fading
        return self.fading and self.radius <= 0

@dataclass
class GameState:
    score: int = 0
    level: int = 1
    game_over: bool = False
    cities: List[City] = field(default_factory=list)
    bases: List[Base] = field(default_factory=list)
    player_missiles: List[Missile] = field(default_factory=list)
    enemy_missiles: List[Missile] = field(default_factory=list)
    explosions: List[Explosion] = field(default_factory=list)
    last_enemy_spawn: float = 0
    enemy_spawn_interval: float = ENEMY_SPAWN_INTERVAL_BASE
    frame_count: int = 0
    board: List[List[str]] = field(default_factory=list)
    combo_count: int = 0
    last_hit_time: float = 0
    power_up_active: bool = False
    power_up_type: str = None
    power_up_end_time: float = 0
    background_stars: List[Tuple[int, int]] = field(default_factory=list)
    
    def __post_init__(self):
        # Initialize board
        self.board = [[EMPTY for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        
        # Set ground row
        self.board[GROUND_ROW] = ["🟫" for _ in range(BOARD_WIDTH)]
        
        # Set cities - more evenly distributed
        city_positions = [2, 5, 8, 11]
        self.cities = [City(col=pos) for pos in city_positions]
        
        # Set bases
        base_positions = [0, 7, 14]
        self.bases = [Base(col=pos) for pos in base_positions]
        
        # Generate background stars for visual effect
        num_stars = random.randint(15, 25)
        for _ in range(num_stars):
            col = random.randint(0, BOARD_WIDTH - 1)
            row = random.randint(0, GROUND_ROW - 2)  # Keep stars away from ground
            self.background_stars.append((row, col))
        
        # Update board with initial objects
        self.update_board()
    
    def update_board(self):
        """Update the visual board with current game state"""
        # Reset sky (leave ground intact)
        for row in range(GROUND_ROW):
            self.board[row] = [EMPTY for _ in range(BOARD_WIDTH)]
        
        # Add background stars first (lowest layer)
        for row, col in self.background_stars:
            self.board[row][col] = BACKGROUND_STAR
        
        # Place cities on the board
        for city in self.cities:
            if city.alive:
                self.board[GROUND_ROW - 1][city.col] = CITY
            else:
                self.board[GROUND_ROW - 1][city.col] = CITY_DESTROYED
        
        # Place bases on the board
        for base in self.bases:
            if base.alive:
                self.board[GROUND_ROW - 1][base.col] = BASE
            else:
                self.board[GROUND_ROW - 1][base.col] = BASE_EMPTY
        
        # Place enemy missiles
        for missile in self.enemy_missiles:
            col = round(missile.current_col)
            row = round(missile.current_row)
            if 0 <= row < GROUND_ROW and 0 <= col < BOARD_WIDTH:
                if missile.missile_type == "fast":
                    self.board[row][col] = ENEMY_MISSILE_FAST
                elif missile.missile_type == "split":
                    self.board[row][col] = ENEMY_MISSILE_SPLIT
                else:
                    self.board[row][col] = ENEMY_MISSILE
        
        # Place player missiles
        for missile in self.player_missiles:
            col = round(missile.current_col)
            row = round(missile.current_row)
            if 0 <= row < GROUND_ROW and 0 <= col < BOARD_WIDTH:
                self.board[row][col] = PLAYER_MISSILE
        
        # Place explosions (and their radius) - this comes last to overlay other objects
        for explosion in self.explosions:
            # Center explosion
            center_col = explosion.col
            center_row = explosion.row
            
            # Determine explosion character based on type and phase
            explosion_char = EXPLOSION
            if explosion.explosion_type == "large":
                explosion_char = LARGE_EXPLOSION
            elif explosion.fading:
                explosion_char = FADING_EXPLOSION
            
            # Draw the explosion with its radius
            for row in range(center_row - explosion.radius, center_row + explosion.radius + 1):
                for col in range(center_col - explosion.radius, center_col + explosion.radius + 1):
                    # Check if within circle radius and board bounds
                    if (0 <= row < GROUND_ROW and 0 <= col < BOARD_WIDTH and
                            (row - center_row)**2 + (col - center_col)**2 <= explosion.radius**2):
                        self.board[row][col] = explosion_char

def reset_game():
    """Reset the game to starting state"""
    st.session_state.missile_command_game = GameState()
    st.session_state.game_start_time = time.time()
    st.session_state.selected_base = 1  # Middle base selected by default
    st.session_state.high_score = max(st.session_state.get('high_score', 0), 
                                    st.session_state.missile_command_game.score)

def spawn_enemy_missile(game_state: GameState):
    """Spawn a new enemy missile with different types based on level"""
    # Target city or base
    valid_targets = []
    
    # Add cities as targets
    for city in game_state.cities:
        if city.alive:
            valid_targets.append((city.col, GROUND_ROW - 1))
    
    # Add bases as targets but with lower probability
    for base in game_state.bases:
        if base.alive:
            # Higher levels target bases more often
            for _ in range(min(1, game_state.level // 3)):
                valid_targets.append((base.col, GROUND_ROW - 1))
    
    if not valid_targets:  # No targets left
        return
    
    # Choose random target
    target_col, target_row = random.choice(valid_targets)
    
    # Choose random start position at top of screen, avoid spawning directly above targets
    safe_zone_width = 1
    safe_start_cols = [c for c in range(BOARD_WIDTH) if abs(c - target_col) > safe_zone_width]
    if safe_start_cols:
        start_col = random.choice(safe_start_cols)
    else:
        start_col = random.randint(0, BOARD_WIDTH - 1)
    
    # Slower missile speeds with larger values
    missile_type = "normal"
    # Base speed that increases very gradually with level
    missile_speed = random.randint(
        int(MIN_MISSILE_STEPS - game_state.level * LEVEL_SPEED_FACTOR), 
        int(MAX_MISSILE_STEPS - game_state.level * LEVEL_SPEED_FACTOR)
    )
    missile_speed = max(missile_speed, MIN_MISSILE_STEPS // 2)  # Ensure minimum speed
    
    # Add fast missiles starting at higher levels
    if game_state.level >= 3 and random.random() < 0.15:  # Lower probability
        missile_type = "fast"
        missile_speed = random.randint(FAST_MISSILE_STEPS, FAST_MISSILE_STEPS + 5)
    
    # Add splitting missiles at even higher levels
    if game_state.level >= 5 and random.random() < 0.1:
        missile_type = "split"
        missile_speed = random.randint(SPLIT_MISSILE_STEPS, SPLIT_MISSILE_STEPS + 5)
    
    # Create the missile with updated speed
    missile = Missile(
        start_col=start_col,
        start_row=0,
        target_col=target_col,
        target_row=target_row,
        current_col=start_col,
        current_row=0,
        is_enemy=True,
        missile_type=missile_type,
        max_steps=missile_speed
    )
    
    game_state.enemy_missiles.append(missile)
    game_state.last_enemy_spawn = time.time()

def split_missile(game_state, original_missile):
    """Split a missile into multiple smaller missiles"""
    current_col = original_missile.current_col
    current_row = original_missile.current_row
    
    # Create 2-3 new missiles heading in different directions
    num_splits = random.randint(2, 3)
    
    # Make split missiles slower too
    for _ in range(num_splits):
        # Get random target near the ground
        target_col = random.randint(max(0, int(current_col) - 4), min(BOARD_WIDTH - 1, int(current_col) + 4))
        
        # Create the new missile
        new_missile = Missile(
            start_col=current_col,
            start_row=current_row,
            target_col=target_col,
            target_row=GROUND_ROW - 1,
            current_col=current_col,
            current_row=current_row,
            is_enemy=True,
            missile_type="normal",  # Split missiles become normal missiles
            max_steps=random.randint(MIN_MISSILE_STEPS - 4, MIN_MISSILE_STEPS + 2)
        )
        game_state.enemy_missiles.append(new_missile)

def check_collision(missile_col, missile_row, explosions):
    """Check if a missile is within any explosion radius"""
    for explosion in explosions:
        # Simple distance-based collision detection
        distance_squared = (missile_col - explosion.col)**2 + (missile_row - explosion.row)**2
        if distance_squared <= explosion.radius**2:
            return True
    return False

def fire_player_missile(game_state: GameState, target_col: int, target_row: int):
    """Fire a player missile from selected base to target coordinates"""
    selected_base_index = st.session_state.selected_base
    if selected_base_index >= len(game_state.bases):
        selected_base_index = 0
    
    base = game_state.bases[selected_base_index]
    
    # Check if base is alive and has missiles
    if not base.alive or base.missiles <= 0:
        # Try other bases if this one can't fire
        for i, alt_base in enumerate(game_state.bases):
            if alt_base.alive and alt_base.missiles > 0:
                base = alt_base
                st.session_state.selected_base = i
                break
        else:
            # No bases can fire
            return False
    
    # Create player missile
    player_missile = Missile(
        start_col=base.col,
        start_row=GROUND_ROW - 1,
        target_col=target_col,
        target_row=target_row,
        current_col=base.col,
        current_row=GROUND_ROW - 1,
        is_enemy=False,
        max_steps=PLAYER_MISSILE_STEPS  # Player missiles are faster than enemy missiles
    )
    
    game_state.player_missiles.append(player_missile)
    base.missiles -= 1
    return True

def update_game(game_state: GameState):
    """Update the game state"""
    if game_state.game_over:
        return
    
    current_time = time.time()
    
    # Check for combo reset
    if game_state.combo_count > 0 and current_time - game_state.last_hit_time > 2.0:
        game_state.combo_count = 0
    
    # Check for power-up expiration
    if game_state.power_up_active and current_time > game_state.power_up_end_time:
        game_state.power_up_active = False
        game_state.power_up_type = None
    
    # Update explosions and remove finished ones
    for explosion in list(game_state.explosions):
        if explosion.update():  # If explosion is finished
            game_state.explosions.remove(explosion)
    
    # Spawn enemy missiles
    time_since_last_spawn = current_time - game_state.last_enemy_spawn
    
    # Adjust spawn interval based on level - much slower progression
    spawn_interval = max(3.0, game_state.enemy_spawn_interval - (game_state.level - 1) * 0.2)
    
    # Maximum missiles scales with level very slowly
    max_missiles = min(MAX_ENEMY_MISSILES, 2 + game_state.level // 2)  # Fewer missiles even at higher levels
    
    if time_since_last_spawn > spawn_interval and len(game_state.enemy_missiles) < max_missiles:
        spawn_enemy_missile(game_state)
    
    # Update player missiles
    for missile in list(game_state.player_missiles):
        if missile.update():  # If missile reached target
            game_state.player_missiles.remove(missile)
            # Create explosion at target
            explosion_type = "normal"
            explosion_size = 2
            
            # Check for power-up: larger explosions
            if game_state.power_up_active and game_state.power_up_type == "large_explosion":
                explosion_type = "large"
                explosion_size = 3
            
            explosion = Explosion(
                col=round(missile.target_col),
                row=round(missile.target_row),
                max_radius=explosion_size,
                explosion_type=explosion_type
            )
            game_state.explosions.append(explosion)
    
    # Update enemy missiles
    for missile in list(game_state.enemy_missiles):
        old_col, old_row = round(missile.current_col), round(missile.current_row)
        
        # Check if missile is in any explosion
        if check_collision(old_col, old_row, game_state.explosions):
            game_state.enemy_missiles.remove(missile)
            
            # Handle split missiles specially
            if missile.missile_type == "split":
                split_missile(game_state, missile)
                game_state.score += 35  # Bonus for destroying a splitting missile
            elif missile.missile_type == "fast":
                game_state.score += 50  # Bonus for destroying a fast missile
            else:
                game_state.score += 25  # Base points
            
            # Update combo
            game_state.combo_count += 1
            game_state.last_hit_time = current_time
            
            # Add combo bonus
            if game_state.combo_count >= 3:
                combo_bonus = game_state.combo_count * 10
                game_state.score += combo_bonus
            
            continue
        
        # Update position
        if missile.update():  # If missile reached target
            # Create explosion at target
            target_col, target_row = round(missile.target_col), round(missile.target_row)
            game_state.enemy_missiles.remove(missile)
            
            # Create explosion at target
            explosion = Explosion(
                col=target_col,
                row=target_row,
                max_radius=1
            )
            game_state.explosions.append(explosion)
            
            # Check if hit city
            for city in game_state.cities:
                if city.alive and city.col == target_col and target_row == GROUND_ROW - 1:
                    city.alive = False
                    break
            
            # Check if hit base
            for base in game_state.bases:
                if base.alive and base.col == target_col and target_row == GROUND_ROW - 1:
                    base.alive = False
                    break
    
    # Check if game is over (all cities destroyed)
    cities_alive = sum(1 for city in game_state.cities if city.alive)
    if cities_alive == 0:
        game_state.game_over = True
        # Save high score
        st.session_state.high_score = max(st.session_state.get('high_score', 0), game_state.score)
    
    # Check level advancement (when all enemy missiles are destroyed)
    if not game_state.enemy_missiles:
        # Count remaining missiles
        remaining_missiles = 0
        for base in game_state.bases:
            if base.alive:
                remaining_missiles += base.missiles
        
        # Award points for unused missiles
        if remaining_missiles > 0 and game_state.frame_count % 5 == 0:  # Every few frames
            # Find a base with missiles
            for base in game_state.bases:
                if base.alive and base.missiles > 0:
                    base.missiles -= 1
                    game_state.score += 10
                    break
        
        # If no more player missiles on screen and enough time passed
        if (not game_state.player_missiles and 
            len(game_state.explosions) == 0 and
            game_state.frame_count > 30):
            
            # Advance to next level
            game_state.level += 1
            
            # Add level completion bonus
            level_bonus = game_state.level * 100
            game_state.score += level_bonus
            
            # Replenish missiles
            for base in game_state.bases:
                if base.alive:
                    base.missiles += 10
            
            # Randomize star positions for visual effect
            game_state.background_stars = []
            num_stars = random.randint(15, 25)
            for _ in range(num_stars):
                col = random.randint(0, BOARD_WIDTH - 1)
                row = random.randint(0, GROUND_ROW - 2)
                game_state.background_stars.append((row, col))
            
            # Reset spawn timer
            game_state.last_enemy_spawn = time.time()
            game_state.frame_count = 0  # Reset frame count for new level
            
            # Small chance for power-up
            if random.random() < 0.3:
                power_ups = ["large_explosion", "faster_missiles", "extra_missiles"]
                game_state.power_up_active = True
                game_state.power_up_type = random.choice(power_ups)
                game_state.power_up_end_time = current_time + 30  # 30 seconds
                
                # Apply power-up effects
                if game_state.power_up_type == "extra_missiles":
                    for base in game_state.bases:
                        if base.alive:
                            base.missiles += 5
    
    # Update board with current game state
    game_state.update_board()
    
    # Increment frame counter
    game_state.frame_count += 1

# Initialize game state in session state
if 'missile_command_game' not in st.session_state:
    st.session_state.missile_command_game = GameState()
    st.session_state.game_start_time = time.time()
    st.session_state.selected_base = 1  # Middle base selected by default
    st.session_state.high_score = 0

# In your main() function, modify the header to be more compact:
def main():    
    # Sidebar for controls
    with st.sidebar:
        st.header("Game Controls")
        
        # New game button
        if st.button("🎮 New Game", key="new_game_btn", use_container_width=True):
            reset_game()
            st.rerun()
        
        # Change base button
        if st.button("🔄 Change Base", key="change_base_btn", use_container_width=True):
            game_state = st.session_state.missile_command_game
            # Find next active base
            current = st.session_state.selected_base
            for i in range(1, len(game_state.bases) + 1):
                next_base = (current + i) % len(game_state.bases)
                if game_state.bases[next_base].alive and game_state.bases[next_base].missiles > 0:
                    st.session_state.selected_base = next_base
                    break
            st.rerun()
        
        # Game stats
        st.markdown("---")
        st.markdown("### Game Status")
        
        game_state = st.session_state.missile_command_game
        
        # Show score with fancy styling
        st.markdown(f'<p class="score-display">Score: {game_state.score}</p>', unsafe_allow_html=True)
        st.markdown(f"**Level:** {game_state.level}")
        st.markdown(f"**High Score:** {st.session_state.high_score}")
        
        # City status
        cities_alive = sum(1 for city in game_state.cities if city.alive)
        st.markdown(f"**Cities:** {cities_alive}/{len(game_state.cities)}")
        
        # Missile count
        total_missiles = 0
        for i, base in enumerate(game_state.bases):
            if base.alive:
                label = "**" if i == st.session_state.selected_base else ""
                st.markdown(f"{label}Base {i+1}: {base.missiles} missiles{label}")
                total_missiles += base.missiles
        
        st.markdown(f"**Total Missiles:** {total_missiles}")
        
        # Show combo counter if active
        if game_state.combo_count >= 3:
            st.success(f"**Combo: x{game_state.combo_count}!**")
        
        # Show power-up if active
        if game_state.power_up_active:
            power_up_name = game_state.power_up_type.replace('_', ' ').title()
            st.info(f"**Power-up: {power_up_name}!**")
            remaining = max(0, int(game_state.power_up_end_time - time.time()))
            st.progress(remaining / 30)  # Assuming 30 second duration
        
        # Game instructions
        st.markdown("---")
        with st.expander("How to Play", expanded=False):
            st.markdown("""
            1. Click on the game grid to fire missiles
            2. Defend your cities (🏙️) from enemy missiles (💣)
            3. Use the **Change Base** button to switch launch sites (🚀)
            4. Each missile base has a limited missile supply
            5. Advance to the next level by destroying all enemy missiles
            
            ### Missile Types:
            - 💣 Regular missiles - Standard threat
            - ⚡ Fast missiles - Move quickly, harder to hit
            - 🧨 Splitting missiles - Split into multiple missiles when destroyed
            
            ### Tips:
            - Watch for combos - hitting multiple missiles in succession rewards bonus points
            - Power-ups appear between levels for special bonuses
            - Prioritize protecting your cities - you lose if all cities are destroyed
            """)
        
        st.markdown("### Legend")
        st.markdown("""
        - 🏙️ : City (protect these!)
        - 🚀 : Missile Base
        - 💣 : Enemy Missile
        - ⚡ : Fast Missile
        - 🧨 : Splitting Missile
        - ⤴️ : Your Missile
        - 💥 : Explosion
        - 🔥 : Destroyed City
        - 🧱 : Destroyed Base
        """)
    
    # Get game state
    game_state = st.session_state.missile_command_game
    
    # Update game state
    update_game(game_state)
    
    # Create a more compact header
    if game_state.game_over:
        st.markdown(f'<h3 class="game-header">Game Over! Score: {game_state.score}</h3>', 
                   unsafe_allow_html=True)
    else:
        selected_base = game_state.bases[st.session_state.selected_base]
        base_status = f"Base {st.session_state.selected_base + 1}: {selected_base.missiles} missiles"
        # More compact header with columns
        cols = st.columns([1, 1])
        with cols[0]:
            st.markdown(f"#### Level {game_state.level}")
        with cols[1]:
            st.markdown(f"#### {base_status}")
    
    # Create container for board
    board_container = st.container()
    
    # Display the board with clickable cells
    with board_container:
        for row in range(BOARD_HEIGHT):
            # Create a row of buttons
            cols = st.columns(BOARD_WIDTH)
            for col in range(BOARD_WIDTH):
                cell_content = game_state.board[row][col]
                
                # Make buttons non-interactable if game over or in ground row
                disabled = game_state.game_over or row == GROUND_ROW
                
                # When cell is clicked, fire missile to that location
                if cols[col].button(cell_content, key=f"cell_{row}_{col}", disabled=disabled):
                    if not game_state.game_over:
                        if fire_player_missile(game_state, col, row):
                            st.rerun()  # Force refresh after firing
    
    # Show restart button if game over
    if game_state.game_over:
        if st.button("Play Again", key="play_again_btn", use_container_width=True):
            reset_game()
            st.rerun()

if __name__ == "__main__":
    main()



