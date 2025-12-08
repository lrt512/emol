# Developer Setup Guide

This document helps you set up your development environment so you can run eMoL. Since eMoL runs entirely in Docker, your main goal is to get Docker, Make, and Git running.

## Linux (Debian, Ubuntu, etc.)

If you're using Fedora, you probably can figure out how to get there from here.

### 1. Install Docker Engine
Follow the official instructions to install Docker Engine:
- [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)

Ensure you also install the **Docker Compose plugin** (included in modern `docker-ce` installs).

### 2. Post-installation Steps
Manage Docker as a non-root user so you don't have to type `sudo` for every command:

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

You'll need to log out and back in for the change to be reflected permanently. You can continue to use `newgrp docker` in terminal windows until you do.

### 3. Install Tools

```bash
sudo apt update
sudo apt install -y make git
```

---

## Windows

**WSL2 is strongly recommended** for the best performance and compatibility with Linux-based tools. You could do a native Windows setup, but it will be fraught with peril and we really don't recommend that.

1.  **Install WSL2**:
    Open PowerShell as Administrator and run:
    ```powershell
    wsl --install
    ```
    This will install Ubuntu by default. Restart your computer when prompted.

2.  **Install Docker Desktop**:
    - Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
    - During installation, ensure the **WSL 2 backend** option is selected.
    - Open Docker Desktop settings -> **Resources** -> **WSL Integration**.
    - Enable integration for your Ubuntu distribution.

3.  **Install Tools in WSL**:
    Open your Ubuntu terminal and run:
    ```bash
    sudo apt update
    sudo apt install -y make git
    ```

## Mac

### 1. Install Package Manager (Homebrew)
If you haven't already, install Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Docker
The easiest method is **Docker Desktop for Mac**:
[Download Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)

*Alternative*: For a lightweight alternative, many developers prefer [OrbStack](https://orbstack.dev/):
```bash
brew install orbstack
```

### 3. Install Tools

```bash
brew install make git
```
Note: macOS comes with a version of Make, but Homebrew can provide a newer one if needed. The system default usually works fine for this project.

---

## SSH Keys

You will likely need an SSH key to authenticate with GitHub and to access remote servers.

See our **[SSH Guide](SSH.md)** for instructions on generating keys and connecting to the eMoL server.

---

## Verification

Once set up, verify your environment by running these commands in your terminal:

```bash
docker --version
# Should output Docker version 20.10+

docker compose version
# Should output Docker Compose version v2+

make --version
# Should output GNU Make version

git --version
# Should output git version
```

## Next Steps

Now you are ready to start! Go back to the [Development Guide](DEVELOPMENT.md) to clone the repo and run `make bootstrap`.
