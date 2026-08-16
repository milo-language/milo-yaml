# yaml

This is a package for the [Milo language](https://milo-language.github.io/milo/).

## Overview

A YAML 1.2 subset parser, with no dependencies beyond the standard library.

Parsing hands back a `Yaml` document, and every lookup returns a *handle* rather
than an `Option`. A path into something that does not exist comes back absent
instead of forcing a branch at every hop, so `??` supplies the default once, at
the end.

Supported: block and flow collections, block scalars, anchors, aliases and merge
keys, and YAML 1.2 core scalar typing. `scripts/oracle.py` checks the results
against `ruamel.yaml` over a corpus of real Kubernetes, GitHub Actions and
OpenAPI documents.

Not supported, each a real part of YAML that config files rarely reach for:
multi-line plain scalars, flow collections spanning lines, explicit keys
(`? key`), tags (parsed but not applied), directives (`%YAML`), complex keys,
and tabs as indentation.

Every function and method: [docs/api.md](docs/api.md).

## Installation

```bash
milo add github.com/milo-language/milo-yaml            # latest release
milo add github.com/milo-language/milo-yaml@v0.2.1     # or pin a tag
```

```milo
from "yaml" import { yamlParse }
```

## Examples

### Reading a config file

Given `app.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8080
  tls: true
features:
  debug: false
```

```milo
from "yaml" import { yamlParse }
from "std/fs" import { readFile }

fn main(): i32 {
    let doc = yamlParse(readFile("app.yaml")!)!

    let host = doc.asStr(doc.path("server.host")) ?? "127.0.0.1"
    let port = doc.asInt(doc.path("server.port")) ?? 80
    let timeout = doc.asFloat(doc.path("server.timeout")) ?? 1.0
    let debug = doc.asBool(doc.path("features.debug")) ?? false

    print($"{host}:{port} timeout={timeout}s debug={debug}")
    return 0
}
```

```
0.0.0.0:8080 timeout=1s debug=false
```

Nothing in the file set `server.timeout`; the `?? 1.0` answered for it.

### Sequences

`len` and `at` walk a sequence, and a path can index one directly
(`services.0.name`):

```milo
let doc = yamlParse("
services:
  - name: web
    ports: [80, 443]
  - name: db
    ports: [5432]
")!

let services = doc.path("services")
for i in 0..doc.len(services) {
    let svc = doc.at(services, i)
    let name = doc.getStr(svc, "name") ?? "?"
    let ports = doc.get(svc, "ports")
    print($"{name}: {doc.len(ports)} port(s), first {doc.text(doc.at(ports, 0))}")
}
```

```
web: 2 port(s), first 80
db: 1 port(s), first 5432
```

### Anchors and merge keys

`&name` / `*name` and `<<:` work, and a key written out always beats a merged
one:

```milo
let doc = yamlParse("
defaults: &defaults
  restart: always

services:
  - name: web
    <<: *defaults
  - name: db
    <<: *defaults
    restart: on-failure
")!

print(doc.getStr(doc.path("services.0"), "restart") ?? "?")
print(doc.getStr(doc.path("services.1"), "restart") ?? "?")
```

```
always
on-failure
```

A complete program against a docker-compose-shaped config:
`milo run examples/config.milo examples/app.yaml`.
