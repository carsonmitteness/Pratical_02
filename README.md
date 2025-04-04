# Pratical_02

Main file you care about is practical_02.py run python practical_02.py

## Running the Script

The main file to execute is `practical_02.py`. Run it using:

```bash
python practical_02.py
```

## Command Line Arguments

### Required Arguments

When running the script, you must specify:

- **Vector Database** (e.g., `Redis`)
- **LLM Model** (e.g., `qwen2.5:latest`)
- **Embedding Model** (e.g., `nomic-embed-text:latest`)

Example usage:

```bash
python practical_02.py Redis qwen2.5:latest nomic-embed-text:latest
```

### Optional Flags

- **`-test`**: Runs the six questions for an experiment.
- **`-debug`**: Enables logging of files found through KNN.
- **Custom Fields**: You can modify fields via command-line arguments or by changing default values in the script.

## Performance Monitoring

- Timers and memory usage checks are performed after index creation.
