# yaml

This is a package for the [Milo language](https://milo-language.github.io/milo/).

## Overview

Parse YAML and read values out of it.

```milo
let port = doc.asInt(doc.path("server.port")) ?? 8080
```

A lookup that misses comes back absent rather than erroring, so `??` supplies
the default at the end of a chain and no step in the middle needs a branch.

Covers the YAML config files are actually written in, including anchors and
merge keys. Skips a few corners of the spec (multi-line plain scalars, tags,
directives). Full list and API: [docs/api.md](docs/api.md).

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
