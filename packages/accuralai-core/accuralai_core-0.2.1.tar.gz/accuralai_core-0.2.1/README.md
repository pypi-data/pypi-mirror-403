# accuralai-core

`accuralai-core` is the orchestration nucleus for the AccuralAI open-source ecosystem. It provides an async pipeline that coordinates canonicalization, caching, routing, backend invocation, validation, and post-processing for local LLM text generation workflows.

This package exposes both a Python API and CLI surface while remaining transport-agnostic. Concrete functionality (canonicalizers, caches, routers, backends, validators) is supplied by sibling packages or third-party plugins via entry-point discovery.

## Quick start

Install with the canonicalizer plugin for a fully working local pipeline:

```bash
pip install accuralai-core accuralai-canonicalize
```

Generate completions via the CLI:

```bash
accuralai-core generate \
  --prompt " Summarize   this text.  " \
  --system-prompt "You are a precise assistant." \
  --tag demo --metadata topic=news --param temperature=0.3
```

The `accuralai-canonicalize` plugin normalizes the prompt, merges metadata defaults, and creates deterministic cache keys before the request is routed to the configured backend.

Add `accuralai-cache` to enable TTL-aware in-memory caching:

```bash
pip install accuralai-cache
```

With caching enabled, repeat invocations are served instantly until the configured TTL expires.

See `plan/accuralai-core-spec.md` for the full architectural specification guiding implementation.

## Interactive CLI

Launch the Codex-style REPL by invoking `accuralai` (or `accuralai-cli`) with no subcommand:

```bash
accuralai --config ~/.accuralai/core.toml
```

The shell remains active until `/exit`, and supports `/` commands for adjusting settings on the fly (`/help`, `/backend`, `/model`, `/meta`, `/history`, `/save`, `/tool ...`, etc.). Plain text input triggers pipeline runs using the current session defaults, and multi-line prompts are accepted by entering `"""` on an empty line. Tools can be listed via `/tool list`, executed manually with `/tool run ...`, and made available to the model for function calling via `/tool enable <name>`.
