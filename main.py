import streamlit as st
import pygame
import numpy as np
from PIL import Image
import io
import random
import math
import time
from dataclasses import dataclass
from typing import List, Tuple

# Import our custom modules
from game_state import save_game_state, load_game_state, clear_game_state

# Game settings
GAME_WIDTH = 800
GAME_HEIGHT = 600
BG_COLOR = (0, 0, 0)  # Black background
WHITE = (255, 255, 255)
FPS = 30
REFRESH_INTERVAL = 500  # Refresh rate in milliseconds

# Initialize Streamlit page with auto-refresh and sidebar - MUST BE FIRST ST COMMAND
st.set_page_config(
    page_title="Streamlit Asteroids",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import and initialize the autorefresh
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=REFRESH_INTERVAL, key="game_autorefresh")

# Game difficulty scaling - significantly increase asteroid speeds
MIN_ASTEROID_SPEED = 3.0
MAX_ASTEROID_SPEED = 6.0
ASTEROID_SPAWN_INTERVAL = 300
ASTEROID_MAX_COUNT = 10

# Debug mode - set to True to show debugging info
DEBUG_MODE = True

# Create sidebar for controls
with st.sidebar:
    st.title("Asteroid Controls")
    
    # Initialize pygame
    pygame.init()

# Main area title
st.title("Streamlit Asteroids")

# Game classes
@dataclass
class Ship:
    x: float
    y: float
    angle: float
    speed: float = 0
    radius: int = 15
    
    def update(self):
        # Update position based on speed and angle
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y -= self.speed * math.sin(math.radians(self.angle))
        
        # Wrap around screen edges
        self.x %= GAME_WIDTH
        self.y %= GAME_HEIGHT
        
        # Apply drag
        self.speed *= 0.98
    
    def rotate(self, direction):
        self.angle += direction * 10
    
    def thrust(self):
        self.speed += 0.2
        if self.speed > 8:
            self.speed = 8
    
    def get_points(self):
        # Calculate ship points for drawing
        nose_x = self.x + self.radius * math.cos(math.radians(self.angle))
        nose_y = self.y - self.radius * math.sin(math.radians(self.angle))
        
        left_x = self.x + self.radius * math.cos(math.radians(self.angle + 140))
        left_y = self.y - self.radius * math.sin(math.radians(self.angle + 140))
        
        right_x = self.x + self.radius * math.cos(math.radians(self.angle - 140))
        right_y = self.y - self.radius * math.sin(math.radians(self.angle - 140))
        
        return [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]

@dataclass
class Asteroid:
    x: float
    y: float
    dx: float
    dy: float
    radius: int
    rotation: float = 0
    rotation_speed: float = 0
    
    def update(self):
        """Update asteroid position and rotation"""
        # Store original position for debugging
        old_x, old_y = self.x, self.y
        
        # Move the asteroid by velocity components
        self.x += self.dx
        self.y += self.dy
        
        # Rotate the asteroid
        self.rotation += self.rotation_speed
        
        # Handle screen wrapping differently
        if self.x < -self.radius * 2:
            self.x = GAME_WIDTH + self.radius
        elif self.x > GAME_WIDTH + self.radius * 2:
            self.x = -self.radius
            
        if self.y < -self.radius * 2:
            self.y = GAME_HEIGHT + self.radius
        elif self.y > GAME_HEIGHT + self.radius * 2:
            self.y = -self.radius
            
        # Debug logging
        if DEBUG_MODE and (abs(old_x - self.x) > 0.1 or abs(old_y - self.y) > 0.1):
            print(f"Asteroid moved: ({old_x:.1f}, {old_y:.1f}) -> ({self.x:.1f}, {self.y:.1f}), vel=({self.dx:.1f}, {self.dy:.1f})")

    def get_points(self):
        """Generate points for drawing the asteroid"""
        points = []
        num_points = 12  # Increased from 8 for less blocky appearance
        # Fixed variation for each vertex to create consistent shape
        variations = [random.uniform(-self.radius * 0.3, self.radius * 0.3) for _ in range(num_points)]
        
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points + self.rotation
            r = self.radius + variations[i]  # Use pre-calculated variation
            points.append((
                self.x + r * math.cos(angle),
                self.y + r * math.sin(angle)
            ))
        return points

@dataclass
class Bullet:
    x: float
    y: float
    angle: float
    speed: float = 10
    life: int = 60  # Frames the bullet lives for
    radius: int = 2  # Add radius property for collision detection
    
    def update(self):
        # Move the bullet
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y -= self.speed * math.sin(math.radians(self.angle))
        
        # Wrap around screen edges
        self.x %= GAME_WIDTH
        self.y %= GAME_HEIGHT
        
        # Decrease life
        self.life -= 1

# Game functions
def check_collision(obj1, obj2):
    # Simple distance-based collision detection
    dist = math.sqrt((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2)
    return dist < (obj1.radius + obj2.radius)

def create_asteroid(size="large", near_ship=False):
    """Create an asteroid with random position and direction"""
    size_map = {"large": 50, "medium": 25, "small": 12}
    
    # Start asteroids away from the center
    side = random.choice(["top", "right", "bottom", "left"])
    if side == "top":
        x = random.randint(0, GAME_WIDTH)
        y = random.randint(-100, 0)  # Start off-screen for smoother entry
    elif side == "right":
        x = random.randint(GAME_WIDTH, GAME_WIDTH + 100)
        y = random.randint(0, GAME_HEIGHT)
    elif side == "bottom":
        x = random.randint(0, GAME_WIDTH)
        y = random.randint(GAME_HEIGHT, GAME_HEIGHT + 100)
    else:  # left
        x = random.randint(-100, 0)
        y = random.randint(0, GAME_HEIGHT)
    
    # Generate velocity components directly rather than using angle
    dx = random.uniform(-MAX_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    while -0.5 < dx < 0.5:  # Ensure non-zero x velocity
        dx = random.uniform(-MAX_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    
    dy = random.uniform(-MAX_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    while -0.5 < dy < 0.5:  # Ensure non-zero y velocity
        dy = random.uniform(-MAX_ASTEROID_SPEED, MAX_ASTEROID_SPEED)
    
    # Make sure we're at least at the minimum speed
    speed = math.sqrt(dx*dx + dy*dy)
    if speed < MIN_ASTEROID_SPEED:
        scale_factor = MIN_ASTEROID_SPEED / speed
        dx *= scale_factor
        dy *= scale_factor
    
    # Set rotation
    rotation = random.uniform(0, 2 * math.pi)
    rotation_speed = random.uniform(0.02, 0.1) * random.choice([-1, 1])
    
    radius = size_map[size]
    
    # Debug output
    if DEBUG_MODE:
        print(f"Created asteroid: pos=({x}, {y}), vel=({dx:.1f}, {dy:.1f}), size={size}")
    
    return Asteroid(
        x=x, 
        y=y, 
        dx=dx, 
        dy=dy, 
        radius=radius, 
        rotation=rotation, 
        rotation_speed=rotation_speed
    )

# Load or initialize game state
saved_state = load_game_state()

# Add a new game_active flag to track if the game is actually started
if "game_active" not in st.session_state:
    st.session_state.game_active = saved_state.get('game_active', False)

# Game state in session state
if "game_initialized" not in st.session_state:
    st.session_state.game_initialized = False
    st.session_state.score = saved_state.get('score', 0)
    st.session_state.lives = saved_state.get('lives', 3)
    st.session_state.game_over = saved_state.get('game_over', False)
    st.session_state.ship = None
    st.session_state.asteroids = []
    st.session_state.bullets = []
    st.session_state.frame_count = saved_state.get('frame_count', 0)
    st.session_state.last_update_time = time.time()
    st.session_state.last_fire_time = 0
    st.session_state.last_asteroid_spawn = 0  # Track last asteroid spawn time

def initialize_game():
    """Initialize game objects but don't start the game yet"""
    st.session_state.ship = Ship(x=GAME_WIDTH/2, y=GAME_HEIGHT/2, angle=90)
    
    # Create a few initial asteroids that are always moving even before game starts
    st.session_state.asteroids = [create_asteroid() for _ in range(2)]
    
    st.session_state.bullets = []
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.game_over = False
    st.session_state.frame_count = 0
    st.session_state.last_update_time = time.time()
    st.session_state.last_fire_time = 0
    st.session_state.last_asteroid_spawn = 0
    st.session_state.game_initialized = True
    st.session_state.game_active = False

def start_game():
    """Start the actual game with additional asteroids"""
    # Add more asteroids to the existing ones
    for _ in range(3):  # Add 3 more for a total of 5 asteroids
        asteroid = create_asteroid()
        # Ensure asteroid is moving fast enough
        speed = math.sqrt(asteroid.dx**2 + asteroid.dy**2)
        if speed < MIN_ASTEROID_SPEED:
            scale_factor = MIN_ASTEROID_SPEED / speed
            asteroid.dx *= scale_factor
            asteroid.dy *= scale_factor
        st.session_state.asteroids.append(asteroid)
    
    st.session_state.game_active = True

def restart_game():
    """Restart the game from scratch"""
    clear_game_state()
    initialize_game()
    start_game()
    st.rerun()

def render_game():
    # Create a surface to draw on
    surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    surface.fill(BG_COLOR)
    
    # Draw the ship
    if st.session_state.ship:
        points = st.session_state.ship.get_points()
        pygame.draw.polygon(surface, WHITE, points, 2)
    
    # Draw asteroids
    for asteroid in st.session_state.asteroids:
        points = asteroid.get_points()
        pygame.draw.polygon(surface, WHITE, points, 2)
    
    # Draw bullets - update to use the bullet's radius
    for bullet in st.session_state.bullets:
        pygame.draw.circle(surface, WHITE, (int(bullet.x), int(bullet.y)), bullet.radius)
    
    # Convert pygame surface to an image for Streamlit
    image_data = pygame.image.tostring(surface, 'RGB')
    image = Image.frombytes('RGB', (GAME_WIDTH, GAME_HEIGHT), image_data)
    
    return image

def update_game():
    if st.session_state.game_over:
        return
    
    # Always update asteroids, even if game not active
    # Update asteroids - always move asteroids regardless of player interaction
    for asteroid in st.session_state.asteroids:
        asteroid.update()
    
    # If game is not active, just update rotating ship and asteroids, skip other logic
    if not st.session_state.game_active:
        # If game is not active but we have a ship, gently rotate it for visual effect
        if st.session_state.ship:
            st.session_state.ship.angle += 0.2
        
        # Periodically spawn a new asteroid even when game isn't active
        if (len(st.session_state.asteroids) < 3 and 
                st.session_state.frame_count % 300 == 0):
            st.session_state.asteroids.append(create_asteroid())
        
        st.session_state.frame_count += 1
        return
    
    # Update ship
    if st.session_state.ship:
        st.session_state.ship.update()
    
    # Debug counter for asteroid movement
    moved_asteroids = 0
    
    # Update asteroids - always move asteroids regardless of player interaction
    for asteroid in st.session_state.asteroids:
        old_x, old_y = asteroid.x, asteroid.y
        asteroid.update()
        # Check if asteroid actually moved
        if old_x != asteroid.x or old_y != asteroid.y:
            moved_asteroids += 1
    
    # Log asteroid movement for debugging
    if st.session_state.frame_count % 30 == 0:  # Log every 30 frames
        print(f"Frame {st.session_state.frame_count}: {moved_asteroids}/{len(st.session_state.asteroids)} asteroids moved")
        for i, asteroid in enumerate(st.session_state.asteroids[:3]):  # Log first 3 asteroids
            print(f"  Asteroid {i}: pos=({asteroid.x:.1f}, {asteroid.y:.1f}), vel=({asteroid.dx:.1f}, {asteroid.dy:.1f})")
    
    # Update bullets and remove dead ones
    st.session_state.bullets = [bullet for bullet in st.session_state.bullets if bullet.life > 0]
    for bullet in st.session_state.bullets:
        bullet.update()
    
    # Check for bullet-asteroid collisions
    new_asteroids = []
    for bullet in list(st.session_state.bullets):
        hit = False
        for asteroid in list(st.session_state.asteroids):
            if check_collision(bullet, asteroid):
                # Remove the bullet and asteroid
                if bullet in st.session_state.bullets:
                    st.session_state.bullets.remove(bullet)
                if asteroid in st.session_state.asteroids:
                    st.session_state.asteroids.remove(asteroid)
                hit = True
                
                # Update score
                if asteroid.radius >= 50:  # Large
                    st.session_state.score += 20
                    # Split into medium asteroids
                    for _ in range(2):
                        new_asteroid = Asteroid(
                            x=asteroid.x, 
                            y=asteroid.y,
                            dx=random.uniform(-2, 2),
                            dy=random.uniform(-2, 2),
                            radius=25
                        )
                        new_asteroids.append(new_asteroid)
                elif asteroid.radius >= 25:  # Medium
                    st.session_state.score += 50
                    # Split into small asteroids
                    for _ in range(2):
                        new_asteroid = Asteroid(
                            x=asteroid.x, 
                            y=asteroid.y,
                            dx=random.uniform(-3, 3),
                            dy=random.uniform(-3, 3),
                            radius=12
                        )
                        new_asteroids.append(new_asteroid)
                else:  # Small
                    st.session_state.score += 100
                
                # Don't check this bullet against other asteroids
                if hit:
                    break
    
    # Add the new asteroids from splitting
    st.session_state.asteroids.extend(new_asteroids)
    
    # Check if ship collided with an asteroid
    if st.session_state.ship:
        for asteroid in list(st.session_state.asteroids):
            if check_collision(st.session_state.ship, asteroid):
                st.session_state.lives -= 1
                # Reset ship position
                st.session_state.ship = Ship(x=GAME_WIDTH/2, y=GAME_HEIGHT/2, angle=90)
                break
    
    # Spawn new asteroids periodically if there are too few
    if (len(st.session_state.asteroids) < ASTEROID_MAX_COUNT and 
            st.session_state.frame_count - st.session_state.last_asteroid_spawn > ASTEROID_SPAWN_INTERVAL):
        spawn_chance = min(0.8, 0.3 + st.session_state.score / 1000)
        if random.random() < spawn_chance:
            st.session_state.asteroids.append(create_asteroid())
            st.session_state.last_asteroid_spawn = st.session_state.frame_count
    
    # Check game over
    if st.session_state.lives <= 0:
        st.session_state.game_over = True
    
    # Increment frame counter
    st.session_state.frame_count += 1
    
    # Save game state for the next run
    save_game_state({
        'score': st.session_state.score,
        'lives': st.session_state.lives,
        'game_over': st.session_state.game_over,
        'ship': st.session_state.ship,
        'asteroids': st.session_state.asteroids,
        'bullets': st.session_state.bullets,
        'frame_count': st.session_state.frame_count,
        'last_update_time': time.time(),
        'game_active': st.session_state.game_active,
        'last_asteroid_spawn': st.session_state.last_asteroid_spawn
    })

# Initialize the game if not already done
if not st.session_state.game_initialized:
    if 'ship' in saved_state:
        try:
            # Reconstruct objects from saved state
            ship_data = saved_state.get('ship')
            if ship_data:
                st.session_state.ship = Ship(**ship_data)
                
            asteroid_data_list = saved_state.get('asteroids', [])
            st.session_state.asteroids = [Asteroid(**data) for data in asteroid_data_list]
            
            bullet_data_list = saved_state.get('bullets', [])
            st.session_state.bullets = [Bullet(**data) for data in bullet_data_list]
            
            st.session_state.game_initialized = True
            st.session_state.game_active = saved_state.get('game_active', False)
        except Exception as e:
            # If reconstruction fails, initialize a new game
            initialize_game()
    else:
        initialize_game()

# Calculate time delta for consistent game speed
current_time = time.time()
if 'last_update_time' in st.session_state:
    delta_time = current_time - st.session_state.last_update_time
    # If too much time has passed (e.g., after page reload), cap it
    if delta_time > 0.1:
        delta_time = 0.033  # ~30 FPS
else:
    delta_time = 0.033

st.session_state.last_update_time = current_time

# Always update game state to ensure continuous motion
update_game()

# Display score and lives at the top
score_lives_container = st.container()
with score_lives_container:
    # Only show score when game is active
    if st.session_state.game_active:
        st.markdown(f"### **Score:** {st.session_state.score} | **Lives:** {st.session_state.lives}")
    else:
        st.markdown("### Welcome to Asteroids!")

# Render the current game state in the main area
game_image = render_game()
game_container = st.empty()
game_container.image(game_image, caption="Asteroids Game", use_column_width=True)

# Game over message
if st.session_state.game_over:
    st.error(f"Game Over! Your final score: {st.session_state.score}")
    with st.sidebar:
        if st.button("Play Again", key="play_again"):
            restart_game()
else:
    # Move all controls to sidebar
    with st.sidebar:
        # Game management - Start/Restart button first
        st.markdown("### Game Management")
        
        # Change button text based on game state
        if not st.session_state.game_active:
            start_button_text = "▶️ Start Game"
            if st.button(start_button_text, key="start_game", use_container_width=True):
                start_game()
                st.rerun()
        else:
            restart_button_text = "⟳ Restart Game"
            if st.button(restart_button_text, key="restart_game", use_container_width=True):
                restart_game()
        
        # Only show game controls if the game is active
        if st.session_state.game_active:
            st.markdown("---")
            st.markdown("### Manual Controls")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("↺ Rotate Left", key="rotate_left"):
                    if st.session_state.ship:
                        st.session_state.ship.rotate(5)
            
            with col2:
                if st.button("↻ Rotate Right", key="rotate_right"):
                    if st.session_state.ship:
                        st.session_state.ship.rotate(-5)
            
            if st.button("🚀 Thrust", key="thrust", use_container_width=True):
                if st.session_state.ship:
                    st.session_state.ship.thrust()
            
            if st.button("🔥 Fire", key="fire", use_container_width=True):
                if st.session_state.ship and len(st.session_state.bullets) < 5:
                    points = st.session_state.ship.get_points()
                    nose = points[0]
                    bullet = Bullet(
                        x=nose[0], 
                        y=nose[1], 
                        angle=st.session_state.ship.angle,
                        radius=2
                    )
                    st.session_state.bullets.append(bullet)
        
        # Always show instructions
        st.markdown("---")
        st.markdown("### How to Play")
        st.markdown("""
        - Use the controls to navigate your ship
        - Shoot asteroids to earn points
        - Avoid collisions with asteroids
        - Larger asteroids break into smaller ones when shot
        
        ### Tips
        - Keep moving to avoid asteroids
        - Use momentum to your advantage
        - Fire carefully - you can only have 5 bullets at a time
        """)

# Show welcome message if game is not active
if not st.session_state.game_active and not st.session_state.game_over:
    st.markdown("""
    ## Welcome to Streamlit Asteroids!
    
    Use the Start Game button in the sidebar to begin.
    
    ### Objective:
    Shoot asteroids and avoid collisions. Larger asteroids break into smaller ones when shot.
    """)
else:
    st.markdown("""
    ---
    This game uses auto-refresh to create a game loop. For best results, play in full screen mode!
    """)
