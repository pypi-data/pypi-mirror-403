# Codebase Review Issues

**Review Date:** 2026-01-29  
**Focus:** API usability, docstrings, docstring tests (mktestdocs)
**Status:** Mostly completed

---

## Executive Summary

The codebase is well-structured with good API design. Issues identified and resolved:

1. ✅ **Fixed test_docs.py** - Now uses correct folder structure with syntax-only testing
2. ✅ **Added docstring examples** - All evaluators have runnable examples
3. ✅ **Added doctest +SKIP markers** - API-dependent examples properly marked
4. ✅ **Enhanced optimizer documentation** - Detailed DSPy optimizer guide added
5. ✅ **Resolved use-cases/cookbook redundancy** - Renamed to "Industry Solutions"

---

## Issue 1: Fix test_docs.py to Match Actual Docs Structure

**Labels:** `bug`, `testing`, `high-priority`

**Description:**
The `tests/test_docs.py` file references folder paths that don't exist:
- `docs/tutorials/` - doesn't exist
- `docs/how-to-guides/` - doesn't exist

Actual structure is:
- `docs/guides/optimization/`
- `docs/guides/evaluators/`
- `docs/guides/advanced/`
- `docs/concepts/`
- `docs/reference/api/`

**Acceptance Criteria:**
- [ ] Update test_docs.py to use actual folder structure
- [ ] Test all markdown files in docs/guides/, docs/concepts/
- [ ] Test docs/index.md and docs/core-concepts.md
- [ ] Run tests to verify they pass

---

## Issue 2: Add Runnable Docstring Examples to Evaluators

**Labels:** `enhancement`, `documentation`

**Description:**
Evaluator classes in `src/dspydantic/evaluators/` have minimal docstrings. They should have:
- Class-level docstrings explaining purpose
- Examples showing instantiation and usage
- Proper type hints (already good)

Files needing improvement:
- `levenshtein.py` - needs usage example
- `text_similarity.py` - needs usage example  
- `python_code.py` - needs usage example
- `predefined_score.py` - needs usage example
- `string_check.py` - needs usage example
- `label_model_grader.py` - needs usage example

**Acceptance Criteria:**
- [ ] Each evaluator class has a docstring with Example section
- [ ] Examples are self-contained and runnable
- [ ] Examples follow Google-style docstring format

---

## Issue 3: Add Missing Docstrings to extractor.py Functions

**Labels:** `enhancement`, `documentation`

**Description:**
The `extractor.py` module has some functions with docstrings but they could be improved with more examples:

- `extract_field_descriptions()` - has example, good
- `extract_field_types()` - has example, good  
- `apply_optimized_descriptions()` - has example but could be more complete
- `create_optimized_model()` - has example, good

**Acceptance Criteria:**
- [ ] All public functions have complete docstrings
- [ ] Each has at least one runnable example
- [ ] Examples demonstrate common use cases

---

## Issue 4: Make Prompter Docstring Examples Fully Testable

**Labels:** `enhancement`, `testing`

**Description:**
The `Prompter` class has good examples in its docstring, but they may not be fully testable with mktestdocs because:
- They require API keys (need mock or skip logic)
- Some examples use `...` for brevity

**Acceptance Criteria:**
- [ ] Add `# doctest: +SKIP` to examples requiring real API calls
- [ ] Add minimal testable examples that don't need API calls
- [ ] Ensure examples showing class instantiation work without network

---

## Issue 5: Add Docstrings to Module-Level Functions

**Labels:** `enhancement`, `documentation`

**Description:**
Some module-level functions lack complete docstrings:

- `utils.py` - `prepare_input_data()`, `convert_images_to_dspy_images()` need examples
- `persistence.py` - `save_prompter_state()`, `load_prompter_state()` need examples

**Acceptance Criteria:**
- [ ] All public functions have docstrings with Args, Returns, Example
- [ ] Examples are runnable without side effects where possible

---

## Issue 6: Add Integration Test for Docstring Examples

**Labels:** `enhancement`, `testing`

**Description:**
Create a proper integration test that validates all docstring examples can run (or are properly skipped).

The current approach with mktestdocs only tests markdown files. We also need:
- doctest-style testing of Python module docstrings
- Proper test configuration in pytest

**Acceptance Criteria:**
- [ ] Add pytest-doctest configuration to pyproject.toml
- [ ] Or create explicit test file that imports and tests docstrings
- [ ] Ensure CI runs docstring tests

---

## Issue 7: Document All Evaluator Types in evaluators/config.py

**Labels:** `enhancement`, `documentation`

**Description:**
The `EVALUATOR_REGISTRY` stores all available evaluators, but there's no documentation listing them. Add a comprehensive docstring listing:
- All registered evaluator names
- Brief description of each
- When to use each type

**Acceptance Criteria:**
- [ ] Add module-level docstring with evaluator catalog
- [ ] Include table of evaluator types and use cases
- [ ] Cross-reference with API docs

---

## Issue 8: Verify All Code Snippets in Docs Are Runnable

**Labels:** `testing`, `documentation`

**Description:**
Run mktestdocs on all markdown files and fix any failing examples. Common issues:
- Missing imports
- Incomplete code that can't run standalone
- Examples that need API calls should be marked appropriately

**Acceptance Criteria:**
- [ ] All code blocks in docs/ are either runnable or explicitly marked as pseudo-code
- [ ] mktestdocs tests pass for all documentation files
- [ ] Add test markers for examples requiring real API calls

---

## Issue 9: Add Type Stubs or Improve Type Annotations

**Labels:** `enhancement`, `quality`

**Description:**
While type hints are generally good, some areas could be improved:
- `Callable` types in optimizer.py are complex - consider type aliases
- Some `Any` types could be more specific

**Acceptance Criteria:**
- [ ] Review and improve type annotations where possible
- [ ] Add type aliases for complex callable signatures
- [ ] Run mypy and fix any type errors

---

## Issue 10: Ensure Example Files Are Up-to-Date with API

**Labels:** `maintenance`, `documentation`

**Description:**
Verify that example files in `examples/` directory work with the current API:
- `text_example.py` - uses PydanticOptimizer directly
- `image_example.py` - check imports
- `imdb_example.py` - verify works
- `evaluator_config_example.py` - verify works
- `judge_without_examples.py` - verify works

**Acceptance Criteria:**
- [ ] All examples run without errors (with proper API keys)
- [ ] Examples demonstrate best practices
- [ ] Add comments explaining key concepts

---

## Execution Order

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | Issue 1 (fix test_docs.py) | Low | High - Unblocks doc testing |
| 2 | Issue 8 (verify doc snippets) | Medium | High - User experience |
| 3 | Issue 2 (evaluator docstrings) | Medium | Medium |
| 4 | Issue 4 (Prompter examples) | Low | Medium |
| 5 | Issue 5 (module functions) | Low | Low |
| 6 | Issue 6 (integration test) | Medium | Medium |
| 7 | Issue 7 (evaluator catalog) | Low | Low |
| 8 | Issue 3 (extractor docs) | Low | Low |
| 9 | Issue 9 (type annotations) | Medium | Low |
| 10 | Issue 10 (example files) | Medium | Low |

---

## Notes

- The API is well-designed with good separation of concerns
- The `Prompter` class provides a clean unified interface
- Evaluator system is extensible and well-architected
- Multi-modal support (text, images, PDFs) is a strong differentiator
- Save/load functionality works well for production deployment
