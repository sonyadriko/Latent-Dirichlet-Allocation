# Indonesian NLP Preprocessing

Details of the text preprocessing pipeline applied to all crawled and manually entered documents before LDA training.

## Pipeline (in order)

| Step | Operation | Library |
|------|-----------|---------|
| 1 | Lowercase | Python built-in |
| 2 | Remove URLs, emails, numbers, punctuation | `re` |
| 3 | Tokenize | NLTK `word_tokenize` |
| 4 | Remove Indonesian stopwords | NLTK + custom set |
| 5 | Stem to root form | Sastrawi |
| 6 | Filter tokens with length ≤ 2 | Python built-in |

Source: `services/preprocessing.py` → `TextPreprocessor.preprocess_documents()`

---

## Step 2 — Cleaning Patterns

Removed via regex before tokenization:

- `http[s]?://\S+` — HTTP/HTTPS URLs
- `www\.\S+` — bare domain links
- `\b[\w.-]+@[\w.-]+\.\w+\b` — email addresses
- `\d+` — standalone numbers
- `[^\w\s]` — punctuation and special characters
- Multiple whitespace collapsed to single space

---

## Step 4 — Stopwords

The extended Indonesian stopword list combines **NLTK's Indonesian corpus** with a custom set of ~45 additional words:

**Articles / identifiers:** `si`, `sebuah`

**Particles / clitics:** `lah`, `kah`, `nya`, `mu`, `ku`, `pun`

**Personal pronouns:** `saya`, `kamu`, `anda`, `ia`, `dia`, `mereka`, `kami`, `kita`

**Prepositions:** `di`, `ke`, `dari`, `pada`, `untuk`, `dalam`, `dengan`, `oleh`, `setelah`, `sebelum`, `antara`, `hingga`, `sampai`, `selama`, `sejak`, `ketika`

**Conjunctions:** `dan`, `atau`, `yang`, `karena`, `jika`, `maka`, `namun`, `tetapi`, `sedangkan`, `sementara`, `agar`, `supaya`, `meski`, `meskipun`, `walaupun`, `bila`

**Modals / auxiliaries:** `akan`, `dapat`, `bisa`, `sudah`, `telah`, `ada`

**Other high-frequency words:** `adalah`, `sebagai`, `saat`, `lebih`, `hanya`, `seperti`, `serta`, `bahwa`, `kapan`, `mengapa`, `bagaimana`, `dimana`, `siapa`, `apa`

---

## Step 5 — Sastrawi Stemmer

[Sastrawi](https://github.com/har07/PySastrawi) is an Indonesian morphological stemmer. It reduces words to their root form following Indonesian affixation rules:

| Inflected | Stemmed |
|-----------|---------|
| `meningkatkan` | `tingkat` |
| `peningkatan` | `tingkat` |
| `diterbitkan` | `terbit` |
| `pemberitahuan` | `beritahu` |
| `mempertimbangkan` | `timbang` |

Sastrawi handles prefixes (`me-`, `pe-`, `di-`, `ter-`, `ber-`, `ke-`) and suffixes (`-kan`, `-an`, `-i`, `-lah`, `-kah`).

---

## NLTK Downloads Required

Run once at first setup:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
```

These are downloaded automatically in the Docker image.

---

## Gensim Dictionary Filtering

After tokenization and stemming, a Gensim **Dictionary** is built from all tokenized documents. Before training LDA:

```python
dictionary.filter_extremes(no_below=1, no_above=0.95)
```

| Parameter | Value | Effect |
|-----------|-------|--------|
| `no_below` | 1 | Keep terms appearing in ≥1 document |
| `no_above` | 0.95 | Drop terms in >95% of docs (too common to distinguish topics) |

Applied only when `len(dictionary) > 10`.

---

## Configuration

| Setting | Default | Override via |
|---------|---------|-------------|
| `NUM_TOPICS` | 5 | `config.py` / env `NUM_TOPICS` |
| `NUM_WORDS_PER_TOPIC` | 10 | `config.py` |
| `PASSES` | 15 | `config.py` |
| `ITERATIONS` | 100 | `config.py` |

LDA model uses `alpha='auto'` (asymmetric document-topic distribution learned from data) and `per_word_topics=True` (enables per-word topic inference for coherence calculation).

---

## Minimum Document Requirements

LDA training requires `len(documents) >= num_topics`. If fewer documents are provided:

```json
{ "success": false, "message": "Need at least 5 documents to train 5 topics. Got 3 documents." }
```
