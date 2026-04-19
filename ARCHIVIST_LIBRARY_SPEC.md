# Archivist Library — Technical Specification (AL1)

**Status:** normative for engine implementation  
**Version:** `AL1`  
**Parent document:** `THE_ARCHIVIST_Design_Document_v2.md` §1.5  
**Reference implementation (Python):** `archivist_al1.py` — kept in lockstep with this file; `python -m unittest discover -s tests` must pass before changing either.  

This file defines **the Archivist Library**: a deterministic fictional text space used by *The Archivist*. It is **not** compatible with any third-party “Library of Babel” website. Coordinates are meaningful **only** inside this ecosystem.

---

## 1. Scope

| In scope | Out of scope |
|----------|----------------|
| Exact alphabet, page size, coordinate grammar | Search / inversion (finding coordinates from arbitrary text) |
| Deterministic mapping **coordinate → page text** | Claiming statistical “meaning” of output |
| Canonical string form for logs, Firebase, gallery | Lore text (handled in the design doc) |

Future revisions may introduce **`AL2`** with a new section in this document; `AL1` remains frozen for reproducibility of archived artefacts unless a deliberate migration path is published.

---

## 2. Alphabet (`ALPHABET_AL1`)

Pages are built from **29** characters, in this **fixed order** (index `0 … 28`):

```
abcdefghijklmnopqrstuvwxyz␠,.
```

In plain text:

- Indices `0–25`: lowercase ASCII `a`–`z`
- Index `26`: **SPACE** (U+0020)
- Index `27`: **COMMA** (U+002C)
- Index `28`: **FULL STOP** (U+002E)

**Rules**

- No uppercase, no digits inside page body, no newlines inside the body.
- All string comparisons for coordinates use **UTF-8** encoding.

---

## 3. Page geometry

| Quantity | Value |
|----------|-------|
| Characters per line | `80` |
| Lines per page | `40` |
| Characters per page | `3200` (= 80 × 40) |

**Linear storage:** a page is a single Unicode string of exactly **3200** characters from `ALPHABET_AL1`.

**Display:** render as **40** lines of **80** characters (wrap at column 80; no extra newline characters stored in the body).

---

## 4. Canonical coordinate (`COORD_AL1`)

### 4.1 Grammar

```
COORD_AL1 ::= "AL1-" PAGE_ID
PAGE_ID     ::= 64 * HEX_DIGIT
HEX_DIGIT   ::= "0"|"1"|...|"9"|"a"|"b"|...|"f"
```

**Examples (valid)**

- `AL1-` + `0` repeated 64 times (minimal page id)
- `AL1-` + any 64 lowercase hex digits

**Invalid**

- Wrong prefix (`al1-`, `AL2-`, …)
- Uppercase hex (`A-F`)
- Length ≠ 64 hex digits after `AL1-`
- Characters outside `[0-9a-f]`

### 4.2 Canonicalisation

Input from users or URLs may be normalised before lookup:

1. Strip leading / trailing ASCII whitespace.
2. If the prefix matches `AL1-` case-insensitively, rewrite as exact ASCII `AL1-`.
3. Lowercase all hex digits.
4. Validate length and character set.

The **canonical form** stored in JSON / Firestore is always:

`AL1-` + **64 lowercase hex digits** → **68** UTF-8 characters total (`AL1-` is four characters: `A`, `L`, digit `1`, `-`).

---

## 5. Deterministic generation — `page_text(coord) → str`

**Goal:** same canonical `coord` → same 3200-character string, on any conforming implementation (Python today; other languages tomorrow).

### 5.1 PRNG stream (counter-based SHA-256)

Let `coord_bytes = UTF8(coord_canonical)`.

For `counter = 0, 1, 2, …` (64-bit unsigned integer, little-endian when serialised):

```
block = SHA256( coord_bytes || uint64_le(counter) )
```

Each `block` is 32 bytes. Interpret as **eight** consecutive 32-bit unsigned integers (big-endian per integer):

For byte indices `0,4,8,12,16,20,24,28` in each block, take 4 bytes starting there:

```
u = int_from_uint32_be(block[i : i+4])
character_index = u mod 29
append ALPHABET_AL1[character_index]
```

Append until exactly **3200** characters have been produced. Increment `counter` only after consuming all eight indices from the current block.

**Order of consumption inside one SHA block:** indices `0, 4, 8, 12, 16, 20, 24, 28` (eight characters per hash).

**Note on bias:** `u mod 29` is slightly biased. This is acceptable for `AL1` (atmospheric noise). A future `AL2` may switch to rejection sampling or a different KDF.

### 5.2 Reference vectors (implementations MUST match)

**Coordinate**

```text
AL1-0000000000000000000000000000000000000000000000000000000000000000
```

**First 80 characters of the page** (single line; wrap mentally at 80 for display):

```text
oq pzeofkxleerybcza.hmbjiclgzrsw,omjmqnhopa,ldvzpi rljoucacpbiaarxbvdghhbf,gdksr
```

**Last 80 characters** (line 40 of the display grid):

```text
aqksofhylydqo,dnazptirypngaj.hujkpkrgeeoruqwzbiipkx rosjcgnzmisycwvoxvixpw,kwvfz
```

**Fingerprint (normative):** `SHA256` over the UTF-8 encoding of the full 3200-character page string (hex, lowercase):

```text
11c535f46bc509d104ef92c5414366a8554868bf85e4ac1b528bb30fe73b5d34
```

Implementers: add a unit test that `sha256(page_text.encode('utf-8')).hexdigest()` equals the fingerprint above for this coordinate (strictest) or, equivalently, assert full string equality character by character.

---

## 6. Scanning API (non-normative hints)

The design doc allows random exploration. **Suggested** internal representation of a “draw”:

1. Sample 32 bytes cryptographically random (`secrets.token_bytes(32)`) **or** derive from a counter for reproducible benchmarks.
2. Encode as 64 hex digits → canonical coordinate.
3. Call `page_text`.

This spec does **not** require a particular exploration strategy.

---

## 7. JSON fields (interchange)

| Field | Type | Description |
|-------|------|-------------|
| `library_version` | string | e.g. `"AL1"` |
| `coordinates` | string | Canonical `COORD_AL1` |
| `page_text` | string | Optional cache; must match `page_text(coordinates)` if present |
| `fragment` | string | Substring or excerpt flagged by filters (verbatim slice of `page_text`) |

Artefacts logged in `archivist_log.json` should always include `library_version` and `coordinates` so reopening works after code changes to filters.

---

## 8. Viewer behaviour

Any **Archivist viewer** (local or gallery) must:

1. Accept canonical `COORD_AL1`.
2. Recompute `page_text` with this spec.
3. Optionally highlight a character range if `fragment` includes offsets.

---

## 9. Change control

| Change | Action |
|--------|--------|
| Typo in reference example | Fix + bump doc patch version in footer |
| Alphabet / geometry / hash algorithm | New `AL2` section; never silently alter `AL1` |

---

*End of ARCHIVIST_LIBRARY_SPEC.md (AL1)*
