# cyberOffensive

**cyberOffensive** is a cross-platform, educational Python package that provides system-level utilities through a clean and beginner-friendly API. 

> ⚠️ **Important Disclaimer**  
> This project is designed for **cybersecurity learners, beginners, and pentesters** for educational and research purposes.    
> Use it **responsibly and ethically**.  
> You must only use this software on systems you own or have explicit permission to test.  
> The author is **not responsible for any illegal or malicious use** of this project.

---

## ⚙️ System-Level Feature Compatibility

Some functions in this package rely on low-level Windows APIs (e.g., input control and elevated operations). These features require administrator privileges and may be restricted by system security policies. On Windows 11, security controls are stricter than on Windows 10, so certain features may not function in Windows 11 or higher.

---

## Features

### Core (All Platforms)
- Network availability check  
- Platform detection (Windows / Linux / macOS)  
- Admin/root privilege detection  
- System information collection  
- Simple command execution helper  

### Linux & macOS
- Run background shell commands  

### Windows (Platform-specific features)
- Windows-specific helpers  
- System interaction utilities  

> Platform-specific functions are only available when running on the supported platform.

---

## Installation

### For Users (when published on PyPI)

```bash
pip install cyberOffensive
```

**Author:** Arpit Jaiswal (Echo Cipher)  
**GitHub:** https://github.com/Arp1it