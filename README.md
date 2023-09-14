# nbhooks

Help keeping Jupyter notebooks of [DA-tutorials](https://github.com/nansencenter/DA-tutorials)
under revision control in git.
Use with the [pre-commit](https://pre-commit.com) framework
by put this in your `.pre-commit-config.yaml` file

```yaml
- repo: https://github.com/patricknraanes/nbhooks.git
  rev: X.Y.Z  # Use `pre-commit autoupdate --bleeding-edge` to set to most recent version
  hooks:
  - id: nb-ensure-clean
    args: [--meta, pin_output]  # Optional WHITELIST of metadata keys (you can use regex)
```

## Hook: nb-ensure-clean

Use this hook to prevent committing "dirty" notebooks, i.e. notebooks which contain:

* outputs
* execution counts
* blacklisted metadata keys (you have to define the blacklist, see sample config)

## Changes since fork

Since the fork from [here](https://gitlab.com/iamlikeme/nbhooks),

* the code has been restructured.
* it checks for uncommented `show_answer` occurrences.
* it automatically changes files to fix issues.

## Development

If you want to use the scripts without the pre-commit framework, do:

```bash
git clone https://github.com/patricknraanes/nbhooks.git
cd nbhooks

# For simple use:
pip install .
nb-ensure-clean --help

# For development purposes, try `pip install -e`, or:
cd /path/to/my_project
pre-commit try-repo path/to/nbhooks nb-ensure-clean --verbose --all-files
```
