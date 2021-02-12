# nbhooks

This repository provides scripts which help with keeping
the Jupyter notebooks of [DA-tutorials](https://github.com/nansencenter/DA-tutorials)
under revision control in git.
They are meant to be used with the
[pre-commit](https://pre-commit.com) framework - see their website
for information about usage and configuration.

Here is a sample config to include in the `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/patricknraanes/nbhooks.git
  rev: X.Y.Z  # Use `pre-commit autoupdate --bleeding-edge` to set to most recent version
  hooks:
  - id: nb-ensure-clean
    args: [--meta, pin_output]  # Optional WHITELIST of metadata keys (you can use regex)
```

If you want to use the scripts directly (i.e. without the framework), do:

```bash
git clone https://github.com/patricknraanes/nbhooks.git
cd nbhooks
pip install .

nb-ensure-clean --help
```

## Hooks

### nb-ensure-clean

Use this hook to prevent commiting "dirty" notebooks, i.e. notebooks which contain:

* outputs
* execution counts
* blacklisted metadata keys (you have to define the blacklist,
  see sample config)

### Changes since fork

Since the fork from [here](https://gitlab.com/iamlikeme/nbhooks),
the code has been restructured.
It now also checks for

* Uncommendted `show_answer` occurences.
* Ensure Colab stuff is not in master branch.

And it automatically changes the files to fix these issues.
