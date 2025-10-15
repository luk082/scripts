# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **professional MicroMelon Rover control system** with a modern, modular architecture featuring multiple interface modes, comprehensive safety systems, and enterprise-grade error handling. The system supports keyboard control, GUI interfaces, and advanced computer vision-based gesture recognition. Currently **Windows-only** with planned Mac support.

## Quick Start

### Installation
```powershell
# Run the automated installer
.\install.ps1

# Or install with development tools
.\install.ps1 -Dev
```

### First Run
```powershell
# Test the system
python rover.py --test-connection --target simulator

# Configure settings
python rover.py --config-wizard

# Start with GUI simulator
python rover.py --mode gui --target simulator
```

## Modern Architecture

The system now uses a **professional, modular architecture** with:

- **Centralized Configuration** (`config.py`): JSON-based settings management
- **Unified CLI Interface** (`rover.py`): Single entry point with comprehensive options
- **Modular Controllers** (`rover_base.py`): Abstract base classes with BLE/simulator implementations
- **Advanced Error Handling** (`error_handling.py`): Logging, retry logic, performance monitoring
- **Safety Management**: Collision avoidance, emergency stops, sensor validation
- **Professional Testing**: Comprehensive test suite with mocking and coverage

## Common Commands

### Control Modes
```powershell
# Keyboard control (enhanced with modern UI)
python rover.py --mode keyboard --target simulator
python rover.py --mode keyboard --target physical --port 1234

# GUI control (professional interface)
python rover.py --mode gui --target simulator
python rover.py --mode gui --target physical --port 1234

# Gesture recognition (computer vision)
python rover.py --mode gesture --target simulator
python rover.py --mode gesture --target physical --port 1234
```

### System Management
```powershell
# Configuration wizard
python rover.py --config-wizard

# System status and diagnostics
python rover.py --status --target simulator
python rover.py --test-connection --target physical

# Training and development
python rover.py --train-gestures
python test_rover_system.py
```

### Advanced Options
```powershell
# Custom configuration
python rover.py --mode gui --target simulator --config custom_config.json

# Debug mode with detailed logging
python rover.py --mode keyboard --target simulator --debug

# Disable safety systems (use with caution)
python rover.py --mode keyboard --target simulator --no-safety

# Session recording for analysis
python rover.py --mode gesture --target simulator --record-session test_session
```

## Advanced Architecture

### Core Components

**Modern Controller Architecture:**
- `RoverControllerBase`: Abstract base class with safety and sensor management
- `BLERoverController`: Physical rover connection with auto-retry and port validation
- `SimulatorRoverController`: Local simulator connection for safe testing
- Factory pattern: `create_rover_controller(config, target_type, port)`

**Professional Interface System:**
1. **Unified CLI** (`rover.py`): Single entry point with argparse and comprehensive options
2. **Modular Interfaces** (`interfaces/`): Pluggable interface classes (keyboard, gui, gesture)
3. **Configuration Management** (`config.py`): Centralized JSON-based settings with validation
4. **Error Handling Framework** (`error_handling.py`): Logging, recovery, performance monitoring

**Enterprise Safety Features:**
- `SafetyManager`: Collision avoidance, battery monitoring, flip detection
- `SensorManager`: Robust sensor reading with caching and error recovery  
- Emergency stop functionality with manual reset requirements
- Motor speed limiting and safety overrides

### Key Architectural Patterns

**Dual Implementation Strategy:**
- Every major script has both physical rover and simulator versions
- Simulator versions use IP connection, physical use BLE
- Identical control logic between versions enables safe testing

**Sensor Integration:**
- Centralized sensor data dictionaries in GUI/gesture scripts
- Periodic sensor updates (typically 0.5-2Hz) to avoid overwhelming the connection
- Error handling for sensor communication failures

**Performance Optimization (Gesture Scripts):**
- Camera resolution optimization (640x480 for speed)
- MediaPipe model complexity tuning
- Frame processing rate control
- Prediction history smoothing for stable control

### Machine Learning Architecture

**Gesture Recognition Pipeline:**
1. **Data Collection** (`train.py`): Systematic landmark collection with positional/rotational variations
2. **Feature Extraction**: 21-point hand landmarks → normalized relative coordinates + finger tip distances
3. **Model**: RandomForest classifier with 200 estimators
4. **Real-time Prediction**: MediaPipe → landmark extraction → model inference → motor commands

**Gesture Mapping:**
- `x+`: Forward (30, 30)
- `x-`: Backward (-20, -20) 
- `y+`: Turn right (5, 10)
- `y-`: Turn left (10, 5)
- `n`: Stop/neutral (0, 0)

## Development Notes

### Connection Management
- Always call `rc.stopRover()` and `rc.end()` in cleanup
- Physical rover requires manual port entry - no auto-discovery
- Connection timeouts are expected and handled gracefully

### Color System
- Standardized 11-color LED palette across all scripts
- Colors defined as both `COLOURS` enum values and RGB tuples for display
- Color cycling typically bound to 'c' key or click events

### Error Handling Patterns
- Sensor reading failures default to "N/A" or "Error" strings
- LED control failures are logged but don't crash the program  
- Camera/MediaPipe failures exit gracefully with cleanup

### Performance Considerations
- Gesture recognition optimized for real-time performance over accuracy
- Sensor polling rates balanced to avoid communication bottlenecks
- Frame rate limiting in GUI scripts to maintain 60 FPS rendering

### Testing Strategy
- Use simulator versions for initial development and testing
- Physical rover testing requires Bluetooth pairing
- Gesture model training requires 100+ samples per gesture for reliability

## Platform Limitations
- **Windows only** - Mac support planned but not implemented
- Requires specific hardware (MicroMelon rover) for physical testing
- Gesture recognition requires webcam access and good lighting conditions