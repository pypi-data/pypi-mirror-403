# nanobox-python

Python bindings for [nanobox](../../) - lightweight cross-platform sandbox.

## Install

```bash
pip install nanobox
```

## Usage

```python
from nanobox import Sandbox, Permission, MB

sandbox = (Sandbox.builder()
    .working_dir("/tmp")
    .memory_limit(512 * MB)
    .wall_time_limit(30.0)
    .build())

result = sandbox.run("python3", ["-c", "print('hello')"])
print(result.stdout)  # hello
print(result.success())  # True
```

## Presets

```python
Sandbox.code_judge("/code").build()        # Strict limits for judging
Sandbox.agent_executor("/workspace").build()  # AI agent execution
Sandbox.data_analysis("/in", "/out").build()  # Data processing
```

## Build

```bash
pip install maturin
maturin develop
```

## License

MIT
