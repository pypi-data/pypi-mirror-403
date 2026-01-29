### tokmor-pos (optional add-on)

This is a **separate** package that provides:
- **POS8 structural hints** (pattern-based, abstaining)
- optional **Micro-CRF boundary smoothing** (BIO only; boundary cleanup, not POS)

It is **not** a linguistic POS tagger.

### Out-of-the-box quality (no setup)

`tokmor-pos` ships with a **built-in full lexicon6 pack + transitions** inside the wheel.
So POS tagging is usable immediately **without** configuring `TOKMORPOS_DATA_DIR`.

- **Download size (pip)**: ~**33MB** (compressed)
- **Unpacked lexicon6**: ~**250MB** on disk

On the UD treebanks available in this repo (10 languages on disk), current POS8 accuracy is about:
- **~80.9% token accuracy**, **UNK=0%**

### Model-free POS hints: POS10-lite via deterministic morphology

If you want **no external POS model at all**, you can still get a useful coarse hint layer by using
TokMor's deterministic morphology/lexicon as evidence.

```python
from tokmor_pos.api import tag_pos10_lite

pos10 = tag_pos10_lite(text, lang="en")  # returns per-token tags in {N,P,V,A,J,R,F,Q,T,S,O} or "UNK"
```

### Install

```bash
pip install tokmor tokmor-pos
```

### Runtime assets (optional)

If you train Micro-CRF models, `tokmor-pos` can load them from:

- `micro_crf/{lang}_bio.pkl`

Point it via:

- `TOKMORPOS_DATA_DIR=/path/to/tokmorpos_snapshot` (preferred)

It will also look under `TOKMOR_DATA_DIR` if set.

### CLI

```bash
tokmor-pos pos8 --lang en --text "Apple announced new products."
```

Fill UNK tokens using TokMor extended dictionaries (if you have a data pack):

```bash
export TOKMOR_DATA_DIR=/path/to/tokmor_data_pack
tokmor-pos pos8 --lang es --extended-dict --text "muy bueno y muy malo en Madrid"
```

Reduce UNK (default) and optionally fill remaining UNK using lexicon6:

```bash
tokmor-pos pos8 --lang fr --lexicon6 --text "Nous avons visité Séoul le 2025-01-10."
```

If you want to preserve the original abstaining behavior (keep UNK), use:

```bash
tokmor-pos pos8 --lang fr --keep-unk --text "Nous avons visité Séoul le 2025-01-10."
```

Structure hint scores (deterministic, derived from POS8/Role4):

```bash
tokmor-pos hints --lang en --morph-fallback --text "Apple announced new products in Seoul."
```


