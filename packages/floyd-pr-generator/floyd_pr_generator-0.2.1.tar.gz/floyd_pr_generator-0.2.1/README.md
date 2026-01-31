# Floyd - AI-Powered Pull Request Generator

Floyd is a command-line tool that leverages Claude AI to automatically generate high-quality pull request titles and descriptions based on your git changes. It analyzes your commits, diffs, and file changes to create professional PRs following conventional commit standards.

## Features

- 🤖 **AI-Powered Analysis**: Uses Claude to analyze your code changes and generate comprehensive PR descriptions
- 📝 **Conventional Commits**: Automatically formats PR titles following conventional commit standards (feat:, fix:, docs:, etc.)
- 🎨 **Beautiful CLI**: Rich, colorful terminal interface with gradient ASCII art
- ♻️ **Iterative Refinement**: Refine generated PRs with natural language feedback
- ⚙️ **Configurable**: Customize AI behavior with custom instructions and diff size limits
- 🔍 **Smart Context**: Analyzes commit history, file stats, and diffs for accurate descriptions
- 🚀 **GitHub Integration**: Seamlessly creates PRs via GitHub CLI

## Prerequisites

- Python 3.14 or higher
- Git
- [GitHub CLI (gh)](https://cli.github.com/) - for creating pull requests
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code/cli) - for AI generation

## Installation

Install Floyd from PyPI using pip:

```bash
pip install floyd-pr-generator
```

Verify installation:
```bash
floyd --help
```

## Configuration

Floyd can be configured using a TOML configuration file. The configuration file should be placed at:

- **Linux/macOS**: `~/.config/floyd.toml`
- **Windows**: `C:\AppData\Roaming\floyd\floyd.toml`

### Configuration Options

Create a `floyd.toml` file with the following structure:

```toml
[ai]
# Maximum character limit for git diffs (prevents token limit issues)
# Set to -1 for no limit
diff_limit = 50000

# Custom instructions to guide the AI's PR generation
# This will be appended to the AI prompt
instructions = """
- Focus on business impact in the description
- Include any breaking changes at the top
- Mention related ticket numbers if present in commits
- Keep descriptions concise but informative
"""
```

### Configuration Parameters

#### `diff_limit` (integer)
- **Purpose**: Limits the size of git diffs sent to Claude to prevent token limit issues
- **Default**: `-1` (no limit)
- **Recommended**: `50000` for most projects
- **Example**: `diff_limit = 50000`

#### `instructions` (string)
- **Purpose**: Provide custom guidance to Claude for generating PRs
- **Format**: Multi-line string
- **Use cases**:
  - Enforce team-specific PR conventions
  - Highlight certain types of changes
  - Include specific formatting requirements
  - Add context about your project's workflow

### Example Configurations

#### Minimal Configuration
```toml
[ai]
diff_limit = 50000
```

#### Comprehensive Configuration
```toml
[ai]
diff_limit = 50000
instructions = """
PR Description Guidelines:
- Start with a brief summary of what changed and why
- List breaking changes first with ⚠️ emoji
- Group related changes by feature area
- Include ticket references (e.g., JIRA-123)
- Mention any migration steps required
- Keep technical details but make them accessible
- Add testing instructions if relevant
"""
```

#### Team-Specific Configuration
```toml
[ai]
diff_limit = 75000
instructions = """
Team Standards:
- Follow our internal PR template structure
- Highlight security implications
- Mention performance impacts
- Reference design docs when applicable
- Tag relevant team members in description
- Include rollback plan for infrastructure changes
"""
```

## Usage

### Basic Usage

Navigate to your git repository and run:

```bash
floyd <target-branch>
```

Example:
```bash
floyd main
```

This will:
1. Fetch the diff between your current branch and the target branch
2. Analyze recent commits and file changes
3. Generate a PR title and description using Claude
4. Display the draft for review
5. Offer options to create, refine, or cancel

### Workflow

1. **Review Generated Draft**: Floyd displays the AI-generated PR title and body in a formatted panel

2. **Choose Action**:
   - **Create Pull Request**: Immediately create the PR on GitHub
   - **Refine Draft**: Provide feedback in natural language to improve the draft
   - **Cancel**: Exit without creating a PR

3. **Iterative Refinement** (optional):
   - If you choose "Refine Draft", you can provide feedback like:
     - "Make the description more technical"
     - "Add more details about the authentication changes"
     - "Keep it shorter and more concise"
     - "Emphasize the performance improvements"

### Example Session

```bash
$ floyd main

 ███████████ █████          ███████    █████ █████ ██████████  
░░███░░░░░░█░░███         ███░░░░░███ ░░███ ░░███ ░░███░░░░███ 
 ░███   █ ░  ░███        ███     ░░███ ░░███ ███   ░███   ░░███
 ░███████    ░███       ░███      ░███  ░░█████    ░███    ░███
 ░███░░░█    ░███       ░███      ░███   ░░███     ░███    ░███
 ░███  ░     ░███      █░░███     ███     ░███     ░███    ███ 
 █████       ███████████ ░░░███████░      █████    ██████████  
░░░░░       ░░░░░░░░░░░    ░░░░░░░       ░░░░░    ░░░░░░░░░░   

'diff_limit' loaded with value: 50000
'instructions' loaded with value: Focus on business impact in...
Successfully fetched branch diff
Successfully generated a PR.

╭─ Draft Pull Request ───────────────────────────────────────────────────╮
│ Title: feat: add user authentication system                            │
│                                                                        │
│ Body:                                                                  │
│ This PR introduces a comprehensive user authentication system with:    │
│ - JWT-based token authentication                                       │
│ - Password hashing with bcrypt                                         │
│ - Session management                                                   │
│ - Login/logout endpoints                                               │
│                                                                        │
│ Breaking Changes:                                                      │
│ - API endpoints now require authentication headers                     │
│ - Database schema updated with users table                             │
╰────────────────────────────────────────────────────────────────────────╯

? What would you like to do?
  ❯ Create Pull Request
    Refine Draft
    Cancel
```

## How It Works

1. **Git Analysis**: Floyd examines your current branch against the target branch to gather:
   - Commit history
   - File change statistics
   - Detailed code diffs

2. **AI Processing**: The information is sent to Claude with:
   - Your custom instructions (if configured)
   - Context about the branch and commits
   - Conventional commit formatting requirements

3. **PR Generation**: Claude generates:
   - A conventional commit-formatted title
   - A comprehensive description of changes
   - Context-aware content based on commit messages

4. **Interactive Review**: You can:
   - Accept and create the PR immediately
   - Request refinements with natural language
   - Cancel if needed

## Project Structure

```
floyd/
├── __init__.py          # Package initialization
├── cli.py              # Command-line interface entry point
├── git.py              # Git operations (diff, commits, branches)
├── models.py           # AI model interaction and response parsing
├── ui.py               # Rich terminal UI components
├── utils.py            # Utilities (config loading, command execution)
└── workflow.py         # Main PR generation workflow
```

## Error Handling

Floyd handles various error scenarios gracefully:

- **Not a Git Repository**: Validates you're in a git repository before proceeding
- **Branch Doesn't Exist**: Checks if the target branch exists on origin
- **PR Already Exists**: Prevents duplicate PRs for the same branch combination
- **Claude CLI Not Available**: Alerts if the Claude CLI isn't installed or accessible
- **Parsing Errors**: Handles unexpected AI response formats

## Dependencies

- **rich**: Beautiful terminal formatting and UI components
- **questionary**: Interactive CLI prompts
- **setuptools**: Package management
- **pathlib**: Cross-platform path handling

## Troubleshooting

### "This directory is not a git repository"
Make sure you're running Floyd from within a git repository.

### "The 'claude' command failed to execute"
Ensure the Claude CLI is installed and available in your PATH. Visit [Claude CLI documentation](https://docs.anthropic.com/en/docs/claude-code/cli) for installation instructions.

### "The branch 'X' does not exist on origin"
The target branch must exist on the remote repository. Push your target branch first or use a different branch name.

### Configuration not loading
Verify your config file is at the correct location:
- Linux/macOS: `~/.config/floyd.toml`
- Windows: `C:\AppData\Roaming\floyd\floyd.toml`

Check the file has correct TOML syntax.

## Contributing

Contributions are welcome! Please feel free to submit issues, fork the repository, and create pull requests.

## Acknowledgments

- Built with [Anthropic's Claude AI](https://www.anthropic.com/claude)
- Uses [GitHub CLI](https://cli.github.com/) for PR creation
- Terminal UI powered by [Rich](https://github.com/Textualize/rich)

---

**Note**: Floyd requires the Claude CLI and GitHub CLI to be properly configured on your system. Make sure you're authenticated with both services before using Floyd.
