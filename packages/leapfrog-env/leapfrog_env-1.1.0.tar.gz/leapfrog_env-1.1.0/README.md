# Leapfrog

A CLI tool for switching between environment configurations. Stop manually editing `.env` files.

## The Problem

You know the drill: you're switching between dev, staging, and production. Every time you need to manually update your `.env` file with different database URLs, API keys, and port numbers. You forget to change one value and waste 20 minutes debugging why your local app is hitting the production database.

I got tired of this, so I built Leapfrog.

## Installation

```bash
pip install leapfrog-env
```

Requires Python 3.7+. Works on Mac, Linux, and Windows.

## Usage

Save your current `.env` as an environment:

```bash
leapfrog hatch production --from-current
```

Create a few more:

```bash
leapfrog hatch staging --from-current
leapfrog hatch development --from-current
```

Switch between them:

```bash
leapfrog leap development
leapfrog leap production
```

See what you have:

```bash
leapfrog pond
```

That's it. Your `.env` file gets updated, and Leapfrog keeps a backup of what was there before.

## Commands

- `hatch <name>` - Save current `.env` as a named environment
  - `--from-current` - Use your current `.env` file
  - `--force` - Overwrite if it already exists
  - `--description "..."` - Add a description

- `leap <name>` - Switch to a saved environment

- `pond` - List all your saved environments

- `croak` - Validate your current `.env` file

- `prune <name>` - Delete an environment you don't need anymore

## How it works

Leapfrog stores your environment configurations locally (in `~/Library/Application Support/leapfrog/` on Mac, similar locations on other platforms). When you switch environments, it backs up your current `.env` and writes the new one.

Everything stays on your machine. No cloud sync, no accounts, no tracking.

## Why I built this

At my company we have like 8 different environments: dev, dev1, dev2, dev3, qa, qa1, qa2, staging. Each one has different database credentials, different MongoDB connection strings, different API endpoints. New developers would constantly forget to update everything and spend hours debugging.

I got tired of seeing the same mistakes over and over, so I built this. Now it takes one command to switch between any environment.

## Tech stack compatibility

Works with anything that uses `.env` files:
- Node.js / Express / Next.js / React
- Python / Django / Flask
- Ruby / Rails
- Go
- PHP / Laravel
- Java / Spring Boot
- Whatever else you're using

## A few nice things

- Automatically backs up your current `.env` before switching
- Validates environment files and tells you if something's wrong
- Groups variables by type (database, API, security, etc.) for readability
- Hides sensitive values in output
- Suggests similar names if you typo an environment name
- Shows you which environments you've used recently

## Contributing

Found a bug? Have a feature idea? Open an issue or PR. I'm pretty responsive.

## License

MIT - do whatever you want with it.

---

Built by someone who got tired of manually editing environment files.