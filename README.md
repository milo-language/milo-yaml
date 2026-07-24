# yaml

A YAML 1.2 subset parser for [Milo](https://github.com/milo-language/milo). No
dependencies beyond the standard library.

```bash
milo add github.com/milo-language/yaml@v0.1.0
```

```milo
from "yaml" import { yamlParse, yamlToJson }

fn main(): i32 {
    let doc = yamlParse("server:\n  host: localhost\n  port: 8080\n")!
    let host = doc.asStr(doc.path("server.host")) ?? "127.0.0.1"
    let port = doc.asInt(doc.path("server.port")) ?? 80
    print($"{host}:{port}")
    print(yamlToJson(doc))
    return 0
}
```

## Handles, not trees

A document parses into a flat pool of nodes. Every value is an `i64` handle into
that pool, and **-1 means "not there"** — so a lookup that misses is not an
error, it is a handle that reads as absent:

```milo
let port = doc.asInt(doc.path("server.port")) ?? 8080   // default if absent
```

That is why there is no `Option` at every step of a path. `Option` shows up only
where a value is actually read, so `??` supplies the default in one place.

## API

Parsing:

| Function | Returns |
|---|---|
| `yamlParse(src: string)` | `Result<Yaml>` — the first document |
| `yamlParseAll(src: string)` | `Result<Vec<Yaml>>` — every `---`-separated document |
| `yamlToJson(y: &Yaml)` | compact JSON for the whole document |

Navigating, all on `Yaml`:

| Method | Meaning |
|---|---|
| `root()` | handle of the top-level value |
| `path(p)` | dotted lookup from the root: `"services.0.image"` |
| `get(node, key)` | map entry, or -1 |
| `at(node, i)` | i-th sequence entry or map value, or -1 |
| `len(node)` | number of children (0 for scalars) |
| `keyAt(node, i)` | key of the i-th map entry |
| `has(node, key)` / `exists(node)` | membership tests |
| `kind(node)` | `YamlKind.Null / Bool / Int / Float / Str / Seq / Map / Missing` |
| `isMap` / `isSeq` / `isScalar` / `isNull` | shape tests |

Reading, all returning `Option`:

| Method | Notes |
|---|---|
| `asStr` / `asInt` / `asFloat` / `asBool` | `None` on a type mismatch or a missing handle |
| `getStr` / `getInt` / `getFloat` / `getBool` | `get` + the matching `as*`, in one call |
| `text(node)` | the scalar's source text whatever its type — `""` for containers |

`asFloat` answers for integers too, since a YAML `1` is a perfectly good float.
`asInt` does not answer for floats.

## What it parses

- Block mappings and sequences, nested to any depth
- Compact entries — `- name: x` and `- - nested`
- Sequences at their key's own indentation
- Flow collections — `[1, 2]`, `{a: 1}`, nested and mixed
- Plain, single-quoted, and double-quoted scalars, with the full escape set
  (`\n`, `\t`, `\xNN`, `\uNNNN`, `\UNNNNNNNN`, …)
- Block scalars — `|` and `>`, with `-`/`+` chomping and an explicit indent digit
- Comments, blank lines, `---`/`...` document markers, multi-document streams
- Anchors and aliases (`&name`, `*name`) and merge keys (`<<: *name`), where an
  explicitly written key always beats a merged one
- YAML 1.2 core scalar typing: `null`/`~`, `true`/`false`, decimal, `0x`, `0o`,
  `0b`, floats, `.inf`, `.nan` — plus `1_000` underscores, which are a 1.1
  carry-over kept because real config files use them

Verified against `ruamel.yaml` on the conformance corpus in `tests/conformance`
(a Kubernetes deployment, a GitHub Actions workflow, an OpenAPI document, and
targeted feature files): `scripts/oracle.py` parses each one with both and
compares the results as data.

## What it does not parse

Deliberate omissions, each a real part of YAML that config files rarely use:

- Multi-line plain scalars — a plain scalar ends at its line
- Flow collections spanning multiple lines
- Explicit key syntax (`? key`)
- Tags (`!!str`, `!Custom`) — parsed and ignored, not applied
- Directives (`%YAML`, `%TAG`)
- Complex keys — a key is always read as a string
- Tabs as indentation (YAML forbids them too)

Errors carry the line number: `line 4: unknown alias '*base'`.

## Tests

```bash
milo test tests/                                  # unit tests
python3 scripts/oracle.py --milo ./milo           # differential test (needs ruamel.yaml)
milo run examples/config.milo examples/app.yaml   # worked example
```

## License

MIT
