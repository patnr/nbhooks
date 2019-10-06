# nbhooks

This repository provides scripts which help with keeping
Jupyter notebooks under revision control in git.
They are meant to be used with the
[pre-commit](https://pre-commit.com) framework - see their website
for information about usage and configuration.


Here is a sample config to include in the `.pre-commit-config.yaml` file:

```yaml
- repo: https://gitlab.com/iamlikeme/nbhooks
  rev: 1.0.0  # Set to the most recent version
  hooks:
  - id: nb-ensure-clean
    args: [--meta, ExecuteTime]  # Optional blacklist of metadata keys (you can use regex)
```

If you want to use the scripts directly (i.e. without the framework), do:

```bash
git clone https://gitlab.com/iamlikeme/nbhooks
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
