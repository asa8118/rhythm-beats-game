# Rhythm Beats Game

A full-featured rhythm game built in Python/Processing featuring dynamic note generation, real-time audio synchronization, and advanced particle effects.

![Game Demo](demo.gif)
*Screenshot coming soon*

## Features

### Core Gameplay
- 4-track rhythm gameplay with precision timing windows (Perfect/Great/Good/Miss)
- Dynamic note spawning system with adjustable difficulty levels
- Real-time combo system with score multipliers
- Multiple difficulty modes (Easy, Normal, Hard, Expert)

### Visual Effects
- Particle system with 1000+ simultaneous particles
- Screen shake effects on successful hits
- Customizable color schemes (Default, High-Contrast, Colorblind-Friendly)
- Smooth animations and visual feedback

### Audio System
- Multi-layered audio processing using Minim library
- Independent music and SFX volume controls
- Sub-50ms timing accuracy for rhythm detection
- Custom hit sounds for each judgment type

### Customization
- Fully remappable key bindings
- Persistent settings storage (JSON)
- Multiple visual themes
- Adjustable gameplay parameters

## Technical Implementation

**Languages & Frameworks:**
- Python/Processing
- Minim Audio Library

**Architecture:**
- Object-oriented design with separate classes for Notes, Particles, and UI elements
- Delta-time based game loop for consistent performance
- Event-driven input system
- JSON-based settings persistence

**Code Stats:**
- 1,000+ lines of code
- Custom particle physics engine
- ATS (Applicant Tracking System) with timing windows
- Settings management with validation

## Installation

1. Install [Processing 3+](https://processing.org/download)
2. Install Minim library:
   - Sketch → Import Library → Add Library → Search "Minim"
3. Clone this repository:
   ```bash
   git clone https://github.com/asa8118/rhythm-beats-game.git
   ```
4. Open `rhythm_beats.pde` in Processing
5. Press Run (or Ctrl+R)

## How to Play

- Press the corresponding keys (D, F, J, K by default) when notes reach the judgment line
- Timing determines your score: Perfect > Great > Good > Miss
- Build combos for score multipliers
- Complete the song without missing to win!

## Controls

**Default Keys:**
- D: Track 1
- F: Track 2
- J: Track 3
- K: Track 4
- ESC: Pause/Resume
- Space: Retry (on results screen)

**All keys are customizable in Settings**

## Project Structure

```
rhythm-beats-game/
├── rhythm_beats.pde       # Main game code (1000+ lines)
├── README.md             # This file
└── data/                 # Audio and visual assets
    ├── hit_perfect.wav
    ├── hit_great.wav
    ├── hit_good.wav
    ├── hit_miss.wav
    ├── button_click.wav
    ├── background_music.mp3
    └── SuperPixel-m2L8j.ttf
```

## Game States

- **Menu**: Difficulty selection and settings
- **Playing**: Active gameplay with note spawning
- **Paused**: Pause menu with resume/restart options
- **Results**: Score summary and judgment breakdown
- **Settings**: Audio, controls, and visual customization

## Development

**Course Project:** Introduction to Computer Science  
**Institution:** New York University Abu Dhabi  
**Semester:** Spring 2025

This project demonstrates:
- Game development fundamentals
- Audio-visual synchronization
- Event-driven programming
- Data persistence
- UI/UX design
- Object-oriented architecture

## Future Improvements

- Additional songs and difficulty levels
- Online leaderboard system
- Custom song import functionality
- Replay system
- More visual themes

## License

Academic project - code available for educational purposes.

## Contact

**Abdulla Saad Almemari**  
Computer Science @ NYU Abu Dhabi  
Email: asa8118@nyu.edu  

---

*Built with Processing and passion for rhythm games*
