### tokmor-pos (TokMor POS = ParSon axes + EAR hint)

`tokmor-pos` is the **add-on package** that provides **TokMor POS = ParSon axes (P/A/R/S/O/N)** and a derived **EAR hint (E/A/R + blank allowed)**.

Important: this is **not linguistic POS**. We allow **blank** (abstain) on uncertain tokens.

EAR hint (E/A/R):
- **E**: existence-ish (high confidence)
- **R**: relation-ish (function words / punctuation)
- **A**: action-ish (high confidence)
- **blank**: untagged (allowed)

This is the same tagging style used in the dashboard (`dashboard/`).

### Install

```bash
pip install tokmor tokmor-pos
```

---

### CLI (EAR)

```bash
tokmor-pos ear --lang en --text "Mariah Carey's first studio album"
```

### CLI (ParSon axes → EAR hint)

If WikiParSon mini data is installed, you can get P/A/R/S/O/N axes and the derived EAR hint:

```bash
tokmor-pos axes --lang en --text "This is my kingdom come"
```

### Install WikiParSon mini (data)

The ParSon mini “profiles” are large and are **not bundled** in the PyPI wheel.
Install them into `~/parson_final/wikiparson_mini/`:

```bash
tokmor-pos install-parson-mini --src /path/to/wikiparson_mini_all323_2026.01.tar.gz
```

You can download the bundle from the GitHub Release assets (tokmor-pos-v0.1.20 or later):
- [tokmor-pos releases](https://github.com/tokmorlab/tokmor/releases)

### Legacy tools

This package still contains POS8/role tooling for compatibility, but the current meaning of “TokMor POS” in this project is **ParSon axes + derived EAR hint**.

To enable legacy micro-CRF tooling:

```bash
pip install tokmor-pos[legacy]
```
