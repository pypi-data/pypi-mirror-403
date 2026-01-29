# SecureX SDK Test Suite

## 📊 Coverage Overview

**Overall Coverage: 96%** (1,236 statements, 49 missing)

### Coverage by Component

| Component | Coverage | Status |
|-----------|----------|--------|
| Client | 100% | ✅ |
| Handlers (Channel, Role, Member) | 100% | ✅ |
| Workers (Action, Cleanup, Guild, Log) | 100% | ✅ |
| Utils (Punishment, Whitelist) | 100% | ✅ |
| Models | 100% | ✅ |
| Backup Manager | 88% | ✅ |

## 🚀 Running Tests

### Run all tests with coverage
```bash
pytest tests/ --cov=securex --cov-report=term-missing -v
```

### Run specific test file
```bash
pytest tests/test_coverage_handlers.py -v
```

### Run specific test class
```bash
pytest tests/test_coverage_handlers.py::TestHandlersExhaustive -v
```

### Generate HTML coverage report
```bash
pytest tests/ --cov=securex --cov-report=html
open htmlcov/index.html
```

## 📁 Test Files

### Comprehensive Coverage Tests

#### `test_coverage_client.py`
Tests the main SecureX client initialization and event handling.
- Audit log listener functionality
- Event registration and callbacks
- Enable/disable mechanisms
- Proxy method delegation

#### `test_coverage_handlers.py`
Tests all handler classes for 100% coverage.
- **ChannelHandler**: Unauthorized channel deletions/updates
- **RoleHandler**: Unauthorized role deletions/updates
- **MemberHandler**: Ban protection and dangerous permissions

#### `test_coverage_manager.py`
Tests the BackupManager for comprehensive backup/restore operations.
- Channel backup and restoration (text, voice, category, stage)
- Role backup and restoration
- Permission restoration
- Guild settings and vanity URL management
- Cache management and auto-refresh

#### `test_coverage_utils.py`
Tests utility classes and data models.
- **Models**: ThreatEvent, BackupInfo, RestoreResult, WhitelistChange
- **PunishmentExecutor**: All punishment types and error handling
- **WhitelistManager**: Add/remove/check operations

#### `test_coverage_workers.py`
Tests all worker classes for 100% coverage.
- **ActionWorker**: Punishment execution and cleanup
- **CleanupWorker**: Unauthorized creation removal
- **GuildWorker**: Restoration coordination
- **LogWorker**: Event logging

### Legacy Tests

#### `test_action_worker.py`
Basic tests for ActionWorker functionality.

#### `test_backup_manager.py`
Basic tests for BackupManager initialization.

#### `test_client.py`
Basic tests for SecureX client.

#### `test_guild_worker.py`
Tests for GuildWorker user token management.

#### `test_handlers.py`
Basic handler initialization tests.

#### `test_integration.py`
Integration tests for queue systems and end-to-end flows.

#### `test_logic.py`
Logic tests for worker processing.

## 🎯 Coverage Goals

### Achieved ✅
- All handlers: 100%
- All workers: 100%
- All utils: 100%
- Client: 100%
- Models: 100%

### BackupManager (88%)
The remaining 12% (49 lines) in BackupManager are complex edge cases:
- Stage channel restoration in category children
- Member permission edge cases with error handling
- Orphaned channel moving scenarios
- Complex asyncio timing and Discord API edge cases

These represent defensive code that's difficult to test without causing mock serialization issues.

## 📝 Test Conventions

### Naming
- Comprehensive tests: `test_coverage_*.py`
- Legacy tests: `test_*.py`

### Structure
- All tests use `pytest.mark.asyncio` for async support
- Mocks from `unittest.mock` (Mock, AsyncMock, MagicMock)
- Test classes group related tests

### Best Practices
- ✅ Use fixtures for common setup (e.g., `tmp_path`)
- ✅ Mock external dependencies (Discord API, file I/O)
- ✅ Test both success and error paths
- ✅ Keep tests isolated and independent
- ✅ Use descriptive test names

## 🛠️ Debugging Failed Tests

### View detailed output
```bash
pytest tests/test_name.py -vv -s
```

### Run specific test
```bash
pytest tests/test_name.py::TestClass::test_method -v
```

### Debug with pdb
```bash
pytest tests/test_name.py --pdb
```

## 📈 Coverage Improvements

Recent improvements:
- **Handler Coverage**: 96-98% → 100%
  - Fixed roles unchanged scenario in member.py
  - Fixed exception handling in role.py
- **BackupManager**: 71% → 88%
  - Added comprehensive edge case tests
  - Consolidated test functions for better organization
- **DateTime**: Fixed deprecation warning
  - Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`

## 🔧 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Install dependencies
pip install -e .
pip install pytest pytest-cov pytest-asyncio
```

**Async Warnings**
- Ensure all async tests have `@pytest.mark.asyncio`
- Check `pytest.ini` or `pyproject.toml` for asyncio configuration

**Coverage Not Showing**
- Use `--cov=securex` not `--cov=.`
- Ensure you're running from project root

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
