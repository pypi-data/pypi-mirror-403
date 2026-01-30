<!-- PACKAGE file - intended to be shown when a user browses the package in a registry, incuding PyPI. Content is focused on what a _consumer_ of the application might want to know. -->

# Kwark

## Tap into AI brilliance from a simple shell command

The tool currently has five commands:
- `doc`: Summarizes the conclusions from a discussion or thread for inclusion in technical documentation
- `branch`: Generates git branch names from input text
- `commit`: Generates git commit messages from diff output
- `chat`: Simple chat interface to interact with AI
- `models`: Lists available Anthropic AI models

All commands use the Anthropic API and require an API key.

## Usage (MacOS)

The `doc` command processes text from standard input and returns a concise summary suitable for technical documentation. It extracts key observations and conclusions from discussions, emails, or notes.

```bash
pbpaste | kwark doc | pbcopy
```

The `branch` command generates a git branch name from input text. It requires input text and produces a concise, hyphen-separated branch name suitable for git.

```bash
echo "Add ability for users to export their transaction history to PDF for quarterly tax reporting" | kwark branch

# Output example: 20250113-export-transaction-history
```

You can use it to create a new branch directly:

```bash
git checkout -b $(echo "Implement role-based access controls for admin dashboard" | kwark branch)
```

**Note:** The branch command requires input text. If no input is provided, it will return an error.

The `commit` command generates a concise, descriptive commit message from git diff output. If there are no changes in the diff, it uses a dot as the commit message.

```bash
git diff | kwark commit

# Output example: Add user authentication feature

# Generate commit message from staged changes (more common)
git diff --staged | kwark commit
# Output: Fix validation bug in user registration
```

You can use it to create a commit directly:

```bash
# Stage your changes first, then commit with AI-generated message
git add .
git commit -m "$(git diff --staged | kwark commit)"
```

The `chat` command provides an interactive interface to have conversations with AI. It maintains conversation history and allows for back-and-forth dialogue. You can provide an initial message via standard input, or start with an empty chat session.

```bash
# Start interactive chat with an initial message
echo "What is the capital of France?" | kwark chat
# This will display the AI's response and then prompt for continued conversation
# Example output:
# The capital of France is Paris.
# 
# You: What's the population?
# Assistant: Paris has a population of approximately 2.1 million...

# Start interactive chat without initial message
kwark chat
# This will start directly in chat mode
# You: Hello, how are you?
# Assistant: I'm doing well, thank you! How can I help you today?
```

In chat mode, type your messages and the AI will respond while maintaining conversation context. The conversation continues until you type `quit`, `exit`, or `bye` to end the session, or use Ctrl+C to interrupt.

The `models` command lists all available Anthropic AI models that can be used with the other commands. The output is formatted as YAML and shows the model ID, display name, and creation date for each available model.

```bash
kwark models
# Output:
# - created_at: '2024-10-22'
#   display_name: Claude 3.5 Sonnet
#   id: claude-3-5-sonnet-20241022
# - created_at: '2024-03-07'
#   display_name: Claude 3 Haiku
#   id: claude-3-haiku-20240307  
# - created_at: '2024-02-29'
#   display_name: Claude 3 Opus
#   id: claude-3-opus-20240229
```

**Note:** Kwark currently uses Claude 4.5 Haiku by default. The models command shows which models are available through your Anthropic API key, but model selection is not yet configurable in Kwark.

(Note `pbcopy` and `pbpaste` are MacOS-specific commands.)

## Quick installation (MacOS)

If you don't already have `pipx`:

```bash
brew install pipx
```

Then install with `pipx`:

```bash
pipx install kwark
```

## Authentication and configuration

Kwark uses Claude 4.5 Haiku through the Antropic API, and requires an API key.

There are three options for providing the API key to Kwark, in order of precedence:

1. **Command line option** (highest precedence): Provide the API key as a `--api-key` option to any kwark command (e.g., `kwark doc --api-key YOUR_KEY` or `kwark chat --api-key YOUR_KEY`)
2. **Configuration file**: Provide the API key in a configuration file using the [WizLib ConfigHandler](https://wizlib.steamwiz.io/api/config-handler) protocol
3. **Environment variable** (lowest precedence): Set the default `ANTHROPIC_API_KEY` environment variable before running the `kwark` command

The command line option takes precedence over both the configuration file and environment variable. If no command line option is provided, the configuration file is checked. If neither is available, the environment variable is used as a fallback.

We recommend storing the key in a password manager such as 1Password, then using a config file to retrieve the key at runtime instead of storing the key itself in a file. For example, create a file at `~/.kwark.yml` with the following contents:

```yaml
kwark:
  api:
    anthropic:
      key: $(op read "op://Private/Anthropic/api-key")
```

<br/>

---

<br/>

<a href="https://www.flaticon.com/free-icons/particles">Particles icon by Freepik-Flaticon</a>
