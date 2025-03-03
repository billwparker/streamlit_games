import streamlit as st
import numpy as np
import io
from PIL import Image
import math
import time
import os

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
    
    /* Reduce space between elements */
    h1 {
        margin-bottom: 0.5rem !important;
        padding-bottom: 0 !important;
    }
    
    /* Reduce spacing around containers */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Tighten up spacing between elements */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
    }
    
    /* Create more compact layout */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: 0.5rem !important;
        padding-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Lower the refresh rate for smoother animation with less flashing
from streamlit_autorefresh import st_autorefresh
count = st_autorefresh(interval=300, limit=None, key="home_autorefresh") # Faster refresh (300ms)

# Initialize session state for animation
if "position_x" not in st.session_state:
    st.session_state.position_x = -50
    st.session_state.cycle = 0
    # Initialize drawing parameters that remain constant
    st.session_state.frame_counter = 0

# Create necessary directories to avoid MediaFileHandler errors
os.makedirs(os.path.join(os.path.dirname(__file__), "assets", "images"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "assets", "audio"), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "assets", "fonts"), exist_ok=True)

# Create a function to generate an animation frame - avoid importing pygame here
def generate_animation_frame(width, height):
    # Get state values
    position_x = st.session_state.position_x
    cycle = st.session_state.cycle
    
    # Update position for next frame
    position_x += 6  # Faster movement (increased from 3 to 6)
    if position_x > width + 50:
        position_x = -50
    
    # Increment animation cycle
    cycle = (cycle + 1) % 15  # Faster cycle (decreased from 20 to 15)
    
    # Save updated state
    st.session_state.position_x = position_x
    st.session_state.cycle = cycle
    st.session_state.frame_counter += 1
    
    # Create an image directly using PIL instead of pygame
    # This avoids potential pygame initialization issues
    img = Image.new('RGB', (width, height), (245, 245, 245))  # Light background
    
    # Draw using PIL's ImageDraw
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(img)
    
    # Draw ground line
    ground_y = height - 20
    draw.line([(0, ground_y), (width, ground_y)], fill=(100, 100, 100), width=2)
    
    # Draw background elements - buildings
    building_positions = [width * 0.1, width * 0.3, width * 0.5, width * 0.7, width * 0.9]
    building_heights = [40, 50, 35, 55, 45]  # Fixed heights
    
    for i, x_pos in enumerate(building_positions):
        x_pos = int(x_pos)
        height_var = building_heights[i % len(building_heights)]
        draw.rectangle(
            [(x_pos - 15, ground_y - height_var), (x_pos + 15, ground_y)],
            fill=(0, 70, 190)
        )
    
    # Drawing the stick figure
    head_radius = 15
    head_x = int(position_x)
    head_y = ground_y - 60
    
    # Draw head - circle
    draw.ellipse(
        [(head_x - head_radius, head_y - head_radius), 
         (head_x + head_radius, head_y + head_radius)],
        outline=(30, 30, 30),
        width=2
    )
    
    # Draw body - line
    body_end_y = ground_y - 25
    draw.line([(head_x, head_y + head_radius), (head_x, body_end_y)], 
              fill=(30, 30, 30), width=2)
    
    # Draw arms with animation - faster arm movements
    arm_angle = math.sin(cycle * 0.4) * 0.7  # Increased amplitude and frequency
    arm_length = 20
    
    # Left arm
    left_arm_x = int(head_x - math.cos(arm_angle) * arm_length)
    left_arm_y = int(head_y + head_radius + 10 - math.sin(arm_angle) * arm_length)
    draw.line([(head_x, head_y + head_radius + 10), (left_arm_x, left_arm_y)], 
              fill=(30, 30, 30), width=2)
    
    # Right arm
    right_arm_x = int(head_x + math.cos(arm_angle) * arm_length)
    right_arm_y = int(head_y + head_radius + 10 + math.sin(arm_angle) * arm_length)
    draw.line([(head_x, head_y + head_radius + 10), (right_arm_x, right_arm_y)], 
              fill=(30, 30, 30), width=2)
    
    # Draw legs with animation - faster leg movements
    leg_length = 25
    leg_angle = math.sin(cycle * 0.4) * 0.6  # Increased amplitude and frequency
    
    # Left leg
    left_leg_x = int(head_x - math.sin(leg_angle) * leg_length)
    left_leg_y = ground_y
    draw.line([(head_x, body_end_y), (left_leg_x, left_leg_y)], 
              fill=(30, 30, 30), width=2)
    
    # Right leg
    right_leg_x = int(head_x + math.sin(leg_angle) * leg_length)
    right_leg_y = ground_y
    draw.line([(head_x, body_end_y), (right_leg_x, right_leg_y)], 
              fill=(30, 30, 30), width=2)
    
    # Draw shadow - ellipse
    shadow_width = 20 + abs(math.sin(cycle * 0.3) * 8)
    draw.ellipse(
        [(head_x - shadow_width/2, ground_y - 4), 
         (head_x + shadow_width/2, ground_y + 4)],
        fill=(200, 200, 200)
    )
    
    return img

# First, create a container for the title to prevent it from moving - reduce margins
st.markdown('<h1 style="margin-bottom:0">🎮 Welcome to Transgressive Games</h1>', unsafe_allow_html=True)

# Create a placeholder for our animation - use a compact layout
animation_container = st.container()
with animation_container:
    # Removed extra margin around animation container
    st.markdown('<div class="animation-container" style="margin-top:-200px">', unsafe_allow_html=True)
    animation_placeholder = st.empty()
    st.markdown('</div>', unsafe_allow_html=True)

# Generate and display the current animation frame
frame = generate_animation_frame(600, 100)
animation_placeholder.image(frame, use_container_width=True)

# Main content - stays fixed when animation updates
st.markdown("""

Transgressive art intentionally pushes boundaries to provoke a reaction, spark 
dialogue, and sometimes inspire change. This is commonly seen in works that 
address political or social themes where the medium and subject 
matter combine to challenge the status quo. But transgressive art can 
also be about using a medium not
typically associated with a given style simply to disrupt conventional aesthetics or 
to invite viewers to re-examine their expectations.

Similarly, this project is a form of what we are calling "Transgressive Gaming" to
demonstrate how to build interactive games in a minimalistic and in an almost anti-UX
pattern.

Each game here explores different techniques from ASCII to Emojis and sometimes PyGame 
for creating interactive experiences within the Streamlit framework - a framework not
typically associated with game development.
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
