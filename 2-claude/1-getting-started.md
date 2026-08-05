# Getting Started with Claude Code

###  Environment
I have installed claude code directly in a VM.  
I am using VmWare(on Windows), and used an Ubuntu Desktop on it, and that's where the installation went to.  

### Installaion

The recommended method today is Anthropic's native installer — no Node.js dependency at all 
(Linux):
```
curl -fsSL https://claude.ai/install.sh | bash
```

Verify details about the installation using the command:
```
claude doctor
```
Here's the output I got:
```
yuval@comp> curl -fsSL https://claude.ai/install.sh | bash
Setting up Claude Code...

✔ Claude Code successfully installed!

  Version: 2.1.207

  Location: ~/.local/bin/claude


  Next: Run claude --help to get started

✅ Installation complete!

yuval@comp>
```

### Login

- Run claude in your terminal. 
- On first use it prompts you to choose a login method: 
  - "Claude account with subscription" (Pro, Max, Team, or Enterprise)  
  or
  - "Anthropic Console account" (API usage billing). 
  For Pro, choose the first. 
- A browser tab opens:
sign in with your Claude account credentials. 
If you're already logged in at claude.ai, the authorization is nearly instant. 
- Return to your terminal, and Claude Code confirms the connection

