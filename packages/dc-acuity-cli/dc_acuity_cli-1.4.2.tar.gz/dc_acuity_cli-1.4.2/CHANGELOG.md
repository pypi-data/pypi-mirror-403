# Changelog

## [1.4.2](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.4.1...v1.4.2) (2026-01-30)


### Bug Fixes

* **client:** honor Retry-After=0 and surface rate limit exhaustion ([#32](https://github.com/DallasCrilleyMarTech/acuity-scheduling/pull/32))
* **client:** retry connection errors and guard invalid JSON/non-dict errors ([#32](https://github.com/DallasCrilleyMarTech/acuity-scheduling/pull/32))
* **cli:** keep calendar_id=0, validate config keys, and lock config permissions ([#32](https://github.com/DallasCrilleyMarTech/acuity-scheduling/pull/32))
* **commands:** remove duplicate validation and align exit codes ([#32](https://github.com/DallasCrilleyMarTech/acuity-scheduling/pull/32))

## [1.4.1](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.4.0...v1.4.1) (2026-01-29)


### Bug Fixes

* **cli:** show help on bare invocation + docs & CI updates ([#30](https://github.com/DallasCrilleyMarTech/acuity-scheduling/issues/30)) ([43f54b0](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/43f54b03977e289687642bc2371e9cc4cdfb8741))

## [1.4.0](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.3.1...v1.4.0) (2026-01-29)


### Features

* **cli:** add update guidance for PEP 668 ([acd8ba2](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/acd8ba268457d56928fccf5a815f2b2b037a5452))
* **cli:** add update guidance for PEP 668 ([bc35aa6](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/bc35aa6dd7b1f06ded7847cb0b1c27e98749dce3))

## [1.3.1](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.3.0...v1.3.1) (2026-01-29)


### Bug Fixes

* **cli:** align version with package metadata ([64e44e4](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/64e44e45701e93f06137da562589e759f41bc28a))
* **cli:** align version with package metadata ([be29f17](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/be29f17bbc146ef7dc26e6834dd5befe96d69489))


### Documentation

* **readme:** add install notes for tag releases ([08af0d6](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/08af0d69254c2e0eb03757073359b4e0c590c85b))

## [1.3.0](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.2.1...v1.3.0) (2026-01-29)


### Features

* add emergency block and client history commands ([#22](https://github.com/DallasCrilleyMarTech/acuity-scheduling/issues/22)) ([e53c3ff](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/e53c3ff9597a3f8484d9ed1fa637976c4ace09fd))
* **appointments:** support labels and no-email ([ca85cec](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/ca85cecb751e746372c185bf0d027a777a7012f8))
* **appointments:** support labels and no-email ([8ab1a82](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/8ab1a8284ccd685de290a21caf5891a520f87d1f))

## [1.2.1](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.2.0...v1.2.1) (2026-01-17)


### Documentation

* fix critical UX friction points in CLI ([#20](https://github.com/DallasCrilleyMarTech/acuity-scheduling/issues/20)) ([23386a8](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/23386a841a4816366f9694e77ecd38caa9cae8da))

## [1.2.0](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.1.0...v1.2.0) (2026-01-16)


### Features

* add verbose logging, pagination, config command, and datetime validation ([#17](https://github.com/DallasCrilleyMarTech/acuity-scheduling/issues/17)) ([81aeb41](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/81aeb4155d858e245aba8b0b35c8057dc3148a28))

## [1.1.0](https://github.com/DallasCrilleyMarTech/acuity-scheduling/compare/v1.0.0...v1.1.0) (2026-01-16)


### Features

* add appointment exclusion filtering ([b57e4f6](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/b57e4f66ce055e8e7f369fb677f0c97fb0699e9e))
* add appointment exclusion filtering ([99c1536](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/99c15365f8c7ac357f3bd595f13e75be0e2148f8))
* load ops credentials into config ([#16](https://github.com/DallasCrilleyMarTech/acuity-scheduling/issues/16)) ([fdd0468](https://github.com/DallasCrilleyMarTech/acuity-scheduling/commit/fdd0468b3a2d43a9bcd3e0acc3be63f84bed9f37))
