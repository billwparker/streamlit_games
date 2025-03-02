import streamlit as st
import streamlit.components.v1 as components
import time  # Add missing import for time

def keyboard_input():
    """Create a JavaScript component to capture keyboard inputs"""
    components.html(
        """
        <div id="keyboard_input" tabindex="0" style="outline: none; height: 0px; width: 100%;">
        </div>
        
        <script>
            // Initialize key state object
            const keyState = {
                ArrowLeft: false,
                ArrowRight: false,
                ArrowUp: false,
                Space: false
            };
            
            // Get the div element and focus it
            const inputDiv = document.getElementById('keyboard_input');
            inputDiv.focus();
            
            // Add event listeners for key down and key up events
            window.addEventListener('keydown', function(event) {
                if (event.key === 'ArrowLeft') {
                    keyState.ArrowLeft = true;
                    window.parent.postMessage({type: 'keydown', key: 'left'}, '*');
                    event.preventDefault();
                } else if (event.key === 'ArrowRight') {
                    keyState.ArrowRight = true;
                    window.parent.postMessage({type: 'keydown', key: 'right'}, '*');
                    event.preventDefault();
                } else if (event.key === 'ArrowUp') {
                    keyState.ArrowUp = true;
                    window.parent.postMessage({type: 'keydown', key: 'up'}, '*');
                    event.preventDefault();
                } else if (event.key === ' ') {
                    keyState.Space = true;
                    window.parent.postMessage({type: 'keydown', key: 'space'}, '*');
                    event.preventDefault();
                }
            });
            
            window.addEventListener('keyup', function(event) {
                if (event.key === 'ArrowLeft') {
                    keyState.ArrowLeft = false;
                } else if (event.key === 'ArrowRight') {
                    keyState.ArrowRight = false;
                } else if (event.key === 'ArrowUp') {
                    keyState.ArrowUp = false;
                } else if (event.key === ' ') {
                    keyState.Space = false;
                }
            });
            
            // Send continuous updates about key states
            setInterval(function() {
                const message = {
                    type: 'keystate',
                    left: keyState.ArrowLeft,
                    right: keyState.ArrowRight,
                    up: keyState.ArrowUp,
                    space: keyState.Space
                };
                window.parent.postMessage(message, '*');
            }, 100);
            
            // Function to handle focus
            function handleFocus() {
                inputDiv.focus();
            }
            
            // Ensure div is focused when clicked anywhere
            document.addEventListener('click', handleFocus);
            
            // Auto-focus on load
            window.addEventListener('load', handleFocus);
        </script>
        """,
        height=0,
    )

def get_key_presses():
    """Get the current key presses from session state"""
    if 'key_presses' not in st.session_state:
        st.session_state.key_presses = {
            'left': False,
            'right': False,
            'up': False,
            'space': False,
            'last_fire_time': 0
        }
    
    return st.session_state.key_presses

def handle_key_event(event_data):
    """Handle keyboard events from JavaScript"""
    key_presses = get_key_presses()
    
    if event_data.get('type') == 'keydown':
        key = event_data.get('key')
        if key == 'space' and not key_presses['space']:
            # Only register space key press if it hasn't been pressed recently
            current_time = time.time()
            if current_time - key_presses['last_fire_time'] > 0.3:  # 300ms cooldown
                key_presses['space'] = True
                key_presses['last_fire_time'] = current_time
    
    elif event_data.get('type') == 'keystate':
        key_presses['left'] = event_data.get('left', False)
        key_presses['right'] = event_data.get('right', False)
        key_presses['up'] = event_data.get('up', False)
