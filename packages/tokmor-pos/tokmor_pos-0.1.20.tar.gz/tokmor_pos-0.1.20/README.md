### tokmor-pos (TokMor POS = EAR)

`tokmor-pos` is the **add-on package** that provides **TokMor POS = ParSon axes (P/A/R/S/O/N)** and a derived **EAR hint (E/A/R)**.

Important: this is **not linguistic POS**. We allow **blank** (abstain) on uncertain tokens.

TokMor POS (EAR):
- **E**: existence-ish (high confidence)
- **R**: relation-ish (function words / punctuation)
- **A**: action-ish (high confidence)
- **blank**: untagged (allowed)

This is the same tagging style used in the dashboard (`dashboard/`).

### Install

```bash
pip install tokmor tokmor-pos
```

Optional (better E detection): install numeric deps for PPMIClassifierV2:

```bash
pip install tokmor-pos[ear]
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

### Legacy tools

This repo still contains POS8/role tooling for compatibility, but the current meaning of “TokMor POS” is **EAR**.
