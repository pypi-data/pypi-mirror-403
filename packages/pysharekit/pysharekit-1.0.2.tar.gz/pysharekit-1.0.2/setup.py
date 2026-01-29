"""
Setup configuration for pysharer package
Effortless screen sharing via browser - no installation required
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="pysharekit",
    version="1.0.2",
    
    # Author information
    author="Raghav Anthwal",
    author_email="raghavanthwal006@gmail.com",
    
    # Project description
    description="Effortless screen sharing via browser - no installation required on viewer devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Project URLs
    url="https://github.com/niterousnebula/sharer",
    project_urls={
    },
    
    # Package configuration
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    
    # Include additional files
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.7",
    
    # Dependencies
    install_requires=[
        "Flask>=2.0.0",
        "flask-socketio>=5.0.0",
        "python-socketio>=5.0.0",
        "mss>=6.0.0",
        "Pillow>=9.0.0",
        "qrcode[pil]>=7.0.0",
        "pyautogui>=0.9.53",
    ],
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "twine>=4.0.0",
            "build>=0.7.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    
    # Console scripts - command line entry points
    entry_points={
        "console_scripts": [
            "sharer=sharer.server:start_server",
        ],
    },
    
    # PyPI classifiers
    classifiers=[
        # Development status
        "Development Status :: 4 - Beta",
        
        # Intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Education",
        
        # Topic
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Desktop Environment",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Multimedia :: Graphics :: Capture :: Screen Capture",
        "Topic :: System :: Networking",
        
        # License
        "License :: OSI Approved :: MIT License",
        
        # Operating systems
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        
        # Programming language
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        
        # Framework
        "Framework :: Flask",
        
        # Environment
        "Environment :: Web Environment",
        "Environment :: Console",
        
        # Natural language
        "Natural Language :: English",
    ],
    
    # Keywords for PyPI search
    keywords=[
        "screen-sharing",
        "remote-control",
        "vnc",
        "presentation",
        "casting",
        "screenshare",
        "remote-desktop",
        "webrtc-alternative",
        "qr-code",
        "browser-based",
        "zero-install",
        "websocket",
        "real-time",
        "flask",
        "socket.io",
        "cross-platform",
        "smart-tv",
        "mobile-friendly",
        "touch-control",
    ],
    
    # Zip safe flag
    zip_safe=False,
    
    # Platform specification (any)
    platforms="any",
)