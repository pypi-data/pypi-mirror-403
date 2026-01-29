# Changelog

All notable changes to pydantic-variants will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-28

### Added
- **ComputedToFields transformer**: Converts computed fields to regular fields in output variants
  - Useful when computed fields depend on internal/excluded fields that won't be available in variants
  - Supports tag-based filtering with `include` and `exclude` parameters
  - Supports callable-based filtering for complex logic
  - Preserves return type as field annotation
  - Preserves docstring as field description
  - 17 new tests covering all transformer features

### Changed
- Exported `ComputedToFields` from `pydantic_variants.transformers`

### Testing
- Increased test coverage to 326 total tests

---

## [0.5.0] - 2026-01-25

### Added
- **Computed field support in name-based transformers**: `FilterFields`, `RenameFields`, and `ModifyFields` now handle computed fields in addition to regular model fields
  - `FilterFields` can exclude/include computed fields by name
  - `RenameFields` can rename computed fields using mapping or rename function
  - `ModifyFields` can modify computed field properties
- **Comprehensive test suite**: 15+ new tests covering edge cases, combinations, and dependencies
  - Tests for computed field dependencies on filtered/renamed fields
  - Tests for transformer combinations (Filter+Rename, Filter+Modify, all three)
  - Edge case tests: empty computed_fields dict, complex filter logic, pattern-based renaming
  - Model dump reflection tests

### Changed
- `FilterFields`, `RenameFields`, and `ModifyFields` now access `_pydantic_decorators.computed_fields` in addition to `model_fields`
- Updated docstrings to document computed field support

### Testing
- Increased test coverage to 309 total tests (up from 294)
- All tests validate edge cases and real-world usage patterns
- Tests document expected errors (e.g., computed fields depending on renamed fields)

---

## [0.4.1] - Previous Version

### Added
- Previous features and improvements
- Test framework and initial test suite coverage

### Changed
- Core transformer implementations
