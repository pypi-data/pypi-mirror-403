# dblpcli

CLI for DBLP, for humans and agents alike.

## Installation

```bash
pip install dblpcli
```

## Usage

### Search publications

```bash
dblpcli search "transformer attention"
dblpcli search "deep learning" --year 2020-2024 --limit 10
dblpcli search "author:Vaswani" --format json
```

### Get publication details

```bash
dblpcli pub conf/nips/VaswaniSPUJGKP17
dblpcli pub conf/nips/VaswaniSPUJGKP17 --format json
```

### Export BibTeX

```bash
dblpcli bibtex conf/nips/VaswaniSPUJGKP17
dblpcli bibtex conf/nips/VaswaniSPUJGKP17 --key vaswani2017attention
dblpcli bibtex conf/nips/VaswaniSPUJGKP17 journals/jmlr/KingmaB14 --output refs.bib
```

### Author commands

```bash
dblpcli author search "Geoffrey Hinton"
dblpcli author get h/GeoffreyEHinton
dblpcli author pubs h/GeoffreyEHinton --year 2020-2024
dblpcli author bibtex h/GeoffreyEHinton
```

### Venue commands

```bash
dblpcli venue search "NeurIPS"
dblpcli venue get conf/nips
dblpcli venue pubs conf/nips --year 2023
```

## Output Formats

All commands support the `--format` / `-f` flag:

- `table` (default) - Human-readable Rich table
- `json` - Structured JSON for agents/scripts
- `bibtex` - BibTeX entries

```bash
dblpcli search "transformers" --format json
dblpcli search "transformers" -f json
```

## License

MIT
