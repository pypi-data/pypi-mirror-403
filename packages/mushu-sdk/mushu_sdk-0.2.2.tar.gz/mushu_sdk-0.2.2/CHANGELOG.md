# Changelog

## [0.2.2](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.2.1...mushu-sdk-v0.2.2) (2026-01-30)


### Features

* **auth:** add Google Sign In and Apple token revocation ([1570962](https://github.com/cjoelrun/mushu/commit/157096209b576e512484bf2320b8c5466945f63a))

## [0.2.1](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.2.0...mushu-sdk-v0.2.1) (2026-01-28)


### Features

* **media:** add custom image transforms with face detection ([2dc1608](https://github.com/cjoelrun/mushu/commit/2dc160826f77782bfa01ddcc25f608f6b960b1c9))
* **sdk:** add api_key param to mushu.client() and unified MediaClient ([2f50bdf](https://github.com/cjoelrun/mushu/commit/2f50bdfb53ff5e44d4cda80652ac3427b6a59a6c))
* **sdk:** add geo_search Python client from OpenAPI spec ([8f10769](https://github.com/cjoelrun/mushu/commit/8f107695aa2b971e80606e79ee96553d1d425585))

## [0.2.0](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.6...mushu-sdk-v0.2.0) (2026-01-27)


### ⚠ BREAKING CHANGES

* **sdk:** AuthUser, OrgMembership, OrgRole, NotifyResult removed. Use ValidateTokenResponse from mushu.auth.models instead.

### refactor

* **sdk:** remove wrappers, use generated clients directly ([5038751](https://github.com/cjoelrun/mushu/commit/5038751d180ecf2ea8af96bbf12f34c92876472d))


### Bug Fixes

* **sdk:** resolve circular dependency in SDK generation ([991317f](https://github.com/cjoelrun/mushu/commit/991317fbeb4c009a333f915e2201d362cee4ddb1))

## [0.1.6](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.5...mushu-sdk-v0.1.6) (2026-01-27)


### Features

* **api:** add explicit operation_id to all FastAPI routes ([dc49c6f](https://github.com/cjoelrun/mushu/commit/dc49c6fca304f90c19861d13e66ff414328af4aa))
* **api:** add explicit operation_id to all FastAPI routes ([8d8759b](https://github.com/cjoelrun/mushu/commit/8d8759b1c003073d6b2e67594387c08da41ba452))
* **sdk:** add high-level client wrappers ([a5740a5](https://github.com/cjoelrun/mushu/commit/a5740a54fe7d53e03898f6bf0fffc4b1b3947e10))
* **sdk:** auto-generate clients from OpenAPI specs ([61b57c4](https://github.com/cjoelrun/mushu/commit/61b57c45e6d81a2fbc9ce09e03aec092540d4d45))
* **sdk:** regenerate from OpenAPI specs ([af1a567](https://github.com/cjoelrun/mushu/commit/af1a56784b312f5c8263e0547c2a7280ba48d83a))
* **sdk:** regenerate from OpenAPI specs ([fa1c059](https://github.com/cjoelrun/mushu/commit/fa1c0593d48a253cb2ec979ff55b3e0d551566aa))

## [0.1.5](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.4...mushu-sdk-v0.1.5) (2026-01-27)


### Features

* **sdk:** add MediaClient for image/video uploads ([078aa9d](https://github.com/cjoelrun/mushu/commit/078aa9d36f403471917491cdd1a5a5b3ffd200a5))

## [0.1.4](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.3...mushu-sdk-v0.1.4) (2026-01-27)


### Features

* **sdk:** add client classes for service-to-service communication ([47b5077](https://github.com/cjoelrun/mushu/commit/47b5077b673714c419f7e54b924259e7f0881d88))
* **sdk:** regenerate from OpenAPI specs ([5201350](https://github.com/cjoelrun/mushu/commit/5201350e65dad0158d46c89e23962207d4db7998))

## [0.1.3](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.2...mushu-sdk-v0.1.3) (2026-01-26)


### Features

* **sdk:** add geo search client ([70fcabe](https://github.com/cjoelrun/mushu/commit/70fcabe59275daf516f13b4c71b0e78b335b991a))
* **sdk:** regenerate from OpenAPI specs ([c7abb2c](https://github.com/cjoelrun/mushu/commit/c7abb2cab7ea3aed1af5f491c775d2924afd4be4))

## [0.1.2](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.1...mushu-sdk-v0.1.2) (2026-01-25)


### Bug Fixes

* **sdk:** add email-validator dependency for EmailStr ([ac57008](https://github.com/cjoelrun/mushu/commit/ac57008d1715a1851b6af89662d77125740c1986))

## [0.1.1](https://github.com/cjoelrun/mushu/compare/mushu-sdk-v0.1.0...mushu-sdk-v0.1.1) (2026-01-25)


### Features

* **sdk:** regenerate from OpenAPI specs ([b1c44c5](https://github.com/cjoelrun/mushu/commit/b1c44c555175769bf20a3f493395c34bf2ee60be))
* **sdk:** regenerate from OpenAPI specs ([ab73e9e](https://github.com/cjoelrun/mushu/commit/ab73e9e575074ac1a0fa554d6154c076f7bb463d))
