# Migration Guide: pypet v0.6.0 Parameter Syntax Update

## Overview

pypet v0.6.0 introduces a **breaking change** to the parameter placeholder syntax to improve shell compatibility and user experience.

### What Changed

**Old syntax (v0.5.x and earlier):**

```bash
pypet new "docker run {image} -p {port=8080} -e ENV={env=production}"
```

**New syntax (v0.6.0+):**

```bash
pypet new "docker run {{image}} -p {{port=8080}} -e ENV={{env=production}}"
```

## Why This Change?

The old `{param}` syntax conflicts with bash brace expansion, causing unexpected behavior. The new `{{param}}` syntax avoids these conflicts and aligns with common template syntax patterns.

## Migration Process

### Automatic Migration

When you upgrade to pypet v0.6.0, your existing snippets will be automatically migrated by the system. The first time you use pypet, it will:

1. Detect snippets using the old `{param}` syntax
2. Offer to migrate them to the new `{{param}}` syntax
3. Create a backup of your snippets before making changes

### Manual Migration

To manually migrate all your snippets:

```bash
pypet migrate
```

This command will:

- Show you all snippets using old syntax
- Ask for confirmation before making changes
- Create an automatic backup
- Migrate all snippets to the new syntax

### Backup and Recovery

Automatic backups are created before migration in `~/.config/pypet/backups/`:

```bash
# List available backups
ls -la ~/.config/pypet/backups/

# Restore from a backup if needed
cp ~/.config/pypet/backups/snippets_backup_YYYYMMDD_HHMMSS.toml ~/.config/pypet/snippets.toml
```

## Parameter Syntax Examples

### Simple Parameters (Required)

Old:

```bash
{name}
```

New:

```bash
{{name}}
```

### Parameters with Defaults

Old:

```bash
{port=8080}
```

New:

```bash
{{port=8080}}
```

### Mixed Usage

Old:

```bash
ssh {user=admin}@{host} -p {port=22}
```

New:

```bash
ssh {{user=admin}}@{{host}} -p {{port=22}}
```

## Adding Parameter Descriptions

With the new system, you can add descriptions to parameters during creation:

```bash
pypet new "docker run {{image}} -p {{port}}" --description "Run Docker container"
```

The system will then interactively prompt you to:

- Add descriptions for each parameter
- Set default values
- Confirm the parameter definitions

## Using Parameterized Snippets

### Execution with Values

Old and new syntax work the same way:

```bash
# Execute with parameter values
pypet exec my-docker -p port=3000 image=ubuntu

# Or interactively (with prompts)
pypet exec my-docker
```

### Shell Aliases

If you created shell aliases for your snippets, they will automatically work with the new syntax:

```bash
# After sourcing the aliases file
source ~/.config/pypet/aliases.sh

# Use the alias with parameters
my-docker port=3000 image=ubuntu
```

## Troubleshooting

### Snippet Not Working After Migration

If a snippet doesn't work after migration, you can:

1. Check the syntax:

   ```bash
   pypet show snippet-id
   ```

2. Manually edit the snippet:

   ```bash
   pypet edit snippet-id
   ```

3. Restore from backup if needed:

   ```bash
   cp ~/.config/pypet/backups/snippets_backup_YYYYMMDD_HHMMSS.toml ~/.config/pypet/snippets.toml
   ```

### Shell Aliases Not Working

If your shell aliases break after migration:

1. Regenerate aliases:

   ```bash
   pypet alias setup
   ```

2. Activate them:

   ```bash
   source ~/.config/pypet/aliases.sh
   ```

### Issues with Shell Expansion

If you see literal brace characters in your commands, this might be shell expansion:

Old problematic syntax:

```bash
echo "Processing {file}" # bash expands {file} if file exists!
```

New safe syntax:

```bash
echo "Processing {{file}}" # Never expanded by bash
```

## Backward Compatibility

- Reading old `{param}` syntax snippets: ✓ Fully supported
- Executing old syntax snippets: ✓ Works as before
- Automatic migration: ✓ Happens silently on first use
- Manual migration: ✓ Available via `pypet migrate`

## Getting Help

For migration issues or questions:

1. Check the help:

   ```bash
   pypet new --help
   pypet migrate --help
   ```

2. View your migration history:

   ```bash
   ls -l ~/.config/pypet/backups/
   ```

3. Report issues or ask for help:
   - GitHub Issues: <https://github.com/fabiandistler/pypet/issues>
   - Documentation: <https://github.com/fabiandistler/pypet#readme>
