# yaml API

Three top-level functions:

```milo
yamlParse(src)            // Result<Yaml>       — the first document
yamlParseAll(src)         // Result<Vec<Yaml>>  — every `---`-separated document
yamlToJson(doc)           // string             — compact JSON for the whole document
```

`yamlParse` returns a `Result`, and the error carries the line it failed on
(`line 4: unknown alias '*base'`). `!` unwraps it, `?` propagates it, `match`
handles it.

Everything else is a method on `Yaml`, taking and returning node handles:

```milo
// navigate
doc.root()                       // handle of the top-level value
doc.path("services.0.image")     // dotted lookup from the root
doc.get(node, "key")             // map entry
doc.at(node, i)                  // i-th sequence entry or map value
doc.len(node)                    // child count (0 for scalars)
doc.keyAt(node, i)               // key of the i-th map entry

// read — all return Option
doc.asStr(node)     doc.asInt(node)     doc.asFloat(node)     doc.asBool(node)
doc.getStr(node, "k")   doc.getInt(node, "k")                 // get + as*, in one call
doc.getFloat(node, "k") doc.getBool(node, "k")
doc.text(node)                   // the scalar's source text, whatever its type

// what is here
doc.kind(node)                   // YamlKind.Null | Bool | Int | Float | Str | Seq | Map | Missing
doc.isMap(node)     doc.isSeq(node)     doc.isScalar(node)    doc.isNull(node)
doc.has(node, "k")  doc.exists(node)
```

`asFloat` answers for integers too, since a YAML `1` is a perfectly good float.
`asInt` does not answer for floats.

A lookup that misses is not an error — it returns a handle that reads as absent,
which is why `??` at the end of a chain is enough and no step needs its own
branch.

## Walking a map with unknown keys

`len` and `keyAt` iterate a map whose schema you do not know ahead of time:

```milo
let features = doc.path("features")
for i in 0..doc.len(features) {
    let key = doc.keyAt(features, i)
    print($"{key} = {doc.text(doc.at(features, i))}")
}
```

## Multiple documents

```milo
from "yaml" import { yamlParseAll }

let docs = yamlParseAll("a: 1\n---\na: 2\n")!
for i in 0..docs.len {
    print((docs[i].asInt(docs[i].path("a")) ?? 0).toString())
}
```

## What it parses

- Block mappings and sequences, nested to any depth
- Compact entries — `- name: x` and `- - nested`
- Sequences at their key's own indentation
- Flow collections — `[1, 2]`, `{a: 1}`, nested and mixed
- Plain, single-quoted, and double-quoted scalars, with the full escape set
  (`\n`, `\t`, `\xNN`, `\uNNNN`, `\UNNNNNNNN`, …)
- Block scalars — `|` and `>`, with `-`/`+` chomping and an explicit indent digit
- Comments, blank lines, `---`/`...` document markers, multi-document streams
- Anchors, aliases, and merge keys
- YAML 1.2 core scalar typing: `null`/`~`, `true`/`false`, decimal, `0x`, `0o`,
  `0b`, floats, `.inf`, `.nan` — plus `1_000` underscores, which are a 1.1
  carry-over kept because real config files use them

Checked against `ruamel.yaml` over the conformance corpus: `scripts/oracle.py`
parses each file with both and compares the results as data. The corpus in
`tests/conformance/` is a Kubernetes deployment, a GitHub Actions workflow, an
OpenAPI document, and targeted feature files.

## What it does not parse

Deliberate omissions, each a real part of YAML that config files rarely use:

- Multi-line plain scalars — a plain scalar ends at its line
- Flow collections spanning multiple lines
- Explicit key syntax (`? key`)
- Tags (`!!str`, `!Custom`) — parsed and ignored, not applied
- Directives (`%YAML`, `%TAG`)
- Complex keys — a key is always read as a string
- Tabs as indentation (YAML forbids them too)

## Tests

```bash
milo test tests                                   # unit tests
python3 scripts/oracle.py --milo ./milo           # differential test (needs ruamel.yaml)
milo run examples/config.milo examples/app.yaml   # worked example
```
