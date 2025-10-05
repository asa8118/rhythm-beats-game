# Rhythm Beats Game

# Ensure float division behavior in Python 2
from __future__ import division
# Import necessary standard libraries
import math         # Used for calculations like log10 in volume conversion
import time         # Used for getting current time for delta_time calculation
import json         # Used for loading and saving game settings

# Import the Minim audio library using Processing's add_library function
# Minim is used for loading and playing sound effects and background music
add_library('minim')

# --- Utility Functions ---

# Function to get the full path to a file in the data folder
def dataPath(fileName):
    # Try using sketchPath (Processing environment)
    try:
        return sketchPath("data/" + fileName)
    # Fallback if sketchPath is not available
    except NameError:
        return "data/" + fileName

# --- Constants ---

# Screen dimensions
SCREEN_WIDTH = 800      # Width of the game window in pixels
SCREEN_HEIGHT = 600     # Height of the game window in pixels

# Gameplay area layout
TRACK_WIDTH = 60        # Width of each individual note track in pixels
NOTE_SIZE = 50          # Visual size (diameter) of the notes in pixels
JUDGMENT_LINE_Y = 500   # Vertical position (Y-coordinate) of the judgment line

# File paths and names
SETTINGS_FILENAME = "settings.json" # Name of the file for storing user settings

# UI Element dimensions and positions
PAUSE_BUTTON_X = SCREEN_WIDTH - 50 # X-coordinate of the pause button center
PAUSE_BUTTON_Y = 30                # Y-coordinate of the pause button center
PAUSE_BUTTON_SIZE = 40             # Diameter of the pause button

# Default settings
DEFAULT_KEY_BINDINGS = {'d': 0, 'f': 1, 'j': 2, 'k': 3} # Default key mapping for tracks

# Music configuration
available_music_tracks = [          # List of available background music files in 'data'
    "background_music.mp3",
    # Add more BGM filenames here if needed
]
# Set the default music track if available
DEFAULT_MUSIC_TRACK = available_music_tracks[0] if available_music_tracks else None

# Timing windows (in pixels from the judgment line) defining hit accuracy
perfect_window = 25     # Pixel tolerance for a 'PERFECT' hit
great_window = 50       # Pixel tolerance for a 'GREAT' hit
good_window = 80        # Pixel tolerance for a 'GOOD' hit (beyond this is 'MISS')

# Color definitions
# Default colors for each of the 4 tracks
track_colors = [
    {"r": 255, "g": 100, "b": 100}, # Track 1 color
    {"r": 100, "g": 255, "b": 100}, # Track 2 color
    {"r": 100, "g": 100, "b": 255}, # Track 3 color
    {"r": 255, "g": 255, "b": 100}  # Track 4 color
]

# Dictionary holding different color schemes for notes and effects
color_schemes = {
    "default": track_colors,            # Standard color scheme
    "high-contrast": [                  # High-contrast alternative
        {"r": 255, "g": 50, "b": 50},
        {"r": 50, "g": 255, "b": 50},
        {"r": 50, "g": 50, "b": 255},
        {"r": 255, "g": 255, "b": 50}
    ],
    "colorblind": [                     # Colorblind-friendly alternative
        {"r": 0, "g": 0, "b": 0},       # Often uses shapes/patterns in real games
        {"r": 0, "g": 107, "b": 164},    # Example: Blue
        {"r": 200, "g": 81, "b": 0},     # Example: Orange/Brown
        {"r": 255, "g": 255, "b": 255}   # Example: White
    ]
}

# --- Global State Variables ---

# Game state management
state = "MENU"          # Current game state ("MENU", "PLAYING", "PAUSED", "RESULTS", "SETTINGS")

# Gameplay statistics
score = 0               # Player's current score
combo = 0               # Current consecutive hits (combo count)
max_combo = 0           # Highest combo achieved in the current play session
# Dictionary to store counts of each judgment type
judgments = {"PERFECT": 0, "GREAT": 0, "GOOD": 0, "MISS": 0}

# Game objects
notes = []              # List to hold all active Note objects on screen
particles = []          # List to hold all active Particle objects for effects
judgment_displays = []  # List to hold active JudgmentDisplay objects

# Gameplay timing and flags
time_up = False         # Flag indicating if the game timer has run out

# UI and Interaction state
my_custom_font = None   # Holds the loaded custom font object, if successful
pressed_button_id = None # ID of the button currently being pressed by the mouse
# Timers for visual feedback when a track key is pressed
track_highlight_timers = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0} # Time remaining for highlight effect

# Gameplay difficulty/parameters (can be changed by difficulty selection)
scroll_speed = 300      # Speed at which notes travel down the screen (pixels per second)
note_spawn_interval = 0.5 # Time delay between potential note spawns (seconds)
note_spawn_probability = 0.6 # Chance (0 to 1) of a note spawning each interval
time_since_last_spawn = 0.0 # Timer tracking time since the last note spawn attempt
game_timer = 0.0        # Timer tracking the duration of the current game round
notes_hit_count = 0     # Counter for the number of notes successfully hit
max_game_time = 25.0    # Maximum duration of a game round in seconds

# Frame timing
last_time = 0.0         # Timestamp of the previous frame
delta_time = 0.0        # Time elapsed since the last frame (in seconds), 0 if paused
is_paused = False       # Flag indicating if the game is currently paused

# User Settings (loaded from/saved to file)
key_bindings = {}       # Dictionary mapping keys (str) to track indices (int)
music_volume = 0.8      # Background music volume (0.0 to 1.0)
sfx_volume = 1.0        # Sound effects volume (0.0 to 1.0)
enable_screen_shake = True # Toggle for screen shake effect on hits
enable_particles = True    # Toggle for particle effects on hits
note_color_scheme = "default" # Currently selected note color scheme name
current_music_track = DEFAULT_MUSIC_TRACK # Currently selected background music track filename

# Settings screen state
is_binding_key = False      # Flag indicating if the game is waiting for a key bind input
binding_track_index = -1    # Index of the track currently being rebound (-1 if none)
binding_prompt_text = ""    # Text displayed while waiting for key bind input
active_settings_tab = 0     # Index of the currently viewed tab in settings (0: Audio, 1: Controls, 2: Visual)
previous_state = "MENU"     # Stores the state the game was in before entering settings

# Confirmation dialog state
confirm_dialog_active = False # Flag indicating if the confirmation dialog is visible
confirm_dialog_message = ""   # Message displayed in the confirmation dialog
confirm_yes_action = None     # Function to call if 'Yes' is clicked
confirm_no_action = None      # Function to call if 'No' is clicked (usually None)

# Visual effects state
shake_intensity = 0.0   # Current magnitude of the screen shake effect
shake_decay = 0.9       # Factor by which shake intensity decreases each frame (controls duration)
max_shake_intensity = 15.0 # Maximum intensity allowed for screen shake

# Audio objects (initialized in setup)
minim = None            # Minim audio library instance
bgm = None              # Background music player object
hit_sound_perfect = None # Sound sample for 'PERFECT' hits
hit_sound_great = None   # Sound sample for 'GREAT' hits
hit_sound_good = None    # Sound sample for 'GOOD' hits
hit_sound_miss = None    # Sound sample for 'MISS' judgments
button_click_sound = None # Sound sample for UI button clicks

# --- Classes ---

# Note class representing a single falling note
class Note:
    # Initialize a new note
    def __init__(self, track_index, x_pos):
        # Use global NOTE_SIZE for consistency
        global NOTE_SIZE

        # Assign attributes
        self.track = track_index    # The track index (0-3) this note belongs to
        self.x = x_pos              # The center X-coordinate of the note
        self.y = 0.0                # The Y-coordinate (starts at the top)
        self.hit = False            # Flag indicating if the note has been hit/processed

    # Update the note's position based on time delta and scroll speed
    def update(self, dt, current_scroll_speed):
        # Only move the note if it hasn't been hit yet
        if not self.hit:
            self.y += current_scroll_speed * dt # Move down based on speed and time delta

    # Draw the note on the screen
    def draw(self, note_color_dict):
        # Use global NOTE_SIZE
        global NOTE_SIZE
        # Only draw if the note hasn't been hit
        if not self.hit:
            try:
                # Extract RGB values from the provided color dictionary
                r, g, b = note_color_dict["r"], note_color_dict["g"], note_color_dict["b"]
                # Set drawing mode to center for ellipses
                ellipseMode(CENTER)

                # Draw the main note body (slightly flattened ellipse)
                fill(r, g, b)
                ellipse(self.x, self.y, NOTE_SIZE, NOTE_SIZE * 0.75)

                # Draw a subtle highlight on top of the note
                fill(255, 255, 255, 130) # White with transparency
                ellipse(self.x, self.y - NOTE_SIZE * 0.1, NOTE_SIZE * 0.6, NOTE_SIZE * 0.35)

                # Reset ellipse mode to default (CORNER)
                ellipseMode(CORNER)
            # Handle potential errors if the color dictionary is invalid
            except (KeyError, TypeError) as e:
                print("Error drawing note, color issue: {}".format(e))
                # Fallback: draw a white note if color is problematic
                fill(255)
                ellipse(self.x, self.y, NOTE_SIZE, NOTE_SIZE * 0.75)

    # Check if the note has passed the judgment line and missed threshold
    def is_missed(self, miss_threshold_y):
        # Note is missed if its Y position is below the threshold and it hasn't been hit
        return self.y > miss_threshold_y and not self.hit

    # Mark the note as hit (so it stops updating/drawing and can be removed)
    def mark_hit(self):
        self.hit = True

    # Check if the note has been marked as hit
    def is_hit(self):
        return self.hit

    # Calculate the vertical distance from the note to a specified Y-line (usually the judgment line)
    def distance_from(self, y_line):
        return abs(self.y - y_line)

# Particle class for visual effects (e.g., explosions on hit)
class Particle:
    # Initialize a new particle
    def __init__(self, x, y, dx, dy, initial_size, r, g, b, initial_alpha):
        self.x = x                  # Starting X position
        self.y = y                  # Starting Y position
        self.dx = dx                # Initial velocity in X direction
        self.dy = dy                # Initial velocity in Y direction
        self.size = initial_size    # Starting size
        self.r, self.g, self.b = r, g, b # Color (RGB)
        self.alpha = initial_alpha  # Starting transparency (0-255)

    # Update the particle's state (position, velocity, size, alpha) over time
    def update(self, dt):
        # Constants controlling particle behavior
        damping_factor = 4.0    # How quickly velocity decreases
        fade_rate = 350.0       # How quickly the particle fades out (alpha decreases)
        shrink_rate = 3.5       # How quickly the particle shrinks

        # Update position based on velocity and delta time (scaled by 60 for visual speed adjustment)
        self.x += self.dx * dt * 60
        self.y += self.dy * dt * 60

        # Apply damping to velocity
        self.dx *= (1.0 - damping_factor * dt)
        self.dy *= (1.0 - damping_factor * dt)

        # Decrease alpha and size over time
        self.alpha -= fade_rate * dt
        self.size *= (1.0 - shrink_rate * dt)

        # Ensure alpha and size don't go below zero
        self.alpha = max(0, self.alpha)
        self.size = max(0, self.size)

    # Draw the particle on the screen
    def draw(self):
        # Only draw if the particle is still visible (alpha > 0) and has a size
        if self.alpha > 0 and self.size > 0.1:
             noStroke() # Particles typically don't have outlines
             fill(self.r, self.g, self.b, self.alpha) # Set color and transparency
             ellipseMode(CENTER) # Draw ellipse from center
             ellipse(self.x, self.y, self.size, self.size) # Draw the particle
             ellipseMode(CORNER) # Reset ellipse mode

    # Check if the particle is effectively "dead" (invisible or too small)
    def is_dead(self):
        return self.alpha <= 0 or self.size < 0.5

# JudgmentDisplay class for showing hit result text (PERFECT, GREAT, etc.)
class JudgmentDisplay:
    # Initialize a new judgment text display
    def __init__(self, judgment_text, x, y, initial_alpha=255):
        self.judgment_text = judgment_text # The text to display (e.g., "PERFECT")
        self.x = x                  # X position (center)
        self.y = y                  # Y position (center)
        self.alpha = initial_alpha  # Starting transparency
        self.move_speed = 50.0      # Speed at which the text floats upwards
        self.fade_speed = 250.0     # Speed at which the text fades out

    # Update the display's position and alpha over time
    def update(self, dt):
        self.y -= self.move_speed * dt      # Move upwards
        self.alpha -= self.fade_speed * dt  # Fade out
        self.alpha = max(0, self.alpha)     # Ensure alpha doesn't go below zero

    # Draw the judgment text on the screen
    def draw(self, font, color_map):
        # Only draw if the text is still visible
        if self.alpha > 0:
            judgment_size = 32 # Font size for the judgment text
            # Apply custom font if available, otherwise use default Processing font
            if font:
                textFont(font, judgment_size)
            else:
                textSize(judgment_size)

            # Get the base color for this judgment type from the provided map, default to white
            base_color = color_map.get(self.judgment_text, color(255))
            # Create the final color including the current alpha value
            final_color = color(red(base_color), green(base_color), blue(base_color), self.alpha)

            # Set fill color and alignment
            fill(final_color)
            textAlign(CENTER, CENTER)
            # Draw the text
            text(self.judgment_text, self.x, self.y)

    # Check if the judgment text has completely faded out
    def is_faded(self):
        return self.alpha <= 0

# --- Core Processing Functions ---

# Initial setup function, called once when the sketch starts
def setup():
    # Make specific global variables modifiable within this function
    global hit_sound_perfect, hit_sound_great, hit_sound_good, hit_sound_miss, button_click_sound
    global last_time, key_bindings, current_music_track
    global music_volume, sfx_volume, enable_screen_shake, enable_particles, note_color_scheme
    global my_custom_font, state, DEFAULT_MUSIC_TRACK, bgm, minim

    # Set window size
    size(SCREEN_WIDTH, SCREEN_HEIGHT)
    # Set target frame rate
    frameRate(60)
    # Set default text alignment
    textAlign(CENTER, CENTER)

    # Attempt to load the custom font
    font_filename = "SuperPixel-m2L8j.ttf" # Font file should be in sketch or data folder
    try:
        my_custom_font = createFont(font_filename, 32) # Create font object
        print("Custom font '{}' loaded successfully.".format(font_filename))
        textFont(my_custom_font) # Set it as the default font
    except Exception as e:
        # Handle font loading errors gracefully
        print("ERROR loading custom font '{}': {}. Using default font.".format(font_filename, e))
        my_custom_font = None # Ensure font variable is None if loading failed

    # Initialize the Minim audio library instance
    minim = Minim(this)

    # Attempt to load sound effect files
    try:
        # Load WAV files from the data folder using the dataPath utility
        hit_sound_perfect = minim.loadSample(dataPath("hit_perfect.wav"))
        hit_sound_great = minim.loadSample(dataPath("hit_great.wav"))
        hit_sound_good = minim.loadSample(dataPath("hit_good.wav"))
        hit_sound_miss = minim.loadSample(dataPath("hit_miss.wav"))
        button_click_sound = minim.loadSample(dataPath("button_click.wav"))
        print("Hit sound files loaded successfully.")
    except Exception as e:
        # Handle sound file loading errors
        print("Error loading hit sound files. Make sure they are in the 'data' folder and path is correct.")
        print("Specific error: {}".format(e))
        # Set sound variables to None if loading failed
        hit_sound_perfect = hit_sound_great = hit_sound_good = hit_sound_miss = button_click_sound = None

    # Initialize the last_time variable for delta time calculation
    try:
        # Use the more precise time.time() if available
        last_time = time.time()
    except AttributeError:
        # Fallback to Processing's millis() if time.time() is not available
        last_time = millis() / 1000.0
        print("Using millis() for delta time.")

    # Load settings from the settings file (or use defaults)
    load_settings()

    # Apply the loaded SFX volume to the sound samples (converting to decibels)
    sfx_vol_db = convertToDecibels(sfx_volume)
    if hit_sound_perfect: hit_sound_perfect.setGain(sfx_vol_db)
    if hit_sound_great: hit_sound_great.setGain(sfx_vol_db)
    if hit_sound_good: hit_sound_good.setGain(sfx_vol_db)
    if hit_sound_miss: hit_sound_miss.setGain(sfx_vol_db)
    if button_click_sound: button_click_sound.setGain(sfx_vol_db)

    # Print confirmation and loaded settings
    print("Game Setup Complete. Initial State: {}, Loaded Music Track: {}".format(state, current_music_track))
    print("Settings loaded: Keys={}, MusicVol={:.2f}, SFXVol={:.2f}, Shake={}, Particles={}, Color={}".format(
        key_bindings, music_volume, sfx_volume, enable_screen_shake, enable_particles, note_color_scheme))

# Function to convert linear volume (0.0 to 1.0) to decibels for Minim
def convertToDecibels(linearVolume):
    # Access Minim instance if needed (though not strictly necessary for this calculation)
    global minim

    # Handle edge case: volume 0 or less should be effectively silent (-80dB is common)
    if linearVolume <= 0.0:
        return -80.0
    # For positive volumes, calculate decibels using log10
    else:
        # Ensure volume is slightly above 0 to avoid log10(0) error
        safe_volume = max(0.0001, linearVolume)
        # Standard formula for converting linear amplitude ratio to dB
        return 20.0 * math.log10(safe_volume)

# Main draw loop function, called repeatedly by Processing
def draw():
    # Make specific global variables modifiable
    global last_time, delta_time, state, shake_intensity, is_paused
    global confirm_dialog_active, confirm_dialog_message, confirm_yes_action, confirm_no_action
    global combo, note_color_scheme, color_schemes, enable_screen_shake
    global pressed_button_id, particles, judgment_displays
    # Access Processing's mousePressed variable
    global mousePressed

    # Calculate delta time (time since last frame)
    current_time = 0.0
    try:
        current_time = time.time() # Preferred method
    except AttributeError:
        current_time = millis() / 1000.0 # Fallback

    actual_delta_time = current_time - last_time
    # Clamp delta time to prevent large jumps (e.g., after lag)
    actual_delta_time = min(actual_delta_time, 0.1) # Max delta = 0.1s (10 FPS)

    # If paused, delta_time used for updates should be 0
    delta_time = 0.0 if is_paused else actual_delta_time
    # Update last_time for the next frame's calculation
    last_time = current_time

    # Update effects that run even when paused (like shake decay, maybe?)
    # Here, only updating if *not* paused. Consider if decay should happen during pause.
    if not is_paused:
        # Apply decay to screen shake intensity
        shake_intensity *= shake_decay
        # If intensity is very low, reset to 0 to stop calculation
        if shake_intensity < 0.1:
            shake_intensity = 0.0

    # Save the current transformation matrix
    pushMatrix()
    # Apply screen shake translation if active and enabled
    if shake_intensity > 0 and enable_screen_shake:
        translate(random(-shake_intensity, shake_intensity),
                  random(-shake_intensity, shake_intensity))

    # Set background brightness based on combo (subtle effect)
    # Map combo (up to 50) to a brightness value (0 to 40)
    bg_brightness = map(min(combo, 50), 0, 50, 0, 40)
    background(bg_brightness) # Draw the background

    # Update game logic and effects only if not paused
    if not is_paused:
        # Update core gameplay elements if in PLAYING state
        if state == "PLAYING":
            update_gameplay(delta_time)
        # Update particles and judgment displays regardless of PLAYING state (they might exist in RESULTS briefly)
        update_particles(delta_time)
        update_judgment_displays(delta_time)

    # Draw the appropriate screen based on the current game state
    if state == "MENU":
        draw_menu()
    elif state == "PLAYING" or state == "PAUSED":
        # Draw the main gameplay interface (tracks, notes, judgment line, HUD)
        draw_gameplay()
        # If paused, draw the pause overlay on top
        if state == "PAUSED":
            draw_paused_screen()
    elif state == "RESULTS":
        draw_results()
    elif state == "SETTINGS":
        draw_settings_screen()

    # Draw the confirmation dialog if it's active (drawn over everything else except particles/judgments)
    if confirm_dialog_active:
        draw_confirmation_dialog(confirm_dialog_message, confirm_yes_action, confirm_no_action)

    # Restore the previous transformation matrix (removes shake effect for subsequent draws)
    popMatrix()

    # Draw particles and judgment displays on top of everything, unaffected by screen shake
    draw_particles()
    draw_judgment_displays()

    # Reset the pressed button ID if the mouse is no longer pressed
    # This prevents buttons appearing stuck if mouse is released outside the game window
    if pressed_button_id is not None and not mousePressed:
        pressed_button_id = None

# --- Drawing Functions ---

# Draws the main menu screen
def draw_menu():
    # Access global variables needed for drawing
    global key_bindings, my_custom_font, width, height

    # Draw the main title
    if my_custom_font: textFont(my_custom_font, 48)
    else: textSize(48)
    fill(255); text("RHYTHM BEATS", width/2, 80)

    # Draw the subtitle
    if my_custom_font: textFont(my_custom_font, 20)
    else: textSize(20)
    text("A Dynamic Rhythm Game", width/2, 120)

    # Define button layout parameters
    button_y_start_center = 180 + 50/2 # Y-coordinate for the center of the first button
    button_h = 50; button_spacing = 60; button_w = 300 # Dimensions and spacing

    # List of difficulty levels to create buttons for
    difficulties = ["Easy", "Normal", "Hard", "Expert"]

    # Draw difficulty buttons
    for i, difficulty in enumerate(difficulties):
        y_center = button_y_start_center + i * button_spacing
        button_id = "menu_{}".format(difficulty.lower()) # Unique ID for hover/click detection
        draw_button(difficulty, button_id, width/2, y_center, button_w, button_h)

    # Draw the Settings button below the difficulty buttons
    settings_y_center = button_y_start_center + len(difficulties) * button_spacing
    draw_button("Settings", "menu_settings", width/2, settings_y_center, button_w, button_h)

    # Draw informational text at the bottom
    if my_custom_font: textFont(my_custom_font, 16)
    else: textSize(16)
    fill(200); text("Click a difficulty to start", width/2, height - 60)

    # Display the currently bound keys
    key_list = ["?"] * 4 # Initialize with placeholders
    try:
        # Sort bindings by track index to display keys in order
        sorted_bindings = sorted(key_bindings.items(), key=lambda item: item[1])
        # Get the uppercase key character for each binding
        key_list = [k.upper() for k, v in sorted_bindings]
    except Exception as e:
        # Handle potential errors during formatting
        print("Error formatting key binding string for menu display: {}".format(e))
    key_string = ", ".join(key_list) # Join keys into a display string
    text("Current Keys: " + key_string, width/2, height - 35)

# Reusable function to draw a button with hover and press states
def draw_button(label, id, x_center, y_center, w, h, base_color=color(30, 40, 80), hover_color=color(50, 60, 120), press_color=color(15, 20, 40), text_color=color(255)):
    # Access global variables needed for interaction state
    global pressed_button_id, my_custom_font
    # Access Processing's mouse position variables
    global mouseX, mouseY

    # Determine if the mouse is hovering over the button's area
    is_hovering = (mouseX > x_center - w/2 and mouseX < x_center + w/2 and
                   mouseY > y_center - h/2 and mouseY < y_center + h/2)
    # Determine if this specific button is currently being pressed
    is_pressed = (pressed_button_id == id)

    # Save current drawing style and coordinate system
    pushMatrix()
    translate(x_center, y_center) # Move origin to button center for easier drawing

    # Set default appearance
    current_fill = base_color
    current_stroke = color(100, 150, 255) # Border color
    text_y_offset = 0 # Text offset for pressed state

    # Adjust appearance based on state
    if is_pressed:
        current_fill = press_color          # Use pressed color
        current_stroke = color(150, 200, 255) # Brighter border when pressed
        text_y_offset = 1                   # Shift text down slightly
    elif is_hovering:
        current_fill = hover_color          # Use hover color
        current_stroke = color(150, 200, 255) # Brighter border on hover

    # Draw the button background rectangle
    fill(current_fill); stroke(current_stroke); strokeWeight(2)
    rectMode(CENTER); rect(0, 0, w, h, 10) # Rounded corners (radius 10)

    # Draw the button label text
    if my_custom_font: textFont(my_custom_font, 18)
    else: textSize(18)
    fill(text_color); textAlign(CENTER, CENTER)
    text(label, 0, text_y_offset) # Apply pressed offset if needed

    # Restore previous drawing style and coordinate system
    popMatrix()
    # Reset drawing modes modified for this function
    rectMode(CORNER); strokeWeight(1); noStroke()

# Draws the settings screen interface
def draw_settings_screen():
    # Access global variables related to settings UI
    global binding_prompt_text, current_music_track, available_music_tracks, active_settings_tab
    global my_custom_font, is_binding_key
    global width, height

    # Draw dark background
    background(20)
    # Draw screen title
    fill(255)
    if my_custom_font: textFont(my_custom_font, 36)
    else: textSize(36)
    text("Settings", width/2, 50)

    # Define tab properties
    tabs = ["Audio", "Controls", "Visual"]
    tab_width = width / len(tabs); tab_height = 40; tab_y = 80
    # Set font for tabs
    if my_custom_font: textFont(my_custom_font, 18)
    else: textSize(18)

    # Draw the tabs
    for i, tab in enumerate(tabs):
        is_active = (i == active_settings_tab) # Check if this is the current tab
        tab_x = i * tab_width # Calculate X position of the tab

        # Draw active tab differently
        if is_active:
            fill(60, 80, 120); noStroke() # Active tab background color
            rect(tab_x, tab_y, tab_width, tab_height) # Draw tab background
            fill(255); text(tab, tab_x + tab_width/2, tab_y + tab_height/2) # Active tab text (white)
        # Draw inactive tab
        else:
            fill(30, 40, 60); noStroke() # Inactive tab background color
            rect(tab_x, tab_y, tab_width, tab_height) # Draw tab background
            stroke(80, 100, 140); strokeWeight(1) # Border line at the top
            line(tab_x, tab_y, tab_x + tab_width, tab_y)
            fill(180); text(tab, tab_x + tab_width/2, tab_y + tab_height/2) # Inactive tab text (gray)
    noStroke() # Reset stroke

    # Calculate starting Y position for tab content
    content_y_start = tab_y + tab_height + 20

    # Draw the content based on the active tab
    if active_settings_tab == 0: draw_audio_settings(content_y_start)
    elif active_settings_tab == 1: draw_control_settings(content_y_start)
    else: draw_visual_settings(content_y_start)

    # Draw the "Save & Return" button at the bottom
    back_button_y_center = height - 70 + 50/2 # Calculate button Y center
    draw_button("Save & Return", "settings_back", width/2, back_button_y_center, 200, 50)

# Draws the content for the Audio settings tab
def draw_audio_settings(start_y):
    # Access global audio settings variables
    global music_volume, sfx_volume, current_music_track, available_music_tracks
    global my_custom_font, width

    # Define layout positions and text size
    label_x = width * 0.35; control_x = width * 0.6; current_y = start_y
    base_text_size = 18
    if my_custom_font: textFont(my_custom_font, base_text_size)
    else: textSize(base_text_size)

    # Draw Music Volume slider
    current_y += 15 # Add vertical spacing
    fill(220); textAlign(RIGHT, CENTER) # Set label style
    text("Music Volume:", label_x, current_y) # Draw label
    textAlign(CENTER, CENTER) # Reset alignment for slider
    draw_slider(control_x, current_y, 300, music_volume) # Draw the slider control

    # Draw SFX Volume slider
    current_y += 50 # Add vertical spacing
    fill(220); textAlign(RIGHT, CENTER) # Set label style
    text("SFX Volume:", label_x, current_y) # Draw label
    textAlign(CENTER, CENTER) # Reset alignment for slider
    draw_slider(control_x, current_y, 300, sfx_volume) # Draw the slider control

    # Music track selection could be added here (e.g., dropdown or list)

# Draws the content for the Controls settings tab
def draw_control_settings(start_y):
    # Access global control settings variables
    global key_bindings, binding_prompt_text, is_binding_key
    global my_custom_font, width

    # Draw section title
    setting_x = width/2 # Center X for this section
    if my_custom_font: textFont(my_custom_font, 24)
    else: textSize(24)
    fill(255); text("Key Bindings", setting_x, start_y)

    # Draw instructional text
    if my_custom_font: textFont(my_custom_font, 16)
    else: textSize(16)
    fill(200); text("Click a button below to rebind the key for that track.", setting_x, start_y + 30)

    # Define layout for the binding buttons
    num_tracks = 4; button_w = 120; button_h = 45; button_spacing_x = 30
    total_width = num_tracks * button_w + (num_tracks - 1) * button_spacing_x
    button_start_x = setting_x - total_width / 2 # Starting X for the first button
    button_y_center = start_y + 70 + button_h / 2 # Y position for the buttons

    # Get the current key characters for display on buttons
    key_chars = ["?"] * num_tracks # Initialize with placeholders
    try:
        # Map bound keys to their track index in the display array
        for key, index in key_bindings.items():
            if 0 <= index < num_tracks: key_chars[index] = key.upper()
    except Exception as e: print("Error displaying key bindings: {}".format(e))

    # Draw a button for each track to trigger rebinding
    for i in range(num_tracks):
        x_center = button_start_x + button_w/2 + i * (button_w + button_spacing_x) # Calculate button center X
        label = "Track {}: {}".format(i+1, key_chars[i]) # Button label shows track and current key
        button_id = "settings_bind_{}".format(i) # Unique ID for the button
        draw_button(label, button_id, x_center, button_y_center, button_w, button_h)

    # If currently waiting for a key press, display the prompt text
    if is_binding_key:
        if my_custom_font: textFont(my_custom_font, 20)
        else: textSize(20)
        fill(255, 255, 0) # Yellow color for prompt
        text(binding_prompt_text, setting_x, button_y_center + button_h/2 + 30) # Draw below buttons

# Draws the content for the Visual settings tab
def draw_visual_settings(start_y):
    # Access global visual settings variables
    global enable_screen_shake, enable_particles, note_color_scheme
    global my_custom_font, width, color_schemes

    # Define layout and text size
    setting_center_x = width / 2; current_y = start_y
    base_text_size = 18
    if my_custom_font: textFont(my_custom_font, base_text_size)
    else: textSize(base_text_size)

    # Draw Screen Shake toggle
    current_y += 20 # Add vertical spacing
    draw_toggle("Screen Shake", setting_center_x, current_y, enable_screen_shake)

    # Draw Particle Effects toggle
    current_y += 50 # Add vertical spacing
    draw_toggle("Particle Effects", setting_center_x, current_y, enable_particles)

    # Draw Note Color Scheme section header
    current_y += 60 # Add vertical spacing
    section_title_size = 20
    if my_custom_font: textFont(my_custom_font, section_title_size)
    else: textSize(section_title_size)
    fill(220); textAlign(CENTER, CENTER)
    text("Note Color Scheme", setting_center_x, current_y)

    # Reset text size for radio buttons
    if my_custom_font: textFont(my_custom_font, base_text_size)
    else: textSize(base_text_size)

    # Get list of available scheme names for display
    schemes = [name.replace("-", " ").title() for name in color_schemes.keys()]
    # Define layout for radio buttons
    radio_y = current_y + 35; radio_spacing = 35 # Start Y and vertical spacing

    # Draw radio buttons for each color scheme
    for i, scheme_name in enumerate(schemes):
        y_pos = radio_y + i * radio_spacing # Calculate Y position for this button
        # Convert display name back to the key used in the dictionary
        scheme_key = scheme_name.lower().replace(" ", "-")
        # Check if this scheme is the currently selected one
        selected = (scheme_key == note_color_scheme)
        # Draw the radio button control
        draw_radio_button(scheme_name, setting_center_x, y_pos, selected)

# Reusable function to draw a slider control
def draw_slider(x, y, w, value):
    # Access global font variable
    global my_custom_font

    # Define slider geometry
    slider_x_start = x - w/2; slider_x_end = x + w/2; handle_size = 20
    # Draw the slider track (line)
    stroke(100); strokeWeight(3); line(slider_x_start, y, slider_x_end, y)
    # Calculate the handle's X position based on the value (0-1)
    handle_x = constrain(map(value, 0, 1, slider_x_start, slider_x_end), slider_x_start, slider_x_end)
    # Draw the slider handle (circle)
    fill(200, 200, 255); stroke(230, 230, 255); strokeWeight(1)
    ellipse(handle_x, y, handle_size, handle_size)

    # Draw the percentage value next to the slider
    if my_custom_font: textFont(my_custom_font, 12)
    else: textSize(12)
    fill(200); textAlign(LEFT, CENTER)
    text("{:.0f}%".format(value * 100), slider_x_end + 10, y)
    # Reset text alignment and stroke
    textAlign(CENTER, CENTER); noStroke()

# Reusable function to draw a toggle switch control
def draw_toggle(label, x_center_layout, y, is_on):
    # Access global font variable
    global my_custom_font

    # Define toggle geometry
    toggle_width = 60; toggle_height = 30; handle_diameter = 26
    # Calculate positions relative to the layout center
    label_offset = - (toggle_width / 2 + 15) # Offset label to the left of the toggle
    toggle_center_x = x_center_layout + 50 # Center X of the toggle switch itself

    # Draw the label text
    if my_custom_font: textFont(my_custom_font, 18)
    else: textSize(18)
    textAlign(RIGHT, CENTER); fill(220)
    text(label, toggle_center_x + label_offset, y)

    # Draw the toggle background (rounded rectangle)
    rectMode(CENTER); noStroke()
    fill(80, 80, 90); rect(toggle_center_x, y, toggle_width, toggle_height, toggle_height/2) # Use height/2 for fully rounded ends

    # Calculate handle position and color based on state (on/off)
    if is_on:
        # Handle position to the right
        handle_x = toggle_center_x + (toggle_width - toggle_height) / 2
        fill(100, 220, 100) # Green color when on
    else:
        # Handle position to the left
        handle_x = toggle_center_x - (toggle_width - toggle_height) / 2
        fill(200, 200, 200) # Gray color when off

    # Draw the toggle handle (circle)
    stroke(50); strokeWeight(1) # Add a slight border to the handle
    ellipse(handle_x, y, handle_diameter, handle_diameter)

    # Reset drawing modes and styles
    textAlign(CENTER, CENTER); rectMode(CORNER); noStroke(); strokeWeight(1)

# Reusable function to draw a radio button control
def draw_radio_button(label, x_center_layout, y, selected):
    # Access global font variable
    global my_custom_font

    # Define radio button geometry
    radio_diameter = 20; inner_diameter = 12 # Outer circle and inner selected circle
    # Calculate positions relative to the layout center
    label_offset = - (radio_diameter / 2 + 10) # Offset label to the left
    radio_center_x = x_center_layout + 30 # Center X of the radio button circle

    # Draw the label text
    if my_custom_font: textFont(my_custom_font, 18)
    else: textSize(18)
    textAlign(RIGHT, CENTER); fill(220)
    text(label, radio_center_x + label_offset, y)

    # Draw the outer circle (the radio button itself)
    strokeWeight(1.5); stroke(180); noFill() # Gray border, no fill
    ellipse(radio_center_x, y, radio_diameter, radio_diameter)

    # If this button is selected, draw the inner filled circle
    if selected:
        noStroke(); fill(100, 220, 100) # Green fill, no border
        ellipse(radio_center_x, y, inner_diameter, inner_diameter)

    # Reset drawing styles
    textAlign(CENTER, CENTER); noStroke(); strokeWeight(1)

# Draws the pause screen overlay
def draw_paused_screen():
    # Access global variables for displaying info
    global score, combo, my_custom_font, width, height

    # Draw a semi-transparent dark overlay covering the screen
    fill(0, 0, 0, 200) # Black with alpha 200
    rect(0, 0, width, height)

    # Draw the "PAUSED" title
    if my_custom_font: textFont(my_custom_font, 52)
    else: textSize(52)
    fill(255); text("PAUSED", width/2, height * 0.25)

    # Display current score and combo
    stats_y = height * 0.35 # Y position for stats
    if my_custom_font: textFont(my_custom_font, 24)
    else: textSize(24)
    fill(220); text("Score: {:,}".format(int(score)), width/2, stats_y) # Formatted score
    # Only display combo if it's greater than 0
    if combo > 0:
        fill(255, 255, 100); text("Combo: {}".format(combo), width/2, stats_y + 35) # Yellow color for combo

    # Define layout for pause menu buttons
    button_w = 220; button_h = 50; button_spacing = 65; num_buttons = 4
    # Calculate total height and starting Y position to center the buttons vertically
    total_button_height = num_buttons * button_h + (num_buttons - 1) * (button_spacing - button_h)
    button_y_start_center = height/2 - total_button_height/2 + button_h/2

    # Draw the pause menu buttons
    draw_button("Resume", "pause_resume", width/2, button_y_start_center, button_w, button_h)
    draw_button("Restart", "pause_restart", width/2, button_y_start_center + button_spacing, button_w, button_h)
    draw_button("Settings", "pause_settings", width/2, button_y_start_center + button_spacing*2, button_w, button_h)
    draw_button("Return to Menu", "pause_menu", width/2, button_y_start_center + button_spacing*3, button_w, button_h)

    # Draw helper text at the bottom
    if my_custom_font: textFont(my_custom_font, 16)
    else: textSize(16)
    fill(180); text("Press ESC to Resume", width/2, height - 40)

# Draws the confirmation dialog box
def draw_confirmation_dialog(message, yes_action, no_action):
    # Access global variables
    global my_custom_font, width, height

    # Draw a dark, semi-transparent overlay
    fill(0, 0, 0, 230); rect(0, 0, width, height)

    # Define dialog box dimensions and position
    box_w = 450; box_h = 220; box_x = width/2 - box_w/2; box_y = height/2 - box_h/2
    # Draw the dialog box background
    fill(45, 50, 70); stroke(100, 150, 255); strokeWeight(2) # Dark blue-gray fill, light blue border
    rect(box_x, box_y, box_w, box_h, 15) # Rounded corners

    # Set text style for the message
    if my_custom_font: textFont(my_custom_font, 22)
    else: textSize(22)
    fill(230); textAlign(CENTER, CENTER) # Light gray text, centered

    # --- Text Wrapping Logic ---
    words = message.split(); lines = []; current_line = ""; max_line_width = box_w * 0.8 # Max width relative to box width
    # Iterate through words to build lines that fit within the max width
    for word in words:
        test_line = current_line + (" " if current_line else "") + word # Add space if not first word
        # Check width using the current font
        if my_custom_font: textFont(my_custom_font, 22)
        else: textSize(22)
        # If the test line fits, update the current line
        if textWidth(test_line) < max_line_width:
            current_line = test_line
        # If it doesn't fit, add the previous line to the list and start a new line
        else:
            lines.append(current_line); current_line = word
    lines.append(current_line) # Add the last line
    # --- End Text Wrapping ---

    # Calculate starting Y position to center the text block vertically
    line_height = 30
    text_start_y = height/2 - (len(lines) * line_height) / 2 + 10 # Adjust slightly upwards from pure center
    # Draw each line of the wrapped text
    for i, line in enumerate(lines):
        text(line, width/2, text_start_y + i * line_height)

    # Define layout for 'Yes' and 'No' buttons
    button_w = 130; button_h = 45; button_spacing = 30
    button_y_center = box_y + box_h - button_h/2 - 25 # Position near bottom of the dialog
    # Calculate X positions for buttons, centered with spacing
    yes_x_center = width/2 - button_spacing/2 - button_w/2
    no_x_center = width/2 + button_spacing/2 + button_w/2

    # Draw the 'Yes' button with distinct colors
    draw_button("Yes", "confirm_yes", yes_x_center, button_y_center, button_w, button_h,
                base_color=color(60, 100, 60), hover_color=color(80, 140, 80), press_color=color(40, 70, 40)) # Greenish
    # Draw the 'No' button with distinct colors
    draw_button("No", "confirm_no", no_x_center, button_y_center, button_w, button_h,
                base_color=color(100, 60, 60), hover_color=color(140, 80, 80), press_color=color(70, 40, 40)) # Reddish

# Draws the results screen after a game round ends
def draw_results():
    # Access global variables holding results data
    global score, max_combo, judgments, my_custom_font, width, height

    # Determine if the game ended because of a miss
    was_miss = judgments.get("MISS", 0) > 0

    # Draw the main result message ("GAME OVER" or "GOOD JOB!")
    if my_custom_font: textFont(my_custom_font, 52)
    else: textSize(52)
    if was_miss: fill(255, 50, 50); text("GAME OVER", width/2, 80) # Red if missed
    else: fill(100, 255, 100); text("GOOD JOB!", width/2, 80) # Green if completed

    # Define layout for results details
    results_y_start = 160; line_spacing = 55

    # Draw the final score
    if my_custom_font: textFont(my_custom_font, 40)
    else: textSize(40)
    fill(255, 220, 100); text("Score: {:,}".format(int(score)), width/2, results_y_start) # Yellowish score

    # Draw the maximum combo achieved
    if my_custom_font: textFont(my_custom_font, 36)
    else: textSize(36)
    fill(255, 255, 150); text("Max Combo: {}".format(max_combo), width/2, results_y_start + line_spacing)

    # Draw the counts for each judgment type
    judgment_y = results_y_start + line_spacing * 2 + 10; judgment_spacing = 45 # Layout for judgments
    if my_custom_font: textFont(my_custom_font, 26)
    else: textSize(26)
    # Define colors associated with each judgment type for display
    judgment_colors = {
        "PERFECT": color(255, 255, 0), "GREAT": color(100, 255, 100),
        "GOOD": color(100, 200, 255), "MISS": color(255, 80, 80)
    }
    judgment_order = ["PERFECT", "GREAT", "GOOD", "MISS"] # Order to display judgments

    # Iterate and draw each judgment count with its color
    for i, judgment_type in enumerate(judgment_order):
        count = judgments.get(judgment_type, 0) # Get count, default to 0
        fill(judgment_colors[judgment_type]) # Set text color
        text(judgment_type + ": " + str(count), width/2, judgment_y + i * judgment_spacing)

    # Define layout for 'Retry' and 'Menu' buttons
    button_y_center = height - 100 + 50/2; button_w = 200; button_h = 50; button_spacing_x = 40
    # Calculate X positions for centered buttons with spacing
    retry_x_center = width/2 - button_spacing_x/2 - button_w/2
    menu_x_center = width/2 + button_spacing_x/2 + button_w/2
    # Draw the buttons
    draw_button("Retry", "results_retry", retry_x_center, button_y_center, button_w, button_h)
    draw_button("Menu", "results_menu", menu_x_center, button_y_center, button_w, button_h)

    # Draw helper text at the bottom
    if my_custom_font: textFont(my_custom_font, 16)
    else: textSize(16)
    fill(200); text("Click a button or press SPACE to Retry", width/2, height - 35)

# --- Game Logic Update Functions ---

# Updates the main gameplay logic when state is "PLAYING"
def update_gameplay(dt):
    # Access global variables related to gameplay state
    global notes, score, combo, max_combo, judgments, state
    global time_since_last_spawn, note_spawn_interval, note_spawn_probability
    global game_timer, notes_hit_count, max_game_time
    global bgm, scroll_speed
    global track_highlight_timers, JUDGMENT_LINE_Y, good_window, width
    global time_up, particles

    # Increment the game timer
    game_timer += dt

    # Check if the maximum game time has been reached
    if game_timer >= max_game_time and not time_up:
        time_up = True # Set the flag
        print("Time is up! Allowing notes to finish falling...")

    # If time is up and no notes are left on screen, end the game
    if time_up and not notes:
        print("Game completed successfully! (Time Limit Reached & Notes Cleared)")
        state = "RESULTS" # Change state to show results
        # Stop and rewind background music if playing
        if bgm and bgm.isPlaying():
            bgm.pause(); bgm.rewind()
        return # Stop further updates in this frame

    # --- Note Spawning Logic ---
    # Increment the time since the last spawn attempt
    time_since_last_spawn += dt

    # Check if it's time for a potential spawn (and game time is not up)
    if not time_up and time_since_last_spawn >= note_spawn_interval:
        # Check if a note should spawn based on probability
        if random(1) < note_spawn_probability:
            track = int(random(4)) # Choose a random track (0-3)
            x_pos = calculate_track_x(track) # Get the X position for that track
            new_note = Note(track_index=track, x_pos=x_pos) # Create a new Note object
            notes.append(new_note) # Add the note to the active list
            time_since_last_spawn = 0.0 # Reset the spawn timer

    # --- Note Update and Miss Check ---
    # Define the Y-coordinate threshold for missing a note
    miss_threshold = JUDGMENT_LINE_Y + good_window + 20 # A bit below the 'GOOD' window
    # Iterate through a copy of the notes list ([:]) to allow removal during iteration
    for note in notes[:]:
        # Update the note's position
        note.update(dt, scroll_speed)

        # Check if the note has been missed
        if note.is_missed(miss_threshold):
            print("Note missed! Track: {}, Y: {:.1f}".format(note.track, note.y))
            # Register the miss judgment (which also handles game over)
            register_judgment("MISS", note.track)
            # If the game state changed to RESULTS due to the miss, stop processing this frame
            if state == "RESULTS":
                # Try removing the missed note (might already be gone if state change was immediate)
                try:
                    if note in notes: notes.remove(note)
                except ValueError: pass # Ignore error if already removed
                return # Exit update loop

            # If game didn't end, just remove the missed note
            try:
                if note in notes:
                    notes.remove(note)
            except ValueError:
                # This might happen if multiple checks remove the same note nearly simultaneously
                print("Warning: Tried to remove already removed missed note.")

    # --- Track Highlight Timer Update ---
    # Decrease the highlight timers for each track
    for i in range(len(track_highlight_timers)):
        if track_highlight_timers[i] > 0:
            track_highlight_timers[i] -= dt
            # Ensure timer doesn't go negative
            if track_highlight_timers[i] < 0:
                track_highlight_timers[i] = 0.0

# Draws the main gameplay interface (tracks, notes, HUD, etc.)
def draw_gameplay():
    # Access global variables needed for drawing the game
    global PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_SIZE
    global key_bindings, notes, note_color_scheme, color_schemes
    global score, combo
    global track_highlight_timers, my_custom_font, particles
    global JUDGMENT_LINE_Y, TRACK_WIDTH, NOTE_SIZE, width, height

    # --- Draw Tracks and Judgment Line ---
    num_tracks = 4 # Define number of tracks
    track_spacing = 20 # Space between tracks
    # Calculate the total width occupied by tracks and spacing
    total_track_area_width = num_tracks * TRACK_WIDTH + (num_tracks - 1) * track_spacing
    # Calculate the starting X position to center the track area
    track_start_x = (width - total_track_area_width) / 2

    # Draw the judgment line across the track area
    stroke(255, 255, 0, 200); strokeWeight(3) # Yellow, semi-transparent, thick line
    line(track_start_x - 10, JUDGMENT_LINE_Y, track_start_x + total_track_area_width + 10, JUDGMENT_LINE_Y)
    noStroke() # Reset stroke

    # Get the currently active color scheme
    active_scheme = color_schemes.get(note_color_scheme, color_schemes["default"])

    # Draw each track lane and key indicator
    for i in range(num_tracks):
        track_center_x = calculate_track_x(i) # Get center X for this track
        track_x_corner = track_center_x - TRACK_WIDTH / 2 # Get left edge X

        # Draw the track background rectangle
        fill(30, 30, 30, 180); rectMode(CORNER) # Dark gray, semi-transparent
        rect(track_x_corner, 0, TRACK_WIDTH, height) # Full height rectangle

        # Draw the key press highlight effect if timer is active
        if track_highlight_timers[i] > 0:
            # Calculate alpha based on remaining time (fades out)
            highlight_alpha = map(track_highlight_timers[i], 0, 0.15, 0, 150)
            # Use the track's color from the active scheme
            if 0 <= i < len(active_scheme):
                clr = active_scheme[i]; fill(clr["r"], clr["g"], clr["b"], highlight_alpha)
            else: fill(255, 255, 255, highlight_alpha) # Fallback white
            # Define highlight rectangle dimensions and position
            key_indicator_height = 45; key_indicator_y = JUDGMENT_LINE_Y - key_indicator_height / 2
            # Draw the highlight rectangle
            rect(track_x_corner, key_indicator_y, TRACK_WIDTH, key_indicator_height, 5) # Rounded corners

        # Draw the static key indicator box at the judgment line
        key_indicator_height = 45; key_indicator_y = JUDGMENT_LINE_Y - key_indicator_height / 2
        fill(55, 55, 60, 220); stroke(150); strokeWeight(1) # Slightly lighter gray, thin border
        rect(track_x_corner, key_indicator_y, TRACK_WIDTH, key_indicator_height, 5) # Rounded corners

        # Find the key character bound to this track
        key_char = "?" # Default placeholder
        try:
            for k, v in key_bindings.items():
                if v == i: key_char = k.upper(); break # Found the key
        except Exception as e: print("Error getting key char: {}".format(e))

        # Draw the key character inside the indicator box
        if my_custom_font: textFont(my_custom_font, 20)
        else: textSize(20)
        fill(255); textAlign(CENTER, CENTER) # White text, centered
        text(key_char, track_center_x, JUDGMENT_LINE_Y) # Draw at the center of the indicator

    noStroke() # Reset stroke

    # --- Draw Notes ---
    # Iterate through active notes and draw them using their assigned color
    for note in notes:
        track_index = note.track
        # Ensure track index is valid before accessing color scheme
        if 0 <= track_index < len(active_scheme):
            note_color = active_scheme[track_index] # Get color from scheme
            note.draw(note_color) # Tell the note to draw itself
        else:
            # Log warning if an invalid track index is encountered
            print("Warning: Invalid track_index {} for note, cannot draw.".format(track_index))

    # --- Draw HUD (Score, Combo) ---
    textAlign(LEFT, TOP) # Align HUD text to top-left
    # Draw Score
    if my_custom_font: textFont(my_custom_font, 28)
    else: textSize(28)
    fill(255); text("Score: {:,}".format(int(score)), 20, 20) # White text, formatted score
    # Draw Combo (only if combo > 1)
    if combo > 1:
        # Draw Combo Number (larger font)
        if my_custom_font: textFont(my_custom_font, 36)
        else: textSize(36)
        fill(255, 255, 100); textAlign(LEFT, TOP) # Yellow text
        combo_str = str(combo)
        # Calculate width of the number to position the "Combo" text next to it
        combo_str_width = 0
        if my_custom_font: textFont(my_custom_font, 36)
        else: textSize(36)
        combo_str_width = textWidth(combo_str)
        text(combo_str, 20, 55) # Draw the combo number
        # Draw "Combo" Text (smaller font)
        if my_custom_font: textFont(my_custom_font, 18)
        else: textSize(18)
        fill(220); text("Combo", 20 + combo_str_width + 10, 65) # Gray text, positioned after number

    # --- Draw Pause Button ---
    fill(200, 200, 200, 150); stroke(255); strokeWeight(1) # Semi-transparent gray circle, white border
    ellipseMode(CENTER); ellipse(PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_SIZE, PAUSE_BUTTON_SIZE)
    # Draw the pause icon (two vertical bars)
    rectMode(CENTER); fill(255); noStroke() # White bars
    bar_width = 5; bar_height = 16; bar_offset = 6 # Icon dimensions
    rect(PAUSE_BUTTON_X - bar_offset, PAUSE_BUTTON_Y, bar_width, bar_height, 2) # Left bar
    rect(PAUSE_BUTTON_X + bar_offset, PAUSE_BUTTON_Y, bar_width, bar_height, 2) # Right bar

    # Reset drawing modes modified for this function
    rectMode(CORNER); ellipseMode(CORNER); textAlign(CENTER, CENTER); noStroke()

# --- Gameplay Actions ---

# Handles processing a key press for a specific track during gameplay
def process_key_press(track_index):
    # Access global variables related to gameplay state and effects
    global notes, shake_intensity, max_shake_intensity
    global track_highlight_timers, enable_screen_shake
    global score, combo, max_combo, judgments, state
    global particles, judgment_displays
    global JUDGMENT_LINE_Y, perfect_window, great_window, good_window
    global width

    # Initialize variables to find the closest note on the pressed track
    closest_note_object = None
    min_distance = float('inf') # Start with infinity distance

    # Activate the visual highlight for the pressed track
    track_highlight_timers[track_index] = 0.15 # Set timer duration (in seconds)

    # Find the nearest unhit note on the target track
    for note in notes:
        # Check if note is on the correct track and hasn't been hit yet
        if note.track == track_index and not note.is_hit():
            # Calculate vertical distance from the judgment line
            distance = note.distance_from(JUDGMENT_LINE_Y)
            # If this note is closer than the current minimum, update closest note
            if distance < min_distance:
                min_distance = distance
                closest_note_object = note

    # If a relevant note was found near the judgment line
    if closest_note_object is not None:
        # Determine the judgment based on the timing (distance)
        judgment = get_judgment_for_timing(min_distance)

        # If the hit was not a miss (i.e., within the 'GOOD' window or better)
        if judgment != "MISS":
            # Register the judgment (updates score, combo, sounds, etc.)
            register_judgment(judgment, track_index)

            # Trigger screen shake effect if enabled
            if enable_screen_shake:
                # Set shake intensity based on judgment quality
                shake_amount = { "PERFECT": 1.0, "GREAT": 0.6, "GOOD": 0.3 }.get(judgment, 0.0)
                shake_intensity = max_shake_intensity * shake_amount
                # Clamp intensity to the maximum allowed value
                shake_intensity = min(shake_intensity, max_shake_intensity)

            # Create particle effects for the hit
            create_hit_effect(track_index, judgment)

            # Mark the note as hit and remove it from the active list
            try:
                closest_note_object.mark_hit()
                # Check again if it's still in the list before removing
                if closest_note_object in notes:
                    notes.remove(closest_note_object)
            except ValueError:
                # Handle rare case where the note might have been removed elsewhere (e.g., miss check)
                print("Warning: Tried to remove note object that was already gone.")
            except Exception as e:
                print("Error removing hit note object: {}".format(e))
        # Implicitly, if judgment is "MISS", nothing happens here because misses are handled
        # by the note travelling past the miss threshold in update_gameplay.
        # An alternative design could handle misses here if a key is pressed when no note is close.

# Updates the state of all active particles
def update_particles(dt):
    # Access the global list of particles
    global particles

    # Iterate through a copy of the list to allow removal
    for particle in particles[:]:
        # Update the particle's individual state (position, alpha, size)
        particle.update(dt)
        # If the particle is dead (faded/shrunk), remove it from the list
        if particle.is_dead():
             try:
                 # Check if it still exists before removing
                 if particle in particles: particles.remove(particle)
             except ValueError:
                 pass # Ignore error if already removed

# Draws all active particles
def draw_particles():
    # Access the global list of particles
    global particles

    # If there are no particles, exit early
    if not particles: return

    # Save current style settings
    pushStyle(); ellipseMode(CENTER); noStroke() # Set drawing mode for particles

    # Draw each active particle
    for particle in particles:
        particle.draw()

    # Restore previous style settings
    popStyle()

# Updates the state of all active judgment displays
def update_judgment_displays(dt):
    # Access the global list of judgment displays
    global judgment_displays

    # Iterate through a copy of the list to allow removal
    for display in judgment_displays[:]:
        # Update the display's state (position, alpha)
        display.update(dt)
        # If the display has faded out, remove it
        if display.is_faded():
             try:
                 # Check if it still exists before removing
                 if display in judgment_displays: judgment_displays.remove(display)
             except ValueError:
                 pass # Ignore error if already removed

# Draws all active judgment displays
def draw_judgment_displays():
    # Access global variables needed for drawing
    global judgment_displays, my_custom_font, width, height

    # If there are no displays, exit early
    if not judgment_displays: return

    # Save current style settings and set text alignment
    pushStyle(); textAlign(CENTER, CENTER)

    # Define the colors associated with each judgment text
    judgment_colors = {
        "PERFECT": color(255, 255, 0), "GREAT": color(100, 255, 100),
        "GOOD": color(100, 200, 255), "MISS": color(255, 80, 80)
    }

    # Draw each active judgment display
    for display in judgment_displays:
        display.draw(my_custom_font, judgment_colors) # Pass font and color map

    # Restore previous style settings
    popStyle()

# Creates particle effects when a note is hit successfully
def create_hit_effect(track_index, judgment):
    # Access global variables related to effects and colors
    global particles, enable_particles
    global note_color_scheme, color_schemes
    global JUDGMENT_LINE_Y, TRACK_WIDTH, width

    # If particle effects are disabled in settings, do nothing
    if not enable_particles: return

    # Determine the position for the particle burst (center of the track at judgment line)
    x = calculate_track_x(track_index)
    y = JUDGMENT_LINE_Y
    # Default particle color (white)
    r, g, b = 255, 255, 255

    # Try to get the track's color from the active scheme
    try:
        active_scheme = color_schemes.get(note_color_scheme, color_schemes["default"])
        if 0 <= track_index < len(active_scheme):
             track_color = active_scheme[track_index]
             r, g, b = track_color["r"], track_color["g"], track_color["b"]
        else: print("Warning: Invalid track index {} for particle color.".format(track_index))
    except Exception as e: print("Error getting particle color: {}".format(e))

    # Define particle parameters based on judgment quality
    particle_count, speed_range, size_range = 0, (0,0), (0,0)
    initial_alpha = 255 # Start fully opaque

    # More particles, faster speed, larger size for better judgments
    if judgment == "PERFECT": particle_count, speed_range, size_range = 25, (2, 7), (6, 18)
    elif judgment == "GREAT": particle_count, speed_range, size_range = 15, (1.5, 5), (4, 14)
    elif judgment == "GOOD":  particle_count, speed_range, size_range = 8, (1, 4), (3, 10)
    else: return # No particles for MISS (or should be handled elsewhere)

    # Create the specified number of particles
    for _ in range(particle_count):
        # Randomize direction (angle) and speed
        angle = random(TWO_PI) # Random angle in radians
        speed = random(speed_range[0], speed_range[1]) # Random speed within range
        # Calculate initial velocity components
        dx = cos(angle) * speed
        dy = sin(angle) * speed
        # Randomize size
        size = random(size_range[0], size_range[1])
        # Slightly randomize starting position around the center point
        start_x = x + random(-TRACK_WIDTH/4, TRACK_WIDTH/4)
        start_y = y + random(-5, 5)

        # Create the new particle object and add it to the global list
        new_particle = Particle(start_x, start_y, dx, dy, size, r, g, b, initial_alpha)
        particles.append(new_particle)

# Registers the result of hitting or missing a note, updates score/combo, plays sound
def register_judgment(judgment, track_index):
    # Access global variables to update game state and play sounds
    global score, combo, max_combo, judgments, state
    global hit_sound_perfect, hit_sound_great, hit_sound_good, hit_sound_miss, sfx_volume
    global bgm, minim
    global notes_hit_count
    global judgment_displays
    global width

    # Increment the count for this judgment type
    judgments[judgment] = judgments.get(judgment, 0) + 1

    # Select the appropriate sound effect based on the judgment
    sound_to_play = None
    if judgment == "PERFECT": sound_to_play = hit_sound_perfect
    elif judgment == "GREAT": sound_to_play = hit_sound_great
    elif judgment == "GOOD": sound_to_play = hit_sound_good
    elif judgment == "MISS": sound_to_play = hit_sound_miss

    # Play the sound effect if it was loaded successfully
    if sound_to_play:
        try:
            sound_to_play.trigger() # Play the sound sample
        except AttributeError: print("Error: Sound object for {} missing.".format(judgment))
        except Exception as e: print("Error playing sound for {}: {}".format(judgment, e))

    # Handle MISS judgment specifically
    if judgment == "MISS":
        combo = 0 # Reset combo
        # If currently playing, a miss ends the game
        if state == "PLAYING":
            print("GAME OVER - Registered MISS!")
            state = "RESULTS" # Change state to results screen
            # Stop and rewind background music
            if bgm and bgm.isPlaying():
                bgm.pause(); bgm.rewind()
    # Handle non-MISS judgments (PERFECT, GREAT, GOOD)
    else:
        combo += 1 # Increment combo
        max_combo = max(max_combo, combo) # Update max combo if current is higher
        notes_hit_count += 1 # Increment count of notes hit

        # Calculate score based on judgment and combo
        base_score = {"PERFECT": 100, "GREAT": 75, "GOOD": 50}.get(judgment, 0)
        combo_multiplier = 1.0 + (combo * 0.01) # Simple combo multiplier
        score += base_score * combo_multiplier # Add score

    # Display the judgment text on screen (for all judgment types)
    show_judgment(judgment, track_index)

# Creates and adds a JudgmentDisplay object to the list
def show_judgment(judgment, track_index):
    # Access global list and layout variables
    global judgment_displays
    global JUDGMENT_LINE_Y, width

    # Calculate position for the judgment text (above the judgment line)
    x = calculate_track_x(track_index)
    y = JUDGMENT_LINE_Y - 70 # Position it vertically offset

    # Create the display object and add it to the list for rendering
    new_display = JudgmentDisplay(judgment, x, y)
    judgment_displays.append(new_display)

# Determines the judgment type based on the distance from the judgment line
def get_judgment_for_timing(distance):
    # Access global timing window constants
    global perfect_window, great_window, good_window

    # Check distance against timing windows (closest first)
    if distance <= perfect_window: return "PERFECT"
    elif distance <= great_window: return "GREAT"
    elif distance <= good_window: return "GOOD"
    # If distance is outside all windows, it's considered a miss (though usually handled by threshold)
    else: return "MISS"

# --- Input Handlers ---

# Handles keyboard presses
def keyPressed():
    # Access global state variables related to input and pausing
    global state, is_binding_key, binding_track_index, key_bindings, binding_prompt_text
    global is_paused, previous_state, minim, bgm
    # Access Processing's key and keyCode variables
    global key, keyCode

    # --- Global ESC Key Handling ---
    if key == ESC:
        key = 0 # Consume the ESC key event to prevent other actions

        # ESC during key binding cancels the binding process
        if is_binding_key:
            is_binding_key = False; binding_track_index = -1; binding_prompt_text = ""
            print("Key binding cancelled.")
        # ESC during gameplay pauses the game
        elif state == "PLAYING":
            state = "PAUSED"; is_paused = True
            if bgm and bgm.isPlaying(): bgm.pause() # Pause music
            print("Game Paused")
        # ESC while paused resumes the game
        elif state == "PAUSED":
            resume_game()
        # ESC in settings saves settings and returns to the previous state
        elif state == "SETTINGS":
             save_settings() # Save current settings
             state = previous_state; # Restore the state before settings
             is_binding_key = False; binding_prompt_text = "" # Ensure binding state is reset
             print("Settings saved. Returning to {}.".format(previous_state))
        return # Stop further processing for ESC

    # --- Key Binding Input Handling ---
    # If in settings, waiting for a key bind, and a track is selected
    if state == "SETTINGS" and is_binding_key and binding_track_index != -1:
        k = None; invalid_key_reason = None # Variables for the pressed key and validation
        # Check if the key is a standard character (unicode) and not ESC
        if isinstance(key, unicode) and len(key) == 1 and key != ESC:
            k = str(key).lower() # Convert to lowercase string
            # Validate if it's alphanumeric (letters or numbers)
            if not k.isalnum(): invalid_key_reason = "Only letters/numbers." ; k = None
        # Check if it's a special coded key (like arrows, shift, etc.)
        elif key == CODED: invalid_key_reason = "Special keys cannot be bound."
        # Handle other unexpected key types
        else: invalid_key_reason = "This key type cannot be bound."

        # If the key is invalid, update the prompt and wait for another key
        if invalid_key_reason:
            binding_prompt_text = invalid_key_reason + " Press another key."
            print("Invalid key for binding: {} ({})".format(key, invalid_key_reason))
            return # Stop processing this key press

        # If the key is valid (k is not None)
        if k:
            # Check if the chosen key is already bound to a *different* track
            current_bound_track = -1
            for bound_key, track_idx in key_bindings.items():
                if bound_key == k: current_bound_track = track_idx; break

            # If key is already bound to another track, show error and wait
            if current_bound_track != -1 and current_bound_track != binding_track_index:
                binding_prompt_text = "Key '{}' is already used for Track {}. Press another key.".format(k.upper(), current_bound_track + 1)
            # If the key is free or already bound to the *same* track
            else:
                # Find the old key previously bound to this track index (if any)
                old_key = None
                for ok, track_idx in key_bindings.items():
                    if track_idx == binding_track_index: old_key = ok; break
                # If there was an old key, and it's different from the new key, remove the old binding
                if old_key is not None and old_key != k and old_key in key_bindings:
                     del key_bindings[old_key]
                # Assign the new key to the target track index
                key_bindings[k] = binding_track_index
                print("Bound key '{}' to Track {}".format(k.upper(), binding_track_index + 1))
                # Save settings immediately after successful binding
                save_settings()
                # Reset binding state
                is_binding_key = False; binding_track_index = -1; binding_prompt_text = ""
        return # Stop processing after handling binding input

    # --- Gameplay Key Handling ---
    # Only process gameplay keys if not paused and not currently binding a key
    if not is_paused and not is_binding_key:
        game_k = None # Variable to hold the pressed key character
        # Get the character if it's a standard key press
        if isinstance(key, unicode) and len(key) == 1: game_k = str(key).lower()

        # If in the PLAYING state
        if state == "PLAYING":
            # Check if the pressed key is one of the bound gameplay keys
            if game_k and game_k in key_bindings:
                target_track_index = key_bindings[game_k] # Find the corresponding track index
                process_key_press(target_track_index) # Process the hit for that track

        # If in the RESULTS state
        elif state == "RESULTS":
            # Allow restarting the game by pressing SPACE
            if key == ' ':
                print("Restarting game from Results screen (Spacebar)...")
                restart_game()

# Handles mouse clicks
def mouseClicked(event=None): # event param for potential future use, not standard in Processing.py
    # Access global variables related to UI interaction, state, and settings
    global state, scroll_speed, is_binding_key, binding_track_index, binding_prompt_text
    global bgm, note_spawn_interval, note_spawn_probability, is_paused, last_time
    global current_music_track, available_music_tracks, active_settings_tab, previous_state
    global confirm_dialog_active, confirm_dialog_message, confirm_yes_action, confirm_no_action
    global music_volume, sfx_volume, enable_screen_shake, enable_particles, note_color_scheme
    global particles, judgment_displays, pressed_button_id, notes
    global hit_sound_perfect, hit_sound_great, hit_sound_good, hit_sound_miss, button_click_sound, minim
    global score, combo, max_combo, judgments, time_up, game_timer, notes_hit_count, track_highlight_timers, shake_intensity
    # Access Processing's mouse position and screen dimensions
    global mouseX, mouseY, width, height, color_schemes

    # Play button click sound effect if available
    if button_click_sound:
        try: button_click_sound.trigger()
        except Exception as e: print("Error playing button click sound: {}".format(e))

    # --- Confirmation Dialog Click Handling ---
    if confirm_dialog_active:
        # Define dialog button layout again (could be stored globally or passed)
        box_w = 450; box_h = 220; button_w = 130; button_h = 45; button_spacing = 30
        button_y_center = (height/2 - box_h/2) + box_h - button_h/2 - 25
        yes_x_center = width/2 - button_spacing/2 - button_w/2
        no_x_center = width/2 + button_spacing/2 + button_w/2
        yes_id = "confirm_yes"; no_id = "confirm_no"

        # Check if 'Yes' button was clicked
        if is_mouse_over_button_centered(yes_x_center, button_y_center, button_w, button_h):
            pressed_button_id = yes_id # Set pressed state for visual feedback
            if confirm_yes_action: confirm_yes_action() # Execute the action
            # Reset and hide the dialog
            confirm_dialog_active = False; confirm_yes_action = None; confirm_no_action = None
            return # Stop further click processing
        # Check if 'No' button was clicked
        elif is_mouse_over_button_centered(no_x_center, button_y_center, button_w, button_h):
            pressed_button_id = no_id
            if confirm_no_action: confirm_no_action() # Execute the (usually null) action
            # Reset and hide the dialog
            confirm_dialog_active = False; confirm_yes_action = None; confirm_no_action = None
            return # Stop further click processing
        # If click was inside dialog but not on buttons, do nothing more
        else: return

    # --- Gameplay Pause Button Click Handling ---
    if state == "PLAYING":
        # Check if the click was on the pause button (using distance squared for efficiency)
        dist_sq = distSq(mouseX, mouseY, PAUSE_BUTTON_X, PAUSE_BUTTON_Y)
        if dist_sq < (PAUSE_BUTTON_SIZE / 2)**2:
            # Pause the game
            state = "PAUSED"; is_paused = True
            if bgm and bgm.isPlaying(): bgm.pause() # Pause music
            print("Game Paused (via button)"); return # Stop further click processing

    # --- Pause Menu Click Handling ---
    elif state == "PAUSED":
        # Define pause menu button layout again
        button_w = 220; button_h = 50; button_spacing = 65; num_buttons = 4
        total_button_height = num_buttons * button_h + (num_buttons - 1) * (button_spacing - button_h)
        button_y_start_center = height/2 - total_button_height/2 + button_h/2
        # Define actions associated with each button ID
        actions = {
            "pause_resume": resume_game,
            "pause_restart": lambda: show_confirmation("Restart the current round?", restart_game),
            "pause_settings": lambda: enter_settings("PAUSED"), # Enter settings, remember we came from PAUSED
            "pause_menu": lambda: show_confirmation("Return to the main menu?", set_state_to_menu)
        }
        ids = ["pause_resume", "pause_restart", "pause_settings", "pause_menu"]

        # Check clicks on each button
        for i, btn_id in enumerate(ids):
             y_center = button_y_start_center + i * button_spacing
             if is_mouse_over_button_centered(width/2, y_center, button_w, button_h):
                 pressed_button_id = btn_id; actions[btn_id](); return # Set pressed state, execute action, stop

    # --- Settings Screen Click Handling ---
    elif state == "SETTINGS":
        # --- Tab Click Handling ---
        tabs = ["Audio", "Controls", "Visual"]; tab_width = width / len(tabs); tab_height = 40; tab_y = 80
        # Check if click is within the vertical bounds of the tabs
        if mouseY > tab_y and mouseY < tab_y + tab_height:
            # Check which tab was clicked horizontally
            for i in range(len(tabs)):
                tab_x = i * tab_width
                if mouseX > tab_x and mouseX < tab_x + tab_width:
                    # If a different tab was clicked, switch to it
                    if active_settings_tab != i:
                        active_settings_tab = i; is_binding_key = False; binding_prompt_text = "" # Reset binding state
                    return # Stop further click processing

        # --- Back Button Click Handling ---
        back_button_y_center = height - 70 + 50/2; back_button_w = 200; back_button_h = 50
        if is_mouse_over_button_centered(width/2, back_button_y_center, back_button_w, back_button_h):
            pressed_button_id = "settings_back"; save_settings(); state = previous_state # Save, restore state
            is_binding_key = False; binding_prompt_text = "" # Reset binding state
            print("Settings saved. Returning to {}.".format(previous_state)); return # Stop

        # Define content area start and control positions (needed for controls within tabs)
        content_y_start = tab_y + tab_height + 20; control_x = width * 0.6

        # --- Audio Tab Control Click Handling ---
        if active_settings_tab == 0:
            slider_width = 300; slider_handle_radius = 12 # Use radius for larger click target
            # Music Volume Slider Click (check vertical proximity)
            music_slider_y = content_y_start + 15
            if abs(mouseY - music_slider_y) < slider_handle_radius * 1.5: # Generous vertical target
                slider_x_start = control_x - slider_width/2; slider_x_end = control_x + slider_width/2
                # Check horizontal bounds and update volume if clicked on the track
                if mouseX >= slider_x_start and mouseX <= slider_x_end:
                    music_volume = constrain(map(mouseX, slider_x_start, slider_x_end, 0, 1), 0, 1) # Map click X to volume
                    if bgm: bgm.setGain(convertToDecibels(music_volume)) # Apply change immediately if music playing
                    print("Music Volume set to: {:.2f}".format(music_volume)); return # Stop
            # SFX Volume Slider Click
            sfx_slider_y = content_y_start + 65
            if abs(mouseY - sfx_slider_y) < slider_handle_radius * 1.5:
                slider_x_start = control_x - slider_width/2; slider_x_end = control_x + slider_width/2
                if mouseX >= slider_x_start and mouseX <= slider_x_end:
                    sfx_volume = constrain(map(mouseX, slider_x_start, slider_x_end, 0, 1), 0, 1)
                    vol_db = convertToDecibels(sfx_volume) # Apply change to all SFX samples
                    if hit_sound_perfect: hit_sound_perfect.setGain(vol_db)
                    # ... (apply to other SFX sounds) ...
                    if button_click_sound: button_click_sound.setGain(vol_db)
                    print("SFX Volume set to: {:.2f}".format(sfx_volume)); return # Stop

        # --- Controls Tab Click Handling ---
        elif active_settings_tab == 1:
            # If already waiting for a key, don't process clicks on bind buttons
            if is_binding_key: return
            # Define bind button layout again
            controls_setting_x = width/2; num_tracks = 4; button_w = 120; button_h = 45; button_spacing_x = 30
            total_width = num_tracks * button_w + (num_tracks - 1) * button_spacing_x
            button_start_x = controls_setting_x - total_width / 2
            button_y_center = content_y_start + 70 + button_h / 2
            # Check clicks on each bind button
            for i in range(num_tracks):
                x_center = button_start_x + button_w/2 + i * (button_w + button_spacing_x)
                if is_mouse_over_button_centered(x_center, button_y_center, button_w, button_h):
                    # Enter key binding mode for the clicked track
                    pressed_button_id = "settings_bind_{}".format(i); is_binding_key = True; binding_track_index = i
                    binding_prompt_text = "Press a key for Track {}...".format(i+1)
                    print("Waiting for key input for track {}...".format(i+1)); return # Stop

        # --- Visual Tab Control Click Handling ---
        elif active_settings_tab == 2:
            visual_setting_x = width/2; toggle_center_x = visual_setting_x + 50 # Center of toggle switches
            toggle_width = 60; toggle_height = 30 # Toggle dimensions for click check
            # Screen Shake Toggle Click
            toggle_y_shake = content_y_start + 20
            # Check click within toggle bounds
            if mouseX > toggle_center_x - toggle_width/2 and mouseX < toggle_center_x + toggle_width/2 and \
               mouseY > toggle_y_shake - toggle_height/2 and mouseY < toggle_y_shake + toggle_height/2:
                enable_screen_shake = not enable_screen_shake # Flip the boolean value
                print("Screen Shake: {}".format(enable_screen_shake)); return # Stop
            # Particle Effects Toggle Click
            toggle_y_particles = content_y_start + 70
            if mouseX > toggle_center_x - toggle_width/2 and mouseX < toggle_center_x + toggle_width/2 and \
               mouseY > toggle_y_particles - toggle_height/2 and mouseY < toggle_y_particles + toggle_height/2:
                enable_particles = not enable_particles # Flip the value
                print("Particle Effects: {}".format(enable_particles)); return # Stop

            # Color Scheme Radio Button Click
            color_scheme_base_y = content_y_start + 130 + 35; radio_spacing = 35 # Layout
            radio_center_x = visual_setting_x + 30; radio_radius = 10; label_clickable_width = 150 # Click target area
            schemes_dict_keys = color_schemes.keys() # Get scheme names
            # Check click for each radio button
            for i, scheme_key in enumerate(schemes_dict_keys):
                y = color_scheme_base_y + i * radio_spacing # Y position of this radio button
                # Check vertical proximity and horizontal area (including label)
                if abs(mouseY - y) < radio_radius + 5: # Generous vertical target
                    # Check horizontal click area (from label start to just past radio circle)
                    if mouseX > radio_center_x - label_clickable_width and mouseX < radio_center_x + radio_radius + 5:
                        # If a different scheme was clicked, update the setting
                        if note_color_scheme != scheme_key:
                            note_color_scheme = scheme_key
                            print("Color Scheme set to: {}".format(scheme_key)); return # Stop

    # --- Main Menu Click Handling ---
    elif state == "MENU":
        # Define menu button layout again
        menu_button_y_start_center = 180 + 50/2; button_h = 50; button_spacing = 60; button_w = 300
        difficulties = ["Easy", "Normal", "Hard", "Expert"]
        # Define settings associated with each difficulty
        difficulty_settings = {
            "Easy":   {"speed": 250, "interval": 0.9, "prob": 0.55},
            "Normal": {"speed": 350, "interval": 0.7, "prob": 0.65},
            "Hard":   {"speed": 475, "interval": 0.5, "prob": 0.75},
            "Expert": {"speed": 600, "interval": 0.35,"prob": 0.85}
        }
        # Check clicks on difficulty buttons
        for i, difficulty in enumerate(difficulties):
            y_center = menu_button_y_start_center + i * button_spacing
            if is_mouse_over_button_centered(width/2, y_center, button_w, button_h):
                pressed_button_id = "menu_{}".format(difficulty.lower()) # Set pressed state
                settings = difficulty_settings.get(difficulty, difficulty_settings["Normal"]) # Get settings for selected difficulty
                # Apply difficulty settings to global variables
                scroll_speed = settings["speed"]; note_spawn_interval = settings["interval"]; note_spawn_probability = settings["prob"]
                print("Selected Difficulty: {}, Speed={}, Interval={}, Prob={}".format(difficulty, scroll_speed, note_spawn_interval, note_spawn_probability))
                restart_game(); return # Start the game with new settings

        # Check click on Settings button
        settings_y_center = menu_button_y_start_center + len(difficulties) * button_spacing
        if is_mouse_over_button_centered(width/2, settings_y_center, button_w, button_h):
            pressed_button_id = "menu_settings"; enter_settings("MENU"); return # Enter settings, remember we came from MENU

    # --- Results Screen Click Handling ---
    elif state == "RESULTS":
        # Define results button layout again
        results_button_y_center = height - 100 + 50/2; button_w = 200; button_h = 50; button_spacing_x = 40
        retry_x_center = width/2 - button_spacing_x/2 - button_w/2
        menu_x_center = width/2 + button_spacing_x/2 + button_w/2

        # Check click on Retry button
        if is_mouse_over_button_centered(retry_x_center, results_button_y_center, button_w, button_h):
            pressed_button_id = "results_retry"; restart_game(); return # Restart the game
        # Check click on Menu button
        if is_mouse_over_button_centered(menu_x_center, results_button_y_center, button_w, button_h):
            pressed_button_id = "results_menu"; set_state_to_menu(); return # Go back to main menu

# Utility function to check if mouse is over a centered button
def is_mouse_over_button_centered(x_center, y_center, w, h):
    # Access Processing's mouse position variables
    global mouseX, mouseY
    # Check if mouse coordinates are within the button's rectangular bounds
    return (mouseX >= x_center - w/2 and mouseX <= x_center + w/2 and
            mouseY >= y_center - h/2 and mouseY <= y_center + h/2)

# Handles mouse button releases
def mouseReleased():
    # Access global variable tracking pressed button
    global pressed_button_id
    # Reset the pressed button ID when the mouse is released
    pressed_button_id = None

# Handles mouse dragging events (primarily for sliders)
def mouseDragged():
    # Access global variables related to settings sliders and state
    global music_volume, sfx_volume, bgm, active_settings_tab, state, minim
    global hit_sound_perfect, hit_sound_great, hit_sound_good, hit_sound_miss, button_click_sound
    # Access Processing's mouse position and screen width
    global mouseX, mouseY, width

    # Only handle drags if in settings and on the audio tab
    if state != "SETTINGS" or active_settings_tab != 0: return

    # Define slider layout again
    content_y_start = 80 + 40 + 20; control_x = width * 0.6; slider_width = 300

    # Music Volume Slider Drag
    music_slider_y = content_y_start + 15
    # Check if dragging vertically near the slider
    if abs(mouseY - music_slider_y) < 15: # Vertical tolerance for drag activation
        slider_x_start = control_x - slider_width/2; slider_x_end = control_x + slider_width/2
        # Constrain mouse X to the slider's bounds before mapping
        constrained_mouseX = constrain(mouseX, slider_x_start, slider_x_end)
        # Map constrained X position to volume (0-1)
        new_volume = constrain(map(constrained_mouseX, slider_x_start, slider_x_end, 0, 1), 0, 1)
        # Update volume and apply change if it's different
        if new_volume != music_volume:
             music_volume = new_volume
             if bgm: bgm.setGain(convertToDecibels(music_volume)) # Apply change immediately
        return # Stop processing (don't check SFX slider)

    # SFX Volume Slider Drag
    sfx_slider_y = content_y_start + 65
    if abs(mouseY - sfx_slider_y) < 15:
        slider_x_start = control_x - slider_width/2; slider_x_end = control_x + slider_width/2
        constrained_mouseX = constrain(mouseX, slider_x_start, slider_x_end)
        new_volume = constrain(map(constrained_mouseX, slider_x_start, slider_x_end, 0, 1), 0, 1)
        if new_volume != sfx_volume:
             sfx_volume = new_volume
             vol_db = convertToDecibels(sfx_volume) # Apply change to all SFX samples
             if hit_sound_perfect: hit_sound_perfect.setGain(vol_db)
             # ... (apply to other SFX sounds) ...
             if button_click_sound: button_click_sound.setGain(vol_db)
        return # Stop processing

# --- State Management Functions ---

# Shows the confirmation dialog with a specific message and action
def show_confirmation(message, yes_func):
    # Access global variables controlling the dialog
    global confirm_dialog_active, confirm_dialog_message, confirm_yes_action, confirm_no_action
    # Activate the dialog
    confirm_dialog_active = True
    # Set the message and the function to call if 'Yes' is clicked
    confirm_dialog_message = message
    confirm_yes_action = yes_func
    # Set 'No' action to do nothing (could be customized if needed)
    confirm_no_action = lambda: None

# Enters the settings screen, remembering the state it came from
def enter_settings(origin_state):
    # Access global variables for state management
    global state, previous_state, is_binding_key, binding_prompt_text, active_settings_tab
    # Store the state we were in before entering settings
    previous_state = origin_state
    # Set the current state to SETTINGS
    state = "SETTINGS"
    # Reset settings-specific states (like key binding mode)
    is_binding_key = False; binding_prompt_text = ""
    active_settings_tab = 0 # Default to the first tab (Audio)
    print("Entering Settings from {}".format(origin_state))

# Resets the game to the initial playing state
def restart_game():
    # Access global variables to reset game state
    global state, score, combo, max_combo, judgments, notes, particles, judgment_displays
    global bgm, last_time, shake_intensity, time_since_last_spawn, is_paused
    global current_music_track, music_volume, available_music_tracks
    global game_timer, notes_hit_count, time_up
    global track_highlight_timers, DEFAULT_MUSIC_TRACK, minim

    print("Restarting game...")

    # Reset core game state variables
    state = "PLAYING"; is_paused = False
    score = 0; combo = 0; max_combo = 0
    judgments = {"PERFECT": 0, "GREAT": 0, "GOOD": 0, "MISS": 0} # Reset judgment counts
    notes = []              # Clear existing notes
    particles = []          # Clear existing particles
    judgment_displays = []  # Clear existing judgment displays
    time_up = False         # Reset game timer flag

    # Reset track highlight timers
    for i in track_highlight_timers: track_highlight_timers[i] = 0.0

    # Reset timers and counters
    game_timer = 0.0; notes_hit_count = 0; time_since_last_spawn = 0.0
    shake_intensity = 0.0   # Reset screen shake

    # Reset frame timing
    try: current_time = time.time()
    except AttributeError: current_time = millis() / 1000.0
    last_time = current_time

    # --- Restart Background Music ---
    # Stop and release the current BGM object if it exists
    if bgm:
        if bgm.isPlaying(): bgm.pause()
        bgm.rewind(); bgm.close(); bgm = None # Close releases resources

    # Determine which music track to load (use default if current is invalid)
    effective_music_track = current_music_track if current_music_track in available_music_tracks else DEFAULT_MUSIC_TRACK

    # Load and play the selected music track if available and Minim is initialized
    if effective_music_track and minim:
        try:
            bgm_path = dataPath(effective_music_track) # Get full path
            print("Loading BGM from: '{}'".format(bgm_path))
            bgm = minim.loadFile(bgm_path) # Load the audio file
            # If loading was successful
            if bgm:
                bgm.setGain(convertToDecibels(music_volume)) # Set volume
                bgm.loop() # Start playing in a loop
                print("Background music '{}' started.".format(effective_music_track))
            # Handle case where loadFile returns None (e.g., file not found, format unsupported)
            else:
                 print("ERROR: minim.loadFile returned None for '{}'".format(bgm_path))
                 bgm = None
        # Catch any other exceptions during loading or playback
        except Exception as e:
            print("ERROR loading or starting BGM '{}': {}".format(effective_music_track, e))
            bgm = None
    # Handle case where no music track is selected or Minim failed
    else:
        print("No available/valid music track or Minim not initialized. Cannot play BGM.")
        bgm = None

    print("Game ready!") # Confirmation message

# Resumes the game from the paused state
def resume_game():
    # Access global variables related to pausing and timing
    global state, is_paused, last_time, bgm

    # Only resume if currently paused
    if state != "PAUSED": return

    # Change state back to playing and unpause
    state = "PLAYING"; is_paused = False

    # Reset frame timing to avoid a large jump after pause
    try: last_time = time.time()
    except AttributeError: last_time = millis() / 1000.0

    # Resume background music if it was paused
    if bgm and not bgm.isPlaying():
        try: bgm.play()
        except Exception as e: print("Error resuming BGM: {}".format(e))

    print("Game Resumed")

# Transitions the game state to the main menu
def set_state_to_menu():
    # Access global variables for state and audio
    global state, is_paused, bgm, minim
    # Access lists of game objects to clear them
    global particles, judgment_displays, notes

    # Set state to MENU and ensure not paused
    state = "MENU"; is_paused = False

    # Stop and rewind background music if playing
    if bgm:
        try:
            if bgm.isPlaying(): bgm.pause()
            bgm.rewind()
        except Exception as e: print("Error stopping BGM: {}".format(e))
        # Note: We don't close the BGM here, it might be restarted if user plays again

    # Clear active game objects
    notes = []; particles = []; judgment_displays = []
    print("Returned to Menu")

# --- Utility Calculation Functions ---

# Calculates the center X coordinate for a given track index (0-3)
def calculate_track_x(track_index):
    # Access global layout variables
    global width, TRACK_WIDTH
    # Define track layout parameters
    num_tracks = 4; track_spacing = 20
    # Calculate total width of the track area
    total_track_area_width = num_tracks * TRACK_WIDTH + (num_tracks - 1) * track_spacing
    # Calculate starting X to center the area
    start_x = (width - total_track_area_width) / 2
    # Calculate the center X of the specified track index
    center_x = start_x + TRACK_WIDTH/2 + track_index * (TRACK_WIDTH + track_spacing)

    # Return the calculated center X if index is valid
    if 0 <= track_index < num_tracks: return center_x
    # Return screen center as a fallback for invalid index
    else:
        print("Warning: Invalid track_index {} in calculate_track_x".format(track_index))
        return width / 2

# Calculates the squared distance between two points (avoids square root for faster comparison)
def distSq(x1, y1, x2, y2):
    return (x2 - x1)**2 + (y2 - y1)**2

# --- Settings Persistence ---

# Loads game settings from the JSON file, using defaults if file not found or invalid
def load_settings():
    # Access global variables that store the settings
    global DEFAULT_KEY_BINDINGS, DEFAULT_MUSIC_TRACK, SETTINGS_FILENAME, available_music_tracks
    global music_volume, sfx_volume, enable_screen_shake, enable_particles, note_color_scheme
    global key_bindings, current_music_track
    # Access audio objects to apply loaded volume
    global hit_sound_perfect, hit_sound_great, hit_sound_good, hit_sound_miss, button_click_sound, color_schemes, minim

    # Define default settings structure
    default_settings = {
        "key_bindings": DEFAULT_KEY_BINDINGS.copy(), # Use copy to avoid modifying default dict
        "music_track": DEFAULT_MUSIC_TRACK,
        "music_volume": 0.8, "sfx_volume": 1.0,
        "enable_screen_shake": True, "enable_particles": True,
        "note_color_scheme": "default"
    }
    loaded_successfully = False # Flag to track if loading worked
    settings_path = dataPath(SETTINGS_FILENAME) # Get full path to settings file

    try:
        # Attempt to open and read the settings file
        with open(settings_path, 'r') as f:
            # Load JSON data from the file
            loaded_data = json.load(f, encoding='utf-8') # Specify encoding for safety

            # --- Validate and Load Key Bindings ---
            keys = loaded_data.get("key_bindings")
            # Perform comprehensive validation on loaded key bindings
            keys_valid = isinstance(keys, dict) and len(keys) == 4 and \
                         all(isinstance(k, (str, unicode)) and len(k) == 1 and k.islower() and k.isalnum() for k in keys.keys()) and \
                         all(isinstance(v, int) and 0 <= v <= 3 for v in keys.values()) and \
                         len(set(keys.values())) == 4 # Ensure all track indices (0-3) are present exactly once
            # Use loaded keys if valid, otherwise use defaults
            key_bindings = {str(k): v for k, v in keys.items()} if keys_valid else default_settings["key_bindings"]
            if not keys_valid: print("Warning: Invalid key bindings in {}, using defaults.".format(SETTINGS_FILENAME))

            # --- Load Music Track (Use default for now, selection not implemented) ---
            # loaded_track = loaded_data.get("music_track", default_settings["music_track"])
            # current_music_track = loaded_track if loaded_track in available_music_tracks else default_settings["music_track"]
            # Simplified: always use default until selection is added
            current_music_track = DEFAULT_MUSIC_TRACK

            # --- Load Audio Volumes (with validation) ---
            music_volume = constrain(loaded_data.get("music_volume", default_settings["music_volume"]), 0.0, 1.0)
            sfx_volume = constrain(loaded_data.get("sfx_volume", default_settings["sfx_volume"]), 0.0, 1.0)

            # --- Load Boolean Toggles ---
            enable_screen_shake = bool(loaded_data.get("enable_screen_shake", default_settings["enable_screen_shake"]))
            enable_particles = bool(loaded_data.get("enable_particles", default_settings["enable_particles"]))

            # --- Load Color Scheme (with validation) ---
            loaded_scheme = loaded_data.get("note_color_scheme", default_settings["note_color_scheme"])
            # Use loaded scheme only if it exists in our defined schemes
            note_color_scheme = loaded_scheme if loaded_scheme in color_schemes else default_settings["note_color_scheme"]
            if note_color_scheme != loaded_scheme: print("Warning: Invalid color scheme '{}', using default.".format(loaded_scheme))

            # Mark loading as successful
            loaded_successfully = True
            print("Settings loaded successfully from {}.".format(SETTINGS_FILENAME))

    # Handle file not found error
    except IOError:
        print("Warning: {} not found. Initializing with default settings.".format(SETTINGS_FILENAME))
    # Handle JSON decoding errors or invalid data structure
    except (ValueError, KeyError, TypeError) as e:
        print("Warning: Error reading/validating {}. Using defaults. Error: {}".format(SETTINGS_FILENAME, e))
    # Catch any other unexpected errors during file reading
    except Exception as e:
        print("Unexpected error loading settings: {}. Using defaults.".format(e))

    # If loading failed for any reason, explicitly apply default settings
    if not loaded_successfully:
        key_bindings = default_settings["key_bindings"]
        current_music_track = default_settings["music_track"]
        music_volume = default_settings["music_volume"]
        sfx_volume = default_settings["sfx_volume"]
        enable_screen_shake = default_settings["enable_screen_shake"]
        enable_particles = default_settings["enable_particles"]
        note_color_scheme = default_settings["note_color_scheme"]

    # Apply the final SFX volume (loaded or default) to the sound objects
    # This needs to happen *after* sounds are potentially loaded in setup
    try:
        vol_db = convertToDecibels(sfx_volume)
        if hit_sound_perfect: hit_sound_perfect.setGain(vol_db)
        if hit_sound_great: hit_sound_great.setGain(vol_db)
        if hit_sound_good: hit_sound_good.setGain(vol_db)
        if hit_sound_miss: hit_sound_miss.setGain(vol_db)
        if button_click_sound: button_click_sound.setGain(vol_db)
    except Exception as e:
        # Catch errors if sounds weren't loaded properly
        print("Error applying SFX volume after load/default: {}".format(e))

# Saves current game settings to the JSON file
def save_settings():
    # Access global variables holding the current settings values
    global key_bindings, current_music_track, SETTINGS_FILENAME
    global music_volume, sfx_volume, enable_screen_shake, enable_particles, note_color_scheme

    # Create a dictionary containing the settings to save
    settings_to_save = {
        "key_bindings": key_bindings,
        "music_track": current_music_track, # Save selected track (even if default for now)
        "music_volume": music_volume, "sfx_volume": sfx_volume,
        "enable_screen_shake": enable_screen_shake,
        "enable_particles": enable_particles,
        "note_color_scheme": note_color_scheme
    }
    # Get the full path to the settings file
    file_path = dataPath(SETTINGS_FILENAME)
    try:
        # Open the file in write mode ('w')
        with open(file_path, 'w') as f:
            # Write the settings dictionary to the file as JSON
            # indent=4 makes the file human-readable
            # ensure_ascii=False helps with potential non-ASCII characters in future
            json.dump(settings_to_save, f, indent=4, encoding='utf-8', ensure_ascii=False)
        print("Settings successfully saved to {}.".format(file_path))
    # Handle file writing errors (e.g., permissions)
    except IOError as e:
        print("ERROR: Could not write settings to {}. Check permissions? {}".format(file_path, e))
    # Handle other potential errors during JSON serialization or writing
    except Exception as e:
        print("ERROR saving settings: {}".format(e))

# --- Cleanup ---

# Function called by Processing when the sketch is stopped/closed
def stop():
    # Access global audio objects that need cleanup
    global minim, bgm

    print("Stopping Minim and closing BGM...")
    # Close the background music file to release resources
    if bgm:
        try:
            bgm.close()
        except Exception as e:
            print("Error closing BGM: {}".format(e))
    # Stop the Minim audio engine
    if minim:
        try:
            minim.stop()
        except Exception as e:
            print("Error stopping Minim: {}".format(e))

    # Attempt to call the superclass's stop method if it exists (good practice in Processing)
    try:
        # Get the stop method from the parent class (if any)
        super_stop = getattr(super(type(this), this), 'stop', None)
        # Call it if it's callable
        if callable(super_stop):
             super_stop()
        else:
             print("Could not call super.stop()") # Should not happen in standard Processing sketch
    except Exception as e:
        print("Error calling super.stop(): {}".format(e))
