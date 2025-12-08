# SSH Guide

This guide covers generating SSH keys and connecting to remote servers, specifically the eMoL Lightsail instance.

## 1. Generating SSH Keys

You need an SSH key pair to authenticate with GitHub and remote servers without using passwords.

### Check for existing keys
Open your terminal and run:
```bash
ls -al ~/.ssh
```
If you see `id_ed25519` or `id_rsa`, you already have keys. It is often good practice to generate a new key for a new project or machine.

### Generate a new key
We recommend the modern Ed25519 algorithm:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```
*   Press Enter to accept the default file location (or specify a new name if managing multiple keys).
*   You can optionally set a passphrase for extra security (recommended).

### Add to GitHub
Display your public key:
```bash
cat ~/.ssh/id_ed25519.pub
```
Copy the output (starts with `ssh-ed25519`) and add it to your GitHub account settings under **SSH and GPG keys**.

---

## 2. Connecting to Linux Servers

The standard command to connect to a remote Linux server is:

```bash
ssh username@hostname_or_ip
```

If you need to use a specific private key file (like a `.pem` file provided by AWS):

```bash
ssh -i /path/to/private-key.pem username@hostname_or_ip
```

### Permissions Error?
If you get a "Permissions are too open" error for your key file, run:
```bash
chmod 400 /path/to/private-key.pem
```

---

## 3. Connecting to eMoL (Lightsail)

The eMoL application runs on an AWS Lightsail instance running Ubuntu.

### Prerequisites
1.  **IP Address**: Get the static IP address of the instance from the Lightsail console or the project administrator.
2.  **SSH Key**: You need the private key (`.pem` file) that was associated with the instance when it was created, or your public key must have been added to `~/.ssh/authorized_keys` on the server.

### Connection Command

The default user for Ubuntu Lightsail instances is `ubuntu`.

```bash
ssh -i ~/.ssh/LightsailDefaultKey-ca-central-1.pem ubuntu@<ip-address>
```

### Setting up an Alias (Optional)
To avoid typing the long command every time, add an entry to your `~/.ssh/config` file:

```text
Host emol
    HostName <ip-address>
    User ubuntu
    IdentityFile ~/.ssh/LightsailDefaultKey-ca-central-1.pem
```

Now you can simply run:
```bash
ssh emol
```

