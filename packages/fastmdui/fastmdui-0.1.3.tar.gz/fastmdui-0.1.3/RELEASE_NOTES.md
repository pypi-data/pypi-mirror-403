# fastMDUI v0.1.0 - Initial Release 🎉

We're excited to announce the first stable release of **fastMDUI** - Material Design UI components for FastHTML!

## 🎯 Overview

fastMDUI brings Google's Material Design 3 to FastHTML, providing a complete set of ready-to-use UI components with built-in theming, icons, and responsive design.

## ✨ Features

### Components (25+)
- **Form Components**: Button, TextField, Select, Checkbox, Radio, Switch, Slider
- **Layout Components**: Card, List, ListItem, Divider, Div
- **Navigation**: TopAppBar, NavigationBar, NavigationDrawer, Tab, TabPanel
- **Feedback**: Dialog, Snackbar, Tooltip, Badge, Progress
- **Display**: Icon, Avatar, Chip, Fab

### Theming
- 🌓 **Dark/Light Mode** - Built-in theme toggle with system preference detection
- 🎨 **Customizable Colors** - Easy primary color configuration
- 🔤 **Google Open Sans Font** - Professional typography by default
- 💾 **Persistent Preferences** - Theme choice saved in localStorage

### Icons
- 🎭 **2000+ Material Icons** - Multiple variants (outlined, filled, rounded, sharp)
- ⚡ **Easy Integration** - Simple icon attribute on components
- 🎨 **Customizable** - Support for custom icon styling

### Developer Experience
- 📦 **Zero Configuration** - Works immediately with sensible defaults
- 🎯 **Type-Safe** - Clear Python component APIs
- 📱 **Responsive** - Mobile-first design
- 📚 **Well Documented** - Comprehensive examples and guides
- 🧪 **Tested** - Extensive test coverage

## 📦 Installation
```bash
pip install fastmdui
```

## 🚀 Quick Start
```python
from fasthtml.common import FastHTML, serve
from fastmdui import MDUI, Button, Card

app = FastHTML(hdrs=MDUI.headers(font="open-sans"))

@app.get("/")
def home():
    return Card(
        title="Welcome to fastMDUI",
        content=Button("Get Started", variant="filled", icon="rocket_launch")
    )

serve()
```

## 📚 Documentation

- **GitHub Repository**: https://github.com/seekerquest/fastmdui
- **PyPI Package**: https://pypi.org/project/fastmdui/
- **Examples**: See `/examples` directory for demos

## 🙏 Acknowledgments

- **MDUI Team** - For the excellent Material Design implementation
- **FastHTML Team** - For the amazing Python web framework
- **Google Material Design** - For the design system and icons

## 🗺️ What's Next

Planned for future releases:
- Additional MDUI components
- Custom theme builder utility
- Component showcase website
- Video tutorials
- Performance optimizations

## 💬 Feedback

Found a bug? Have a feature request? Please [open an issue](https://github.com/seekerquest/fastmdui/issues)!

---

**Full Changelog**: https://github.com/seekerquest/fastmdui/commits/v0.1.0