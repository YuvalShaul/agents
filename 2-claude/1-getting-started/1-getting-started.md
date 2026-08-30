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

Run `claude` in your terminal. On first use it prompts you to choose a login
method — pick whichever matches how you (or your organization) pays for
Claude:

```
Select login method:
❯ Claude account with subscription   Pro, Max, Team, or Enterprise
  Anthropic Console account          API usage billing
  3rd-party platform                 Amazon Bedrock, Microsoft Foundry, or Vertex AI
```

- **Claude account with subscription** — what I use (a Pro plan). Choose
  this if you have a Pro, Max, Team, or Enterprise subscription and want
  usage covered by that plan. A browser tab opens; sign in with your
  claude.ai account. If you're already logged in at claude.ai, the
  authorization is nearly instant.
- **Anthropic Console account** — pay-as-you-go by API token usage instead
  of a flat subscription. Choose this if you manage billing through
  [console.anthropic.com](https://console.anthropic.com) — you'll need an
  API key from there, which the browser step links to your terminal
  session.
- **3rd-party platform** — for organizations that already route Claude
  traffic through Amazon Bedrock, Microsoft Foundry, or Google Vertex AI.
  This asks for your cloud provider's credentials instead of an Anthropic
  login, and billing goes through that cloud account. Only relevant if your
  org has explicitly set this up — most students won't need it.

Whichever you pick, return to the terminal after the browser step and
Claude Code confirms the connection.

**Non-interactive alternative**: if you're on a Console-billed API key, you
can skip the prompt entirely by setting `ANTHROPIC_API_KEY` in your
environment before running `claude` — handy for CI or scripting.

Once logged in, `/logout` ends the session and clears stored credentials,
and `/login` lets you sign in again or switch methods (e.g. after upgrading
a subscription plan).

