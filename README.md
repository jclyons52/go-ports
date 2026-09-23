# Go ports of JavaScript tooling

npm packages rebuilt in Go, verified against the originals.

Each project below is a Go implementation of a JavaScript/npm library or tool. None of them are 'inspired by' rewrites: every one carries a parity harness that runs the real npm package as the oracle and fails when the Go output differs. The numbers on this page are the gate results from those harnesses.

Website: https://jclyons52.github.io/go-ports/ (built from `manifest.json` by `build_site.py`)

## The ESLint chain

The parser → scope analysis → rules pipeline, each layer verified against the npm original it ports.

- **[eslint-go](https://github.com/jclyons52/eslint-go)** — port of `eslint 8.57.0`. Linter.verify/verifyAndFix, SourceCode + token store, report-translator, rule-fixer, formatters and the CLI. This is the composition target of the whole effort. _e2e: 11/11 CLI scenarios byte-identical to eslint 8.57 (stylish, coloured stylish, json, --fix, --quiet, globs, stdin)_
- **[espree-go](https://github.com/jclyons52/espree-go)** — port of `espree 9.6.1`. The ESLint parser: acorn plus espree's post-processing — Program bounds, TemplateElement offsets, loc/range emission, Esprima-style parse errors. _full AST (structure + start/end + loc + range + tokens + comments) identical to espree over the corpus; 19 unparsable inputs with identical message/line/column_
- **[acorn-go](https://github.com/jclyons52/acorn-go)** — port of `acorn 8.15`. The JavaScript parser itself — the largest single port in the chain (6.4k LOC of parser, tokenizer and scope logic). _91/91 JS-oracle cases including dynamic import() and import.meta_
- **[eslint-scope-go](https://github.com/jclyons52/eslint-scope-go)** — port of `eslint-scope 7.2.2`. Scope analysis: nested scopes, variables, references, through-references — what makes no-undef / no-unused-vars / no-shadow possible. _40 cases comparing a canonical ScopeManager serialization, 0 mismatches_
- **[estraverse-go](https://github.com/jclyons52/estraverse-go)** — port of `estraverse 5.3.0`. AST traversal with visitor keys, plus replace/attachComments. _traversal order, replace/remove, parent arguments and visitor-keys table all match the oracle_
- **[esquery-go](https://github.com/jclyons52/esquery-go)** — port of `esquery 1.7.0`. The selector engine behind ESLint's inline rule configuration and `--rule` selectors. _1850 parse + 29874 query + 6786 matches (94024 node results) cases, 0 mismatches_

## Leaf packages

The dependency leaves ESLint pulls in, ported one repo each — code, tests and the JS oracle that decides whether the port is done.

- **[prelude-ls-go](https://github.com/jclyons52/prelude-ls-go)** — port of `prelude-ls 1.2.1`. Prelude.ls functional helpers (option/obj/str/func/list). _1.2.1 subset parity suite green_
- **[argparse-go](https://github.com/jclyons52/argparse-go)** — port of `argparse 2.0.1`. Python-style argument parsing — ported from the JS port of the Python library. _parity suite green against the npm original_
- **[ignore-go](https://github.com/jclyons52/ignore-go)** — port of `ignore 5.3.2`. gitignore semantics for ignore files and pattern matching. _parity suite green_
- **[uri-js-go](https://github.com/jclyons52/uri-js-go)** — port of `uri-js 4.4.1`. URI parsing/serialization and normalization. _parity suite green_
- **[lodash-merge-go](https://github.com/jclyons52/lodash-merge-go)** — port of `lodash.merge 4.6.2`. Deep merge with lodash's exact coercion rules. _42/42 byte-parity cases (string/array-like sources, length resize, __proto__, typed arrays)_
- **[json-schema-traverse-go](https://github.com/jclyons52/json-schema-traverse-go)** — port of `json-schema-traverse 0.4.1`. Schema traversal callbacks for JSON Schema validation. _event-sequence parity against the oracle_
- **[eslint-community-regexpp](https://github.com/jclyons52/eslint-community-regexpp)** — port of `@eslint-community/regexpp 4.12.1`. Regular-expression parser with full ES2024 syntax, including v-mode and modifier groups. _62/62 byte-parity including named groups, v-mode, modifier groups_
- **[flatted-go](https://github.com/jclyons52/flatted-go)** — port of `flatted 3.4.4`. Circular-JSON parse/stringify. _28/28 round-trip + 13/13 byte-parity_
- **[debug-go](https://github.com/jclyons52/debug-go)** — port of `debug 4.3.4`. The namespace-based debug logger's core. _namespace-matching parity_
- **[ungap-structured-clone-go](https://github.com/jclyons52/ungap-structured-clone-go)** — port of `@ungap/structured-clone 1.3.3`. Structured clone (serialize/deserialize) including Map/Set/Date/RegExp. _round-trip 29/0, structural 15/0_
- **[humanwhocodes-object-schema-go](https://github.com/jclyons52/humanwhocodes-object-schema-go)** — port of `@humanwhocodes/object-schema 1.2.1`. Object schema validation/merge strategies. _parity suite green_
- **[nodelib-fs-stat-go](https://github.com/jclyons52/nodelib-fs-stat-go)** — port of `@nodelib/fs.stat 2.0.5`. Filesystem stat with a symlink policy. _symlink-policy parity_
- **[isexe-go](https://github.com/jclyons52/isexe-go)** — port of `isexe 2.0.0`. Executable permission checks. _permission-matrix parity_
- **[esutils-go](https://github.com/jclyons52/esutils-go)** — port of `esutils 2.0.3`. AST/code/keyword helpers used across the estools family. _parity suite green_
- **[color-name-go](https://github.com/jclyons52/color-name-go)** — port of `color-name 1.1.4`. CSS colour-name table. _148 entries, 0 mismatches_
- **[eslint-visitor-keys-go](https://github.com/jclyons52/eslint-visitor-keys-go)** — port of `eslint-visitor-keys 3.4.3`. The canonical ESTree visitor-keys table ESLint traverses by. _table parity against the oracle_

## Tooling

The machinery that made the ports above affordable — and the ports of developer tooling in their own right.

- **[uplift](https://github.com/jclyons52/uplift)** — port of `JS → Go toolchain`. The pipeline used for every port: measure a JS codebase, resolve its npm→Go counterpart registry, scaffold a repo with a real parity harness, ingest .d.ts contracts, and transpile/lift where that is cheaper than hand-porting. _registry verdicts (port / use_existing / stdlib / inline) so a leaf is assessed once, never re-derived_
- **[ts-go-morph](https://github.com/jclyons52/ts-go-morph)** — port of `ts-morph`. Go port of ts-morph (TypeScript AST manipulation) — the TypeScript-side counterpart of the parser chain. _baseline suite against the original_
- **[go-gqlcodegen](https://github.com/jclyons52/go-gqlcodegen)** — port of `GraphQL Code Generator`. Native Go port of GraphQL Code Generator: byte-identical TypeScript output, ~90x faster cold start, no Node runtime. _generated output byte-identical to the npm tool_
- **[go-typewryter](https://github.com/jclyons52/go-typewryter)** — port of `typewryter`. Go port of the typewryter CLI for generating TypeScript types from data. _output parity against the original CLI_

## How a port is verified

1. Vendor the original npm package next to the Go code — the oracle, not a reference to read.
2. Build a corpus of real inputs (valid, invalid, edge, non-ASCII) and a driver that runs the original package over it.
3. Run the same corpus through the Go implementation and diff the results: full JSON ASTs for parsers, message objects for linters, byte-for-byte output for code generators and fixers.
4. Treat any difference as a bug in the port. When the difference is caused by the original's own behaviour, encode that behaviour deliberately and say so in the README.
5. Commit only when the harness reports zero mismatches, and keep the number in the repo's README so it can be re-checked.
