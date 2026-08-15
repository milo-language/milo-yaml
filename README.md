# yaml

A YAML 1.2 subset parser for [Milo](https://github.com/milo-language/milo). No
dependencies beyond the standard library.

## Install

```bash
milo add github.com/milo-language/milo-yaml            # latest release
milo add github.com/milo-language/milo-yaml@v0.2.1     # or pin a tag
```

No tag means the newest release, which `milo add` writes into `milo.json`.
Either way, `milo.lock` pins the exact commit.

Then import it:

```milo
from "yaml" import { yamlParse }
```

## Quick start

Copy this into `main.milo` and run `milo run main.milo`:

```milo
from "yaml" import { yamlParse, yamlToJson }

fn main(): i32 {
    let doc = yamlParse("
server:
  host: 0.0.0.0
  port: 8080
  tls: true
")!

    let host = doc.asStr(doc.path("server.host")) ?? "127.0.0.1"
    let port = doc.asInt(doc.path("server.port")) ?? 80
    let tls = doc.asBool(doc.path("server.tls")) ?? false

    print($"{host}:{port} tls={tls}")
    print(yamlToJson(doc))
    return 0
}
```

```
0.0.0.0:8080 tls=true
{"server":{"host":"0.0.0.0","port":8080,"tls":true}}
```

## Reading a config file

`path` takes a dotted lookup and hands back a handle. A miss is not an error —
it is a handle that reads as absent, so `??` supplies the default:

```milo
from "yaml" import { yamlParse }
from "std/fs" import { readFile }

fn main(): i32 {
    let doc = yamlParse(readFile("app.yaml")!)!

    let host = doc.asStr(doc.path("server.host")) ?? "127.0.0.1"
    let port = doc.asInt(doc.path("server.port")) ?? 8080
    let timeout = doc.asFloat(doc.path("server.timeout")) ?? 1.0
    let debug = doc.asBool(doc.path("features.debug")) ?? false

    print($"{host}:{port} timeout={timeout}s debug={debug}")
    return 0
}
```

Because handles chain without an `Option` at every hop, a path into something
that does not exist just comes back absent instead of forcing a branch per step.

## Sequences

Index a sequence inside a path, or walk it with `len` and `at`:

```yaml
services:
  - name: web
    ports: [80, 443]
  - name: db
    ports: [5432]
```

```milo
print(doc.asStr(doc.path("services.0.name")) ?? "?")   // web

let services = doc.path("services")
for i in 0..doc.len(services) {
    let svc = doc.at(services, i)
    let name = doc.getStr(svc, "name") ?? "?"

    let ports = doc.get(svc, "ports")
    var list = ""
    for p in 0..doc.len(ports) {
        if p > 0 {
            list.pushStr(", ")
        }
        list.pushStr(doc.text(doc.at(ports, p)))
    }
    print($"{name}: [{list}]")
}
```

## Walking unknown keys

```milo
let features = doc.path("features")
for i in 0..doc.len(features) {
    let key = doc.keyAt(features, i)
    print($"{key} = {doc.text(doc.at(features, i))}")
}
```

## Anchors and merge keys

`&name` / `*name` and `<<:` work, and an explicitly written key always beats a
merged one:

```yaml
defaults: &defaults
  restart: always

services:
  - name: web
    <<: *defaults
  - name: db
    <<: *defaults
    restart: on-failure   # wins over the merged value
```

```milo
print(doc.getStr(doc.path("services.0"), "restart") ?? "no")   // always
print(doc.getStr(doc.path("services.1"), "restart") ?? "no")   // on-failure
```

## Handling parse errors

`yamlParse` returns a `Result`. `!` unwraps it (panicking on a bad document),
`?` propagates it, and `match` lets you handle it. Errors carry the line:

```milo
match yamlParse(text) {
    Result.Ok(doc) => {
        print(doc.asStr(doc.path("name")) ?? "unnamed")
    }
    Result.Err(msg) => {
        print($"bad config: {msg}")   // line 4: unknown alias '*base'
        return 1
    }
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

## Runnable examples

`examples/` holds a complete program you can run against a real config:

```bash
milo run examples/config.milo examples/app.yaml
```

- `examples/config.milo` — typed lookups with defaults, a sequence of maps,
  merge keys, and a block scalar
- `examples/app.yaml` — the docker-compose-shaped config it reads

`tests/conformance/` has the corpus: a Kubernetes deployment, a GitHub Actions
workflow, an OpenAPI document, and targeted feature files.

## API

```milo
yamlParse(src)            // Result<Yaml>       — the first document
yamlParseAll(src)         // Result<Vec<Yaml>>  — every `---`-separated document
yamlToJson(doc)           // string             — compact JSON for the whole document
```

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
parses each file with both and compares the results as data.

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

## License

MIT
