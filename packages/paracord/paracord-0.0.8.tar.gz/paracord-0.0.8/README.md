# Paracord CLI

A modern, fast CLI tool that wraps copier, uv, and rav into a unified developer experience for Paracord projects.

## Installation

```bash
uv tool install paracord
```

Or run directly without installing:

```bash
uvx paracord init my-project
```

## Usage

### Create a new project

```bash
paracord init my-project
# or
pc init my-project
```

### Run tasks

Inside a Paracord project:

```bash
# List available tasks
paracord run

# Run a specific task
paracord run dev
```

### Update from template

```bash
paracord update
```

### Check for updates

```bash
paracord check
```

## Commands

| Command | Description |
|---------|-------------|
| `paracord init [project-name]` | Create a new Paracord project |
| `paracord run [task]` | Run a rav task (or list tasks if none specified) |
| `paracord update` | Update project from upstream template |
| `paracord check` | Check for template updates |

## Aliases

Both `paracord` and `pc` are available as CLI commands.

## License

MIT
