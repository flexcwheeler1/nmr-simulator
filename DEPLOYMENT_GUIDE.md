# NMR Spectra Simulator - Deployment Guide

## Overview

The NMR Spectra Simulator can now be deployed in multiple ways:

1. **Desktop GUI Application** (Original tkinter version)
2. **Web Application** (Flask-based)
3. **Standalone Executable** (Single .exe file)
4. **Docker Container** (Web app in container)

## 🖥️ Desktop GUI Application

### Quick Start
```bash
python launcher.py --gui
```

### Manual Start
```bash
python main.py
```

**Features:**
- Full-featured desktop interface
- All advanced features (visual grouping, export, etc.)
- Works offline
- Best for power users and research

---

## 🌐 Web Application

### Quick Start
```bash
python launcher.py --web
```

### Manual Start
```bash
python web_app.py
```

**Access:** Open browser to `http://localhost:5000`

**Features:**
- Modern responsive web interface
- Accessible from any device with a browser
- Easy to share and deploy
- Great for educational use

### Production Deployment

#### Using Gunicorn (Linux/Mac)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

#### Using Waitress (Windows)
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 web_app:app
```

---

## 📦 Standalone Executable

### Build Executable
```bash
python launcher.py --build
```

### Manual Build
```bash
python build_exe.py
# OR
python -m PyInstaller nmr_simulator.spec
```

**Output:** `dist/NMR-Spectra-Simulator.exe`

**Features:**
- Single file, no installation required
- Include all dependencies
- Perfect for distribution
- Works on systems without Python

---

## 🐳 Docker Deployment

### Build and Run
```bash
docker build -t nmr-simulator .
docker run -p 5000:5000 nmr-simulator
```

### Using Docker Compose
```bash
docker-compose up -d
```

**Access:** `http://localhost:5000`

**Features:**
- Isolated environment
- Easy scaling
- Production-ready
- Cross-platform deployment

---

## 📋 Requirements

### Core Requirements
- Python 3.8+
- NumPy, Matplotlib, SciPy
- Requests, BeautifulSoup4

### GUI Requirements
- tkinter (usually included with Python)

### Web Requirements
- Flask
- Jinja2

### Build Requirements
- PyInstaller

### Install All Requirements
```bash
pip install -r requirements_full.txt
```

---

## 🚀 Universal Launcher

Use the universal launcher for easy access to all modes:

```bash
python launcher.py
```

**Interactive Menu:**
1. Desktop GUI (tkinter)
2. Web Application (Flask)  
3. Build Standalone Executable
4. Exit

**Command Line Options:**
- `--gui`: Start desktop GUI
- `--web`: Start web application
- `--build`: Build standalone executable

---

## 🔧 Configuration

### Web Application
- Port: 5000 (configurable in `web_app.py`)
- Host: localhost (change to 0.0.0.0 for external access)
- Debug: Enabled in development

### Standalone Executable
- All dependencies included
- No external configuration needed
- Antivirus software may need approval

### Docker
- Port mapping: 5000:5000
- Volume mounting for exports
- Health checks included

---

## 🎯 Use Cases

### Research/Academic
- **Desktop GUI**: Full features, offline use
- **Docker**: Shared lab environments

### Educational
- **Web App**: Easy student access
- **Standalone**: No installation classrooms

### Distribution
- **Standalone**: End-user distribution
- **Docker**: Server deployment

---

## 🛠️ Troubleshooting

### Common Issues

#### Import Errors
```bash
pip install -r requirements_full.txt
```

#### tkinter Missing (Linux)
```bash
sudo apt-get install python3-tk
```

#### PyInstaller Build Fails
- Check all dependencies installed
- Try building with `--debug` flag
- Check antivirus software

#### Web App Port Conflicts
- Change port in `web_app.py`
- Use different port: `flask run --port 5001`

#### Docker Issues
- Check Docker daemon running
- Verify port not in use
- Check firewall settings

---

## 📊 Performance Comparison

| Version | Startup Time | Memory Usage | Features | Distribution |
|---------|--------------|--------------|----------|--------------|
| Desktop GUI | Fast | Medium | Full | Python Required |
| Web App | Medium | Low | Core | Browser Required |
| Standalone | Medium | High | Full | Self-contained |
| Docker | Slow | Medium | Core | Container Required |

---

## 🔄 Migration Guide

### From Desktop to Web
1. Export your data from desktop version
2. Import data in web interface
3. Features are mostly compatible

### From Web to Desktop
1. Copy peak data from web interface
2. Paste into desktop version
3. Use advanced features as needed

---

## 📞 Support

- Check `README.md` for general usage
- See `ENHANCED_FEATURES_SUMMARY.md` for features
- Check console output for error messages
- Ensure Python 3.8+ is installed
