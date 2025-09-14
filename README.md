# VisionFlux - AI-Powered RTSP Camera Monitoring

VisionFlux is an intelligent computer vision application that monitors RTSP camera feeds and generates real-time alerts based on custom AI prompts and event detection.

## Features

- 🎥 **RTSP Camera Integration** - Connect to any RTSP camera feed
- 🤖 **AI-Powered Detection** - Use modern AI models for intelligent event detection
- 🚨 **Custom Alert System** - Configure custom prompts and get real-time notifications
- 🌐 **Web Dashboard** - Modern web interface for monitoring and configuration
- 📊 **Event Logging** - Track and analyze detected events over time
- ⚡ **Real-time Processing** - Low-latency video processing and analysis

## Architecture

- **Backend**: FastAPI with async processing
- **Computer Vision**: OpenCV + YOLO/Transformers
- **AI Models**: Hugging Face Transformers for image analysis
- **Frontend**: HTML/CSS/JavaScript dashboard
- **Alerts**: Multiple notification channels

## Quick Start

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the Application**

   ```bash
   python main.py
   ```

4. **Access Dashboard**
   Open http://localhost:8000 in your browser

## Configuration

### RTSP Camera Setup

- Add your camera's RTSP URL in the configuration
- Support for multiple camera feeds
- Automatic reconnection on stream failure

### Custom Event Detection

- Define custom prompts for specific scenarios
- Configure detection sensitivity
- Set up alert conditions and thresholds

### Alert Channels

- Email notifications
- Webhook integration
- Desktop notifications
- Custom integrations

## Example Use Cases

- **Security Monitoring**: Detect unauthorized access, suspicious activities
- **Safety Compliance**: Monitor for safety equipment usage, restricted area access
- **Operational Insights**: Track customer behavior, queue lengths, occupancy
- **Quality Control**: Detect defects, monitor processes

## Project Structure

```
VisionFlux/
├── main.py                 # Main application entry point
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   ├── api/              # API endpoints
│   └── utils/            # Utility functions
├── ai_models/            # AI model implementations
├── static/               # Web assets
├── templates/            # HTML templates
├── tests/               # Test files
└── docs/                # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

