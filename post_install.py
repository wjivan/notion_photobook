#!/usr/bin/env python3
"""
Post-installation script for Notion Photobook Generator.

This script helps users configure their PATH after installation.
"""

import os
import sys
import site
from pathlib import Path


def get_script_location():
    """Get the location where the photobookgen script was installed."""
    user_site = site.getusersitepackages()
    if user_site:
        script_dir = Path(user_site).parent / "bin"
        if (script_dir / "photobookgen").exists():
            return script_dir
    return None


def get_shell_config_file():
    """Get the appropriate shell config file for the current user."""
    home = Path.home()
    
    # Check which shell is being used
    shell = os.environ.get('SHELL', '')
    
    if 'zsh' in shell:
        return home / '.zshrc'
    elif 'bash' in shell:
        return home / '.bashrc'
    else:
        # Default to .zshrc on macOS, .bashrc on Linux
        if sys.platform == 'darwin':
            return home / '.zshrc'
        else:
            return home / '.bashrc'


def add_to_path(script_dir):
    """Add the script directory to PATH in the shell config file."""
    config_file = get_shell_config_file()
    export_line = f'export PATH="{script_dir}:$PATH"'
    
    # Check if the line already exists
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
            if export_line in content:
                print(f"✅ PATH already configured in {config_file}")
                return True
    
    # Add the export line
    try:
        with open(config_file, 'a') as f:
            f.write(f'\n# Added by Notion Photobook Generator\n{export_line}\n')
        
        print(f"✅ Added to PATH in {config_file}")
        print(f"   Run 'source {config_file}' or restart your terminal to apply changes")
        return True
    except Exception as e:
        print(f"❌ Failed to update {config_file}: {e}")
        return False


def main():
    """Main post-installation function."""
    print("🔧 Notion Photobook Generator - Post Installation Setup\n")
    
    script_dir = get_script_location()
    if not script_dir:
        print("❌ Could not find photobookgen script location")
        print("   Try reinstalling the package")
        return 1
    
    print(f"📍 Script location: {script_dir}")
    
    # Check if already in PATH
    import shutil
    if shutil.which("photobookgen"):
        print("✅ photobookgen is already available in your PATH")
        return 0
    
    print("\n📝 The photobookgen command is not in your PATH.")
    print("   Would you like to add it automatically? (y/n): ", end="")
    
    try:
        response = input().lower().strip()
        if response in ['y', 'yes']:
            if add_to_path(script_dir):
                print("\n🎉 Setup complete! You can now use 'photobookgen' from anywhere.")
                print("   If it doesn't work immediately, restart your terminal.")
            else:
                print("\n⚠️  Automatic setup failed. Please add manually:")
                print(f"   export PATH=\"{script_dir}:$PATH\"")
        else:
            print("\n📋 Manual setup instructions:")
            print(f"   Add this line to your shell config file:")
            print(f"   export PATH=\"{script_dir}:$PATH\"")
            print(f"   Then restart your terminal or run 'source ~/.zshrc'")
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 