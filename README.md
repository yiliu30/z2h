# Agent Skills Hub

Custom agent skills and instruction files, packaged so the repo can be used directly with `npx skills add ...`.

## Repo Layout

```text
agent-skills-hub/
├── skills/                       # installable skills
├── instructions/                 # optional .instructions.md files
├── plugins/
│   └── agent-skills-hub-custom/  # plugin metadata for marketplace-style installs
├── .agents/plugins/marketplace.json
├── scripts/
│   ├── build-catalog.py
│   ├── export-plugin.py
│   ├── generate-vscode-settings.sh
│   └── install-skill.sh
└── catalog.json
```

## Install

Install all bundled skills from GitHub:

```bash
npx skills add <your-user>/agent-skills-hub
```

List what the repo exposes:

```bash
npx skills add <your-user>/agent-skills-hub --list
```

Install from a local checkout:

```bash
npx skills add .
```

## Local Commands

```bash
make help
make list
make catalog
make plugin
make refresh
```

| Command | Description |
|---------|-------------|
| `make list` | List bundled skills |
| `make install SKILL=<name> TARGET=<dir>` | Copy one skill into a target directory |
| `make catalog` | Rebuild `catalog.json` from `skills/` |
| `make plugin` | Rebuild plugin marketplace metadata |
| `make refresh` | Rebuild both catalog and plugin metadata |
| `make settings` | Generate VS Code settings snippets |

## VS Code

Generate a settings snippet:

```bash
make settings
```

Expected paths:

```jsonc
"chat.agentSkillsLocations": {
  "~/workspace/agent-skills-hub/skills": true
},
"chat.instructionsFilesLocations": {
  "~/workspace/agent-skills-hub/instructions": true
}
```

## Adding A Skill

1. Copy the template:

```bash
cp -r skills/example-skill skills/my-new-skill
```

2. Edit `skills/my-new-skill/SKILL.md`.
3. Run `make refresh`.

## Catalog

`catalog.json` is generated from `skills/` and records:

- skill name
- description
- repo-relative path
- whether the skill includes extra assets

## License

The repo is licensed under [MIT](LICENSE).
