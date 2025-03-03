import streamlit as st
import pygame
import numpy as np
import io
from PIL import Image
import math
import time

# Configure the page with wider layout and without scrolling
st.set_page_config(
    page_title="Streamlit Games",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Use custom CSS to minimize flashing and prevent scrolling
st.markdown("""
<style>
    /* Reduce animation flicker effect */
    img {
        transition: none !important;
    }
    
    /* Prevent auto-scrolling */
    html {
        scroll-behavior: auto !important;
    }
    
    /* Fix footer at bottom to prevent layout shift */
    footer {
        position: fixed;
        bottom: 0;
        width: 100%;
    }
    
    /* Hide streamlit's default rerun spinner that causes flashing */
    .stSpinner {
        display: none !important;
    }
    
    /* Prevent content shift on rerun */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Make animation container fixed height */
    .animation-container {
        height: 100px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Lower the refresh rate for smoother animation with less flashing
from streamlit_autorefresh import st_autorefresh
count = st_autorefresh(interval=100, limit=None, key="home_autorefresh")

# Initialize session state for animation - add frame buffer to reduce flashing
if "position_x" not in st.session_state:
    st.session_state.position_x = -50
    st.session_state.cycle = 0
    # Generate a fixed background once to avoid regenerating it every frame
    st.session_state.background = None
    # Cache the last frame to reduce computation
    st.session_state.last_frame_time = 0
    st.session_state.cached_frame = None
    # Previous scrollY position
    st.session_state.scroll_pos = 0

# Create a function to generate an animation frame with Pygame
def generate_animation_frame(width, height):
    # Use frame caching to reduce CPU usage and flashing
    current_time = time.time()
    if (st.session_state.cached_frame is not None and 
        current_time - st.session_state.last_frame_time < 0.08):  # Only update every ~80ms
        return st.session_state.cached_frame
    
    # Get state values
    position_x = st.session_state.position_x
    cycle = st.session_state.cycle
    
    # Update position for next frame
    position_x += 3  # Slower movement (was 5)
    if position_x > width + 50:
        position_x = -50
    
    # Increment animation cycle
    cycle = (cycle + 1) % 20  # Slower animation cycle (was 10)
    
    # Save updated state
    st.session_state.position_x = position_x
    st.session_state.cycle = cycle
    
    # Initialize pygame surface
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Generate or reuse background
    if st.session_state.background is None:
        # Create a new background
        background = pygame.Surface((width, height), pygame.SRCALPHA)
        background.fill((245, 245, 245))  # Light background
        
        # Colors
        BLUE = (0, 70, 190)
        
        # Ground line
        ground_y = height - 20
        pygame.draw.line(background, (100, 100, 100), (0, ground_y), (width, ground_y), 2)
        
        # Draw some background elements for depth
        # Trees or buildings in the distance - use fixed positions
        building_positions = [width * 0.1, width * 0.3, width * 0.5, width * 0.7, width * 0.9]
        building_heights = [40, 50, 35, 55, 45]  # Fixed heights to prevent flicker
        
        for i, x_pos in enumerate(building_positions):
            height_var = building_heights[i % len(building_heights)]
            pygame.draw.rect(background, BLUE, (x_pos - 15, ground_y - height_var, 30, height_var))
        
        st.session_state.background = background
    
    # Blit the cached background to avoid regenerating it
    surface.blit(st.session_state.background, (0, 0))
    
    # Rest of drawing code remains the same
    BLACK = (30, 30, 30)
    ground_y = height - 20
    
    # Draw stick figure at the current position
    head_radius = 15
    head_x = position_x
    head_y = ground_y - 60
    
    # Draw head
    pygame.draw.circle(surface, BLACK, (head_x, head_y), head_radius, 2)
    
    # Draw body
    body_end_y = ground_y - 25
    pygame.draw.line(surface, BLACK, (head_x, head_y + head_radius), (head_x, body_end_y), 2)
    
    # Draw arms with animation - smoother movement with adjusted animation speed
    arm_angle = math.sin(cycle * 0.3) * 0.5  # Slower arm swing
    arm_length = 20
    
    # Left arm
    left_arm_x = head_x - math.cos(arm_angle) * arm_length
    left_arm_y = head_y + head_radius + 10 - math.sin(arm_angle) * arm_length
    pygame.draw.line(surface, BLACK, (head_x, head_y + head_radius + 10), (left_arm_x, left_arm_y), 2)
    
    # Right arm (opposite phase)
    right_arm_x = head_x + math.cos(arm_angle) * arm_length
    right_arm_y = head_y + head_radius + 10 + math.sin(arm_angle) * arm_length
    pygame.draw.line(surface, BLACK, (head_x, head_y + head_radius + 10), (right_arm_x, right_arm_y), 2)
    
    # Draw legs with animation - smoother movement
    leg_length = 25
    leg_angle = math.sin(cycle * 0.3) * 0.4  # Slower leg swing
    
    # Left leg
    left_leg_x = head_x - math.sin(leg_angle) * leg_length
    left_leg_y = ground_y
    pygame.draw.line(surface, BLACK, (head_x, body_end_y), (left_leg_x, left_leg_y), 2)
    
    # Right leg (opposite phase)
    right_leg_x = head_x + math.sin(leg_angle) * leg_length
    right_leg_y = ground_y
    pygame.draw.line(surface, BLACK, (head_x, body_end_y), (right_leg_x, right_leg_y), 2)
    
    # Draw a small shadow
    shadow_width = 20 + abs(math.sin(cycle * 0.3) * 8)  # Shadow width changes with step
    ellipse_rect = pygame.Rect(head_x - shadow_width/2, ground_y - 4, shadow_width, 8)
    pygame.draw.ellipse(surface, (200, 200, 200), ellipse_rect)
    
    # Convert the pygame surface to a PIL Image
    img_data = pygame.image.tostring(surface, 'RGBA')
    img = Image.frombytes('RGBA', (width, height), img_data)
    
    # Cache the frame
    st.session_state.cached_frame = img
    st.session_state.last_frame_time = current_time
    
    return img

# Initialize pygame for drawing
pygame.init()

# Animation settings
WIDTH = 600
HEIGHT = 100

# First, create a container for the title to prevent it from moving
st.markdown('<h1>🎮 Welcome to Streamlit Games</h1>', unsafe_allow_html=True)

# Create a placeholder for our animation
animation_container = st.container()
with animation_container:
    st.markdown('<div class="animation-container">', unsafe_allow_html=True)
    animation_placeholder = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# Generate and display the current animation frame
frame = generate_animation_frame(WIDTH, HEIGHT)
animation_placeholder.image(frame, use_container_width=True)

# Main content - stays fixed when animation updates
st.markdown("""

This project demonstrates how to build interactive games using Streamlit.
""")

# Add JavaScript to maintain scroll position
js = """
<script>
    // Store scroll position before Streamlit rerun
    window.addEventListener('beforeunload', function() {
        sessionStorage.setItem('scrollY', window.scrollY);
    });
    
    // Restore scroll position after page loads
    window.addEventListener('load', function() {
        requestAnimationFrame(function() {
            const scrollY = sessionStorage.getItem('scrollY') || 0;
            window.scrollTo(0, scrollY);
        });
    });
</script>
"""
st.markdown(js, unsafe_allow_html=True)

st.sidebar.success("Select a game above to start playing!")
