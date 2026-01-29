## Tank

Tool to load test LLM served in SGLang.

## Quickstart

This repository has already tokenized texts you can use them to run first load test:

```bash
CLEARML_CONFIG_FILE=clearml.conf python3 -m tank.cli \
  --input ./resources/example_tokenized_texts.jsonl \
  --rps-from 1 \
  --rps-to 32 \
  --duration-seconds 6 \
  --report-path results.bin \
  --constraint "e2e.avg@w=15s,s=1s<=3" \
  --constraint "err.ratio@w=1s,s=1s<=0.0" \
  --constraint "e2e.p90@w=15s,s=1s<=3" \
  --constraint "tpot.p90@w=15s,s=1s<=0.2" \
  --clearml-project llm-bench \
  --clearml-task sglang_streaming_run_3 \
  --tokenizer Qwen/Qwen2.5-0.5B-Instruct \
  --url http://178.154.254.47:8000/generate
```

For example:

![](./resources/demo.png)

## Documentation

For more details check documentation:

- [documentation/metrics.md](./documentation/metrics.md) describes how to interpret every dashboard in report.
- [documentation/guides.md](./documentation/guides.md) gives advices on how to perform solid test or compare tests and more.
- [documentation/semantics.md](./documentation/semantics.md) explains semantics of the load test under the hood.
- [documentation/development/md](./documentation/development.md) for developers.
