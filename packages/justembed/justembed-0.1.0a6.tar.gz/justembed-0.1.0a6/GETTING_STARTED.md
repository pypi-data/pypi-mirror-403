# Getting Started with Vectra v0.1.0 Development

## Project Structure Created ✓

The complete project structure has been set up with:

### Core Structure
- ✅ Package structure (`vectra/core/`, `vectra/storage/`, `vectra/utils/`, `vectra/models/`)
- ✅ Public API (`vectra/__init__.py`)
- ✅ Exception classes (`vectra/exceptions.py`)
- ✅ Version tracking (`vectra/_version.py`)

### Documentation
- ✅ `docs/FILE_REGISTRY.md` - Track all files
- ✅ `docs/FUNCTION_REGISTRY.md` - Track all functions
- ✅ `docs/DEPENDENCY_MAP.md` - Track dependencies
- ✅ `docs/decisions/` - Architecture Decision Records (ADRs)

### Configuration
- ✅ `pyproject.toml` - Modern Python packaging
- ✅ `.gitignore` - Git ignore rules
- ✅ `LICENSE` - MIT License
- ✅ `README.md` - Project overview

## Next Steps

### 1. Copy ONNX Model
```bash
# From archive to v0.1.0
cp ../archive/e5_small_multilingual/multilingual-e5-small.onnx vectra/models/
cp ../archive/e5_small_multilingual/multilingual-e5-small.onnx.data vectra/models/

# Compress the model
cd vectra/models/
tar -czf multilingual-e5-small.tar.gz multilingual-e5-small.onnx multilingual-e5-small.onnx.data
rm multilingual-e5-small.onnx multilingual-e5-small.onnx.data
cd ../..
```

### 2. Implementation Order

**Phase 1: Foundation (Week 1)**
1. `vectra/models/model_extractor.py` - Extract compressed model
2. `vectra/core/embedder.py` - ONNX model wrapper
3. `vectra/utils/hardware_detector.py` - RAM detection
4. `vectra/utils/limit_enforcer.py` - Limit enforcement
5. `vectra/utils/validator.py` - Input validation
6. `vectra/utils/timer.py` - Time tracking

**Phase 2: Storage (Week 1)**
7. `vectra/storage/parquet_writer.py` - Write embeddings
8. `vectra/storage/parquet_reader.py` - Read embeddings
9. `vectra/storage/metadata_writer.py` - Generate index.md
10. `vectra/storage/config_manager.py` - Handle config.json

**Phase 3: Core Logic (Week 2)**
11. `vectra/utils/text_chunker.py` - Text chunking
12. `vectra/core/_state.py` - Global state management
13. `vectra/core/loader.py` - Folder loading
14. `vectra/core/indexer.py` - Embedding creation
15. `vectra/core/searcher.py` - Search execution
16. `vectra/core/status.py` - Status management

**Phase 4: Testing (Week 2)**
17. Write unit tests for each module
18. Write integration tests
19. Write property-based tests

**Phase 5: Examples & Docs (Week 3)**
20. Create example scripts
21. Write API documentation
22. Write performance guide
23. Write philosophy document

### 3. Development Workflow

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black vectra/
ruff check vectra/

# Type check
mypy vectra/
```

### 4. Testing Strategy

- **Unit tests:** Test each function in isolation
- **Integration tests:** Test end-to-end workflows
- **Property-based tests:** Test limits and validation
- **Performance tests:** Verify time limits

### 5. Documentation Updates

As you implement each module:
1. Update `docs/FILE_REGISTRY.md` - Mark as ✓ Implemented
2. Update `docs/FUNCTION_REGISTRY.md` - Add function details
3. Update `docs/DEPENDENCY_MAP.md` - Add dependencies
4. Add docstrings with examples

## Ground Rules Reminder

### Naming Conventions
- Files: `<noun>_<role>.py` (e.g., `parquet_writer.py`)
- Functions: `verb_noun()` (e.g., `load_folder()`)
- Classes: `PascalCase` (e.g., `TextChunker`)
- Variables: `snake_case` (e.g., `chunk_count`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_CHUNKS`)

### Code Quality
- ✅ Type hints on all functions
- ✅ Docstrings with examples
- ✅ Keep files under 300 lines
- ✅ One class per file (when possible)
- ✅ Private functions start with `_`

### Testing
- ✅ Test file mirrors source: `test_embedder.py` for `embedder.py`
- ✅ Test function mirrors source: `test_load_folder()` for `load_folder()`
- ✅ Update registries with test coverage

## Ready to Start!

The foundation is set. Let's start implementing the modules in order.

**First task:** Copy the ONNX model and implement `model_extractor.py`

Would you like to proceed?
