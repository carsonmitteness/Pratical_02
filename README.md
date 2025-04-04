# Pratical_02

First you need to install the required packages:

```bash
pip install -r requirements.txt
```

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
- **`-pre`**: Enables preprocessing to remove whitespace and stop words from the data set
- **Custom Fields**: You can modify fields via command-line arguments or by changing default values in the script.

These include:

- **`-p`**: Port Number
- **`-chunk`**: Chunk Sizes
- **`-o`**: Overlap

Overall can run from the command line something like this:

```bash
python practical_02.py -test -chunk 1000 -o 100 Redis qwen2.5:latest all-minilm:latest
```

## Performance Monitoring

- Timers and memory usage checks are performed after index creation.
