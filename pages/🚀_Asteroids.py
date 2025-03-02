import streamlit as st
import numpy as np
import time
import random
import math
from PIL import Image, ImageDraw
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Streamlit page with auto-refresh and sidebar - MUST BE FIRST ST COMMAND
st.set_page_config(
    page_title="Asteroids",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import and initialize the autorefresh
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=500, key="asteroids_autorefresh")

# Game settings
GAME_WIDTH = 800
GAME_HEIGHT = 600
BG_COLOR = (0, 0, 0)  # Black background
WHITE = (255, 255, 255)
REFRESH_INTERVAL = 500  # milliseconds

# Game difficulty settings
MIN_ASTEROID_SPEED = 3.0
MAX_ASTEROID_SPEED = 6.0
ASTEROID_SPAWN_INTERVAL = 300
ASTEROID_MAX_COUNT = 10

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
        
        # Apply reduced drag (from 0.98 to 0.99) to maintain speed better
        self.speed *= 0.99
    
    def rotate(self, direction):
        self.angle += direction * 10
    
    def thrust(self):
        # Double the thrust acceleration (from 0.4 to 0.8)
        self.speed += 0.8
        # Double the max speed (from 12 to 24)
        if self.speed > 24:
            self.speed = 24
    
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
        # Move the asteroid by velocity components
        self.x += self.dx
        self.y += self.dy
        
        # Rotate the asteroid
        self.rotation += self.rotation_speed
        
        # Handle screen wrapping
        if self.x < -self.radius * 2:
            self.x = GAME_WIDTH + self.radius
        elif self.x > GAME_WIDTH + self.radius * 2:
            self.x = -self.radius
            
        if self.y < -self.radius * 2:
            self.y = GAME_HEIGHT + self.radius
        elif self.y > GAME_HEIGHT + self.radius * 2:
            self.y = -self.radius

    def get_points(self):
        """Generate points for drawing the asteroid"""
        points = []
        num_points = 12  # More points for smoother appearance
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
    
    return Asteroid(
        x=x, 
        y=y, 
        dx=dx, 
        dy=dy, 
        radius=radius, 
        rotation=rotation, 
        rotation_speed=rotation_speed
    )

# Initialize game state in session state
if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False
    st.session_state.game_active = False
    st.session_state.score = 0
    st.session_state.lives = 3
    st.session_state.game_over = False
    st.session_state.ship = None
    st.session_state.asteroids = []
    st.session_state.bullets = []
    st.session_state.frame_count = 0
    st.session_state.last_update_time = time.time()
    st.session_state.last_fire_time = 0
    st.session_state.last_asteroid_spawn = 0

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
    initialize_game()
    start_game()

def render_game():
    # Create a new image
    img = Image.new('RGB', (GAME_WIDTH, GAME_HEIGHT), color="black")
    draw = ImageDraw.Draw(img)
    
    # Draw the ship if it exists
    if st.session_state.ship:
        points = st.session_state.ship.get_points()
        draw.polygon(points, fill=None, outline="white")
    
    # Draw asteroids
    for asteroid in st.session_state.asteroids:
        points = asteroid.get_points()
        draw.polygon(points, fill=None, outline="white")
    
    # Draw bullets
    for bullet in st.session_state.bullets:
        draw.ellipse([
            bullet.x - bullet.radius, 
            bullet.y - bullet.radius,
            bullet.x + bullet.radius, 
            bullet.y + bullet.radius
        ], fill="white")
    
    return img

def update_game():
    if st.session_state.game_over:
        return
    
    # Always update asteroids, even if game not active
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
                            radius=25,
                            rotation=random.uniform(0, 2 * math.pi),
                            rotation_speed=random.uniform(0.02, 0.1) * random.choice([-1, 1])
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
                            radius=12,
                            rotation=random.uniform(0, 2 * math.pi),
                            rotation_speed=random.uniform(0.02, 0.1) * random.choice([-1, 1])
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

# Initialize the game if not already done
if not st.session_state.game_initialized:
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

# Create a container for game display
game_container = st.empty()

# Sidebar controls and information
with st.sidebar:
    # Game management
    st.markdown("### Game Controls")
    
    # Change button text based on game state
    if not st.session_state.game_active and not st.session_state.game_over:
        if st.button("▶️ Start Game", key="start_game", use_container_width=True):
            start_game()
    
    # Always show restart button
    if st.button("⟳ Restart Game", key="restart_game", use_container_width=True):
        restart_game()
    
    # Only show game controls if the game is active
    if st.session_state.game_active:
        st.markdown("---")
        st.markdown("### Ship Controls")
        
        # Rotation controls in two columns
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↺ Rotate Left", key="rotate_left"):
                if st.session_state.ship:
                    st.session_state.ship.rotate(5)
        
        with col2:
            if st.button("↻ Rotate Right", key="rotate_right"):
                if st.session_state.ship:
                    st.session_state.ship.rotate(-5)
        
        # Thrust and Fire controls in two columns
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("🚀 Thrust", key="thrust", use_container_width=True):
                if st.session_state.ship:
                    st.session_state.ship.thrust()
        
        with action_col2:
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
    
    # Always show score and lives - now in horizontal layout
    st.markdown("---")
    
    # Display Score and Lives in two columns
    stats_col1, stats_col2 = st.columns(2)
    with stats_col1:
        st.markdown(f"### Score: {st.session_state.score}")
    
    if st.session_state.game_active:
        with stats_col2:
            st.markdown(f"### Lives: {st.session_state.lives}")
    
    # Always show instructions
    st.markdown("---")
    st.markdown("### How to Play")
    st.markdown("""
    - Use the controls to navigate your ship
    - Shoot asteroids to earn points
    - Avoid collisions with asteroids
    - Larger asteroids break into smaller ones when shot
    
    ### Scoring
    - Small Asteroid: 100 points
    - Medium Asteroid: 50 points
    - Large Asteroid: 20 points
    """)

# Render the current game state
game_image = render_game()

# Display game over message or game screen
if st.session_state.game_over:
    with game_container:
        st.image(game_image, use_container_width=True)
        st.error(f"Game Over! Your final score: {st.session_state.score}")
        if st.button("Play Again", key="main_play_again"):
            restart_game()
elif not st.session_state.game_active:
    with game_container:
        st.image(game_image, use_container_width=True)
        st.markdown("""
        ## Welcome to Asteroids!
        
        Use the Start Game button in the sidebar to begin.
        
        ### Objective:
        Shoot asteroids and avoid collisions. Larger asteroids break into smaller ones when shot.
        """)
else:
    game_container.image(game_image, use_container_width=True)
