# Changelog

## 0.2.1 (2026-01-30)

Full Changelog: [v0.2.0...v0.2.1](https://github.com/et0and/schools-sdk-python/compare/v0.2.0...v0.2.1)

### Chores

* configure new SDK language ([3ec2a25](https://github.com/et0and/schools-sdk-python/commit/3ec2a25ab514463373ddb1472e799d5a0afe5fe7))

## 0.2.0 (2026-01-29)

Full Changelog: [v0.1.6...v0.2.0](https://github.com/et0and/schools-sdk-python/compare/v0.1.6...v0.2.0)

### Features

* **client:** add support for binary request streaming ([4b6922e](https://github.com/et0and/schools-sdk-python/commit/4b6922e4ee9e8639f548ab3bf3346ee9effdcd98))


### Bug Fixes

* **client:** loosen auth header validation ([49eb039](https://github.com/et0and/schools-sdk-python/commit/49eb03920d3a4514f8f2184e8512fdec170544de))
* **docs:** fix mcp installation instructions for remote servers ([3fdac9d](https://github.com/et0and/schools-sdk-python/commit/3fdac9d05a1e067763ff50d0fe0f0f9f01abeb39))


### Chores

* **ci:** upgrade `actions/github-script` ([1d74fca](https://github.com/et0and/schools-sdk-python/commit/1d74fca925ab212efe0217b327dd84b26844ffa1))
* **internal:** update `actions/checkout` version ([3f50e80](https://github.com/et0and/schools-sdk-python/commit/3f50e807ee7db300d7e5419cb26cc6b5d3dcdc19))


### Documentation

* prominently feature MCP server setup in root SDK readmes ([2304058](https://github.com/et0and/schools-sdk-python/commit/2304058f312fb8f618f6cec3950b6c27b6339e69))

## 0.1.6 (2025-12-19)

Full Changelog: [v0.1.5...v0.1.6](https://github.com/et0and/schools-sdk-python/compare/v0.1.5...v0.1.6)

### Chores

* **internal:** add `--fix` argument to lint script ([90d1b77](https://github.com/et0and/schools-sdk-python/commit/90d1b7722d9a8bbc54121112a4e083075203819e))

## 0.1.5 (2025-12-18)

Full Changelog: [v0.1.4...v0.1.5](https://github.com/et0and/schools-sdk-python/compare/v0.1.4...v0.1.5)

### Bug Fixes

* **types:** allow pyright to infer TypedDict types within SequenceNotStr ([e1cc8f4](https://github.com/et0and/schools-sdk-python/commit/e1cc8f40ae0428536c274a8d9be5cb302a52c697))
* use async_to_httpx_files in patch method ([b5ca638](https://github.com/et0and/schools-sdk-python/commit/b5ca638f87291a9fa917bf47eb94d86953d677d2))


### Chores

* **internal:** add missing files argument to base client ([142e32c](https://github.com/et0and/schools-sdk-python/commit/142e32cf983b28ecc2e48466e7acd25b59b94e9a))
* speedup initial import ([187b5ab](https://github.com/et0and/schools-sdk-python/commit/187b5ab3637a18f7ec0ad769e1ed76b6eba1fa8f))

## 0.1.4 (2025-12-03)

Full Changelog: [v0.1.3...v0.1.4](https://github.com/et0and/schools-sdk-python/compare/v0.1.3...v0.1.4)

### Bug Fixes

* ensure streams are always closed ([4a636b0](https://github.com/et0and/schools-sdk-python/commit/4a636b04eaf667f6e92a60515379f2af636495d3))


### Chores

* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([d2a6052](https://github.com/et0and/schools-sdk-python/commit/d2a60529290a6aec3ec330b485b75693664a108e))
* **docs:** use environment variables for authentication in code snippets ([4ad844e](https://github.com/et0and/schools-sdk-python/commit/4ad844ed51c139f70ed4ff2f6e76ed8e0c28b3e1))
* update lockfile ([60dff69](https://github.com/et0and/schools-sdk-python/commit/60dff690c733085e0fbac043e795dde94a538547))

## 0.1.3 (2025-11-22)

Full Changelog: [v0.1.2...v0.1.3](https://github.com/et0and/schools-sdk-python/compare/v0.1.2...v0.1.3)

### Bug Fixes

* compat with Python 3.14 ([c808edf](https://github.com/et0and/schools-sdk-python/commit/c808edf7d22cd29098f8c81b35b7187e4242fe13))
* **compat:** update signatures of `model_dump` and `model_dump_json` for Pydantic v1 ([c78202e](https://github.com/et0and/schools-sdk-python/commit/c78202e38c569f832de2420791b2f63c55765873))


### Chores

* add Python 3.14 classifier and testing ([c91fd4a](https://github.com/et0and/schools-sdk-python/commit/c91fd4a0a6a8311a1405a24d180e62f09f2e1dbf))
* **package:** drop Python 3.8 support ([71ae8c2](https://github.com/et0and/schools-sdk-python/commit/71ae8c26b917bcbeb244382c7e8f0833a0742c7c))

## 0.1.2 (2025-11-04)

Full Changelog: [v0.1.1...v0.1.2](https://github.com/et0and/schools-sdk-python/compare/v0.1.1...v0.1.2)

### Chores

* update SDK settings ([de8b948](https://github.com/et0and/schools-sdk-python/commit/de8b948666ae96c851e1d75011b4e52ba5935be2))

## 0.1.1 (2025-11-04)

Full Changelog: [v0.0.1...v0.1.1](https://github.com/et0and/schools-sdk-python/compare/v0.0.1...v0.1.1)

### Chores

* configure new SDK language ([0fbcc5f](https://github.com/et0and/schools-sdk-python/commit/0fbcc5fddca8b89445bbe6e8fee11e942957b282))
* update SDK settings ([cbc3fcb](https://github.com/et0and/schools-sdk-python/commit/cbc3fcb8509c0535b526b07b9be6232e2c3e8b5d))
* update SDK settings ([03fe460](https://github.com/et0and/schools-sdk-python/commit/03fe460ff9a8c32e51c92d0f8e2f313c23635f4a))
