# @spear-ai/horizon-data-core

## 4.0.1

### Patch Changes

- 8d72350: Fixed preparing releases.
- Updated dependencies [8d72350]
  - @spear-ai/horizon-database@4.0.1

## 4.0.0

### Major Changes

- 61197be: Created an optional dependency group for SDK tests: `pip install horizon-data-core[testing]`.

### Minor Changes

- 5168023: Add Kafka-based Iceberg write path to SDK.
  - Added `IcebergRepository` for writing DataRow and MetadataRow to Iceberg tables via Kafka
  - Added `KafkaProducer` with PyArrow serialization for Iceberg-compatible messages
  - Added `KafkaConfig` and `StorageBackend` enum to configure SDK storage backend
  - Added context manager support to HorizonSDK for proper Kafka producer cleanup
  - Added `created_datetime` field to Iceberg tables for duplicate resolution

### Patch Changes

- Updated dependencies [c7886a3]
- Updated dependencies [95ce451]
- Updated dependencies [95ce451]
- Updated dependencies [95ce451]
- Updated dependencies [a30d3b8]
- Updated dependencies [95ce451]
- Updated dependencies [95ce451]
- Updated dependencies [95ce451]
- Updated dependencies [95ce451]
- Updated dependencies [5168023]
  - @spear-ai/horizon-database@4.0.0

## 3.11.2

### Patch Changes

- 64177c0: Synchronize shared developer tooling versions across packages via a catalog.
- Updated dependencies [64177c0]
- Updated dependencies [bcb856f]
  - @spear-ai/horizon-database@3.11.2

## 3.11.1

### Patch Changes

- d77906c: Fixed the release action after the pnpm migration.
- Updated dependencies [e9e4e5a]
- Updated dependencies [488ed7c]
- Updated dependencies [d77906c]
  - @spear-ai/horizon-database@3.11.1

## 3.11.0

### Minor Changes

- bef40ed: Migrated from Yarn 4 to PNPM 10 for workspace and package management.
- cae99c1: Added a human-friendly `name` field to the data_stream table for display in the UI, and updated the SDK to generate idempotent data stream IDs based on sensor and platform names.

### Patch Changes

- 798ad81: Added elevation, update_rate, and normalizer fields to BearingTimeRecordSpecification across horizon-data-core, horizon-database, and horizon-app packages
- 8d93639: Completed a dependency management and update pass.
- dfc3dd6: Add pitch, roll, and speed_over_ground fields to metadata_row table in horizon-database
- b2f2d36: Added elevation, update_rate, and normalizer fields to BeamgramSpecification across horizon-data-core, horizon-database, and horizon-app packages
- Updated dependencies [5de93a0]
- Updated dependencies [087f0c7]
- Updated dependencies [f044c34]
- Updated dependencies [798ad81]
- Updated dependencies [7bf8707]
- Updated dependencies [7de66a6]
- Updated dependencies [8c32a5d]
- Updated dependencies [8d93639]
- Updated dependencies [087f0c7]
- Updated dependencies [7440a27]
- Updated dependencies [bef40ed]
- Updated dependencies [dfc3dd6]
- Updated dependencies [b2f2d36]
- Updated dependencies [cae99c1]
- Updated dependencies [9262ea7]
- Updated dependencies [8641344]
  - @spear-ai/horizon-database@3.11.0

## 3.10.0

### Minor Changes

- 8ff4746: Make several fixes to how the SDK handles the life cycle of a connection to iceberg catalog

  Changed the default SDK behavior to only write data to postgres instead of iceberg

  BREAKING CHANGES:
  - Changes how SDK is initialized. Now must provide catalog parameters, not a catalog
  - Change from "create" and "create_or_update" verbs to "insert" and "upsert" verbs in the SDK

### Patch Changes

- 7affe45: Update shared dependencies and tooling
- Updated dependencies [c1f5996]
- Updated dependencies [7affe45]
- Updated dependencies [5462d23]
- Updated dependencies [8ff4746]
  - @spear-ai/horizon-database@3.10.0

## 3.9.0

### Patch Changes

- Updated dependencies [d9ecabb]
  - @spear-ai/horizon-database@3.9.0

## 3.8.0

### Patch Changes

- Updated dependencies [2502b1f]
- Updated dependencies [0aaed7e]
  - @spear-ai/horizon-database@3.8.0

## 3.7.1

### Patch Changes

- f97fca5: Linked Horizon package versions.
- Updated dependencies [197dd9f]
- Updated dependencies [f97fca5]
  - @spear-ai/horizon-database@3.7.1

## 0.3.9

### Patch Changes

- Updated dependencies [39d3fab]
  - @spear-ai/horizon-database@3.1.4

## 0.3.8

### Patch Changes

- Updated dependencies [186b115]
  - @spear-ai/horizon-database@3.1.3

## 0.3.7

### Patch Changes

- Updated dependencies [2595d3c]
  - @spear-ai/horizon-database@3.1.2

## 0.3.6

### Patch Changes

- Updated dependencies [ef40c73]
  - @spear-ai/horizon-database@3.1.1

## 0.3.5

### Patch Changes

- 7d111f8: Updated dependencies.
- Updated dependencies [1c37e74]
- Updated dependencies [1c37e74]
- Updated dependencies [7d111f8]
- Updated dependencies [f11ab43]
- Updated dependencies [26fb39f]
- Updated dependencies [26fb39f]
- Updated dependencies [26fb39f]
  - @spear-ai/horizon-database@3.1.0

## 0.3.4

### Patch Changes

- Updated dependencies [0e34c3f]
  - @spear-ai/horizon-database@3.0.1

## 0.3.3

### Patch Changes

- 0c63eab: Switch out psycopg2 for psycopg2-binary to avoid installation errors
- 873d1c2: Adjusted postgres connector to handle special sslmode case for neon connection.
- Updated dependencies [873d1c2]
- Updated dependencies [873d1c2]
- Updated dependencies [b60aeba]
  - @spear-ai/horizon-database@3.0.0

## 0.3.2

### Patch Changes

- 099931f: Fake patch to induce release.
- Updated dependencies [099931f]
  - @spear-ai/horizon-database@2.1.2

## 0.3.1

### Patch Changes

- 1152a0e: Fake patch to allow release.
- Updated dependencies [1152a0e]
  - @spear-ai/horizon-database@2.1.1

## 0.3.0

### Minor Changes

- 5e32b51: Adjusted pipelines generating visual artifacts to produce tiles rather than JSON.
- 5398cf6: Bump python version from 3.11 to 3.12

### Patch Changes

- dd7f8bb: Updated linting dependencies across the packages.
- 5e6c2c2: Bumped dependency versions.
- 0639322: Updated and synchronized dependencies across packages.
- Updated dependencies [5e32b51]
- Updated dependencies [dd7f8bb]
- Updated dependencies [72f5207]
- Updated dependencies [1fb74d0]
- Updated dependencies [51b4231]
- Updated dependencies [6878a4e]
- Updated dependencies [5e6c2c2]
- Updated dependencies [9aa39ae]
- Updated dependencies [535cd6d]
- Updated dependencies [0639322]
- Updated dependencies [249e936]
  - @spear-ai/horizon-database@2.1.0

## 0.2.0

### Minor Changes

- 9862f58: Migrate all data pipelines out into separate repo level packages

### Patch Changes

- Updated dependencies [b1442f6]
- Updated dependencies [b1442f6]
- Updated dependencies [bd1628a]
  - @spear-ai/horizon-database@2.0.0
