# Python Code Style Guide

**Version:** 1.0  
**Based on:** UCS codebase patterns  
**Goal:** Clean, simple, easily maintainable, and super easy to read code

---

## Core Principles

1. **Simplicity over cleverness** – Write code that a junior developer can understand
2. **Explicit over implicit** – Don't hide behavior
3. **Flat is better than nested** – Avoid deep nesting
4. **One thing per function** – Small, focused functions
5. **Fail fast** – Validate early, raise exceptions immediately

---

## File Structure

Every Python file should follow this order:

```python
"""Module docstring - brief description of what this module does"""

# Standard library imports
import os
import sys
from typing import TYPE_CHECKING, Any, Optional

# Third-party imports
from nats.aio.client import Client

# Local imports
from ucs.config import DB_HOST
from ucs.error import ProcessingError
from ucs.utils import LOG_FAIL, log

if TYPE_CHECKING:
    from ucs import UCS

# Module-level constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module code (classes, functions)
```

---

## Naming Conventions

### Variables and Functions
```python
# snake_case for everything
user_id = 42
def get_user_by_id(user_id: int) -> dict:
    ...

# Descriptive but not verbose
# Good
connection_timeout = 30
user_count = len(users)

# Bad - too verbose
the_timeout_value_for_connection_in_seconds = 30
total_number_of_users_in_system = len(users)

# Bad - too cryptic
t = 30
uc = len(users)
```

### Classes
```python
# PascalCase for class names
class UserManager:
    ...

class NatsConnector:
    ...

class HTTPClient:  # Acronyms stay uppercase
    ...
```

### Constants
```python
# SCREAMING_SNAKE_CASE
LOG_FAIL = 0
LOG_WARN = 1
LOG_INFO = 2

MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30

# Event constants - use descriptive prefixes
EVENT_CALL_NEW = "call.new"
EVENT_CALL_HANGUP = "call.hangup"
EVENT_USER_LOGIN = "user.login"
```

### Private Members
```python
class Example:
    def __init__(self):
        self._internal_state = {}  # Single underscore for "internal use"
        self.__truly_private = []  # Double underscore only when necessary
    
    def _helper_method(self):
        """Internal method - not part of public API"""
        pass
```

---

## Type Hints

### Always use type hints for function signatures
```python
from typing import Any, Optional

def get_user(user_id: int) -> Optional[dict]:
    ...

def process_data(data: dict[str, Any], timeout: float = 1.0) -> bool:
    ...

def send_message(
    recipient: str,
    message: str,
    *,
    priority: int = 0,
    retry: bool = True,
) -> None:
    ...
```

### Use TYPE_CHECKING for circular imports
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ucs import UCS

class MyClass:
    def __init__(self, ucs: "UCS"):
        self.ucs = ucs
```

### Common type patterns
```python
from typing import Any, Callable, Optional
from collections.abc import Iterable

# Optional for nullable values
def find_user(user_id: int) -> Optional[dict]:
    ...

# Callable for callbacks
def register_handler(callback: Callable[[str, dict], None]) -> None:
    ...

# Use dict/list/tuple directly (Python 3.9+)
def process(items: list[str], config: dict[str, Any]) -> tuple[int, str]:
    ...
```

---

## Documentation

### Module Docstrings
```python
"""UCS Logger

Provides centralized logging with support for console, file, and syslog output.
"""
```

### Class Docstrings
```python
class NatsConnector:
    """NATS message bus connector
    
    Handles connection, subscription, and message publishing to NATS server.
    Supports automatic reconnection and JetStream key-value storage.
    """
```

### Function Docstrings
```python
def get_user(user_id: int) -> Optional[dict]:
    """Get user by ID
    
    Returns None if user doesn't exist.
    """
    ...

# For complex functions, add parameter descriptions
def create_backup(
    path: str,
    exclude: list[str],
    compress: bool = True,
) -> str:
    """Create system backup
    
    @param path: Destination path for backup file
    @param exclude: List of patterns to exclude
    @param compress: Whether to compress the backup
    @return: Path to created backup file
    """
    ...
```

---

## Class Design

### Constructor Pattern
```python
class UserService:
    """Service for user management"""
    
    def __init__(self, ucs: "UCS"):
        self.ucs = ucs
        self.db = ucs.db
        self.log = ucs.log
        
        # Initialize internal state
        self._cache: dict[int, dict] = {}
        self._loaded = False
        
        # Load data if needed
        self.load()
    
    def load(self) -> None:
        """Load users from database"""
        ...
    
    def start(self) -> None:
        """Start service (called by UCS on startup)"""
        pass
    
    def stop(self) -> None:
        """Stop service (called by UCS on shutdown)"""
        pass
```

### Method Organization
```python
class Example:
    # 1. __init__ first
    def __init__(self):
        ...
    
    # 2. Public methods
    def get(self, key: str) -> Any:
        ...
    
    def set(self, key: str, value: Any) -> None:
        ...
    
    # 3. Private/internal methods
    def _validate(self, data: dict) -> bool:
        ...
    
    def _cleanup(self) -> None:
        ...
    
    # 4. Magic methods last (if any)
    def __getitem__(self, key: str) -> Any:
        ...
```

---

## Error Handling

### Custom Exception Hierarchy
```python
class UCSException(Exception):
    """Base exception for all UCS errors"""
    
    def __init__(self, message: str = "Internal server error", code: int = -1000):
        super().__init__(message)
        self.message = message
        self.code = code


class UnknownKey(UCSException):
    """Unknown key/ID requested"""
    
    def __init__(self, message: str = "Unknown key"):
        super().__init__(message, code=-4)


class PermissionDenied(UCSException):
    """Permission denied for operation"""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code=-1)
```

### Exception Chaining
```python
# Always chain exceptions to preserve context
try:
    data = self.db.get(user_id)
except KeyError as error:
    raise UnknownKey(f"User {user_id} not found") from error
```

### Guard Clauses
```python
# Good - fail fast with guard clauses
def process_user(user_id: int, data: dict) -> dict:
    if not user_id:
        raise ValueError("user_id is required")
    
    if not data:
        raise ValueError("data cannot be empty")
    
    user = self.get_user(user_id)
    if not user:
        raise UnknownKey(f"User {user_id} not found")
    
    # Main logic here
    return self._do_process(user, data)

# Bad - deep nesting
def process_user(user_id: int, data: dict) -> dict:
    if user_id:
        if data:
            user = self.get_user(user_id)
            if user:
                return self._do_process(user, data)
            else:
                raise UnknownKey()
        else:
            raise ValueError()
    else:
        raise ValueError()
```

---

## Logging

### Log Levels
```python
LOG_DEV = -1   # Development only (never in production)
LOG_FAIL = 0   # Errors that need attention
LOG_WARN = 1   # Warnings - something unexpected but handled
LOG_INFO = 2   # Important information
LOG_DBUG = 3   # Debug details
LOG_PROT = 4   # Protocol/communication details
```

### Logging Patterns
```python
# Use log level appropriate methods
self.log.fail("Critical error: %s", error)
self.log.warn("Connection retry %d/%d", attempt, max_retries)
self.log.info("User %s logged in", username)
self.log.dbug("Processing data: %s", data)

# Include context in log messages
self.log.info("Connected to NATS on: %s", self._url)
self.log.warn('Unknown SSO provider ID %s', sso_id)

# For exceptions, use trace
try:
    risky_operation()
except Exception:
    self.log.trace()
```

---

## Constants and Enums

### Constants with Enums Pattern
```python
# Define constant values
AGENT_OFFLINE = 0
AGENT_READY = 1
AGENT_ACW = 2
AGENT_AUX = 3

# Create enum tuple for UI/API
AGENT_STATUS_ENUM = (
    (AGENT_OFFLINE, "Offline"),
    (AGENT_READY, "Ready"),
    (AGENT_ACW, "ACW"),
    (AGENT_AUX, "AUX"),
)
```

### Using Python Enums
```python
from enum import IntEnum, StrEnum

class InteractionType(IntEnum):
    """Contact centre interaction channel type"""
    
    CALL = 1
    SMS = 2
    MAIL = 3
    
    def __str__(self) -> str:
        descriptions = {
            InteractionType.CALL: "call",
            InteractionType.SMS: "SMS",
            InteractionType.MAIL: "e-mail",
        }
        return descriptions.get(self.value, str(self.value))


class AclPermission(StrEnum):
    """Access Control List permissions"""
    
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
```

---

## Function Design

### Keep Functions Small and Focused
```python
# Good - each function does one thing
def get_user(user_id: int) -> Optional[dict]:
    """Get user by ID"""
    return self._users.get(user_id)

def validate_user(user: dict) -> bool:
    """Validate user data"""
    return bool(user.get("name") and user.get("email"))

def save_user(user: dict) -> dict:
    """Save user to database"""
    return self.db.insert("users", user, returning="*").dict(0)

# Bad - function does too many things
def get_validate_and_save_user(user_id: int, data: dict) -> dict:
    user = self._users.get(user_id)
    if not user:
        raise UnknownKey()
    if not data.get("name"):
        raise ValueError()
    user.update(data)
    return self.db.update("users", user, {"id": user_id}).dict(0)
```

### Use Keyword-Only Arguments for Clarity
```python
def create_client(
    url: str,
    *,  # Everything after this must be keyword argument
    timeout: float = 1.0,
    retry: bool = True,
    log_body: bool = False,
) -> Client:
    ...

# Usage is explicit and readable
client = create_client(
    "https://api.example.com",
    timeout=5.0,
    retry=False,
)
```

### Return Early, Don't Nest
```python
# Good
def process(data: dict) -> Optional[str]:
    if not data:
        return None
    
    if "id" not in data:
        return None
    
    return self._transform(data)

# Bad
def process(data: dict) -> Optional[str]:
    result = None
    if data:
        if "id" in data:
            result = self._transform(data)
    return result
```

---

## Async Code

### Async/Await Patterns
```python
async def connect(self) -> None:
    """Create connection to message bus"""
    self.log.info("Connecting to %s...", self._url)
    
    await self._connection.connect(
        self._url,
        name=f"service@{socket.getfqdn()}",
        max_reconnect_attempts=-1,
        reconnected_cb=self._on_reconnected,
        error_cb=self._on_error,
    )
    
    await self._subscribe_all()
    self.log.info("Connected to %s", self._url)


async def _on_message(self, msg: Msg) -> None:
    """Handle incoming message"""
    data = fromJSON(msg.data)
    
    if msg.reply:
        asyncio.create_task(self._handle_rpc(msg, data))
        return
    
    self._notify(msg.subject, data)
```

### Bridging Sync and Async
```python
def request(self, subject: str, *args, **kwargs) -> Any:
    """Call async NATS request from sync code"""
    timeout = kwargs.pop("timeout", 2)
    return self._ucs.await_coroutine(
        self._async_request(subject, args, kwargs),
        timeout=timeout,
    )
```

---

## Database Operations

### SQL Query Patterns
```python
# Simple select
users = self.db.select("*", "users", {"active": True}).dict()

# With specific columns
user = self.db.select("id, name, email", "users", {"id": user_id}).dict(0)

# Insert with returning
new_user = self.db.insert("users", data, returning="*").dict(0)

# Update with returning
updated = self.db.update(
    "users",
    {"name": new_name},
    where={"id": user_id},
    returning="*",
).dict(0)

# Delete
self.db.delete("users", where={"id": user_id})
```

---

## API Methods

### API Method Pattern
```python
def getUser(self, user: UserSerialized, user_id: int) -> dict:
    """Get user by ID"""
    _ = user["_"]  # Translation function
    
    # Permission check
    if not user["is_super"]:
        if not self.ucs.tree.checkGroupAccess(user["id"], target_group_id):
            raise PermissionDenied(_("Permission denied"))
    
    # Business logic
    result = self.ucs.users.get(user_id)
    if not result:
        raise UnknownKey(_("User not found"))
    
    return result

# API metadata
getUser._xmlrpc = "user.get"
getUser._input = (User(), Int("user ID"))
getUser._output = Array("user data", Int("status"), UserStruct)
```

---

## Import Organization

```python
# 1. Standard library (alphabetical)
import asyncio
import os
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

# 2. Third-party packages (alphabetical)
from nats.aio.client import Client
from nats.aio.msg import Msg

# 3. Local imports - absolute (alphabetical)
from ucs.config import DB_HOST, DB_PORT
from ucs.constants import AGENT_READY, AGENT_OFFLINE
from ucs.error import ProcessingError, UnknownKey
from ucs.utils import LOG_FAIL, log, trace

# 4. TYPE_CHECKING imports (for avoiding circular imports)
if TYPE_CHECKING:
    from ucs import UCS
    from ucs.tree.user import UserSerialized
```

---

## Code Formatting

### Line Length
- Maximum 120 characters
- Break long lines at logical points

### String Formatting
```python
# Use f-strings for simple cases
message = f"User {user_id} not found"

# Use % formatting for log messages (lazy evaluation)
self.log.info("Processing user %s", user_id)

# Use .format() or f-strings for complex templates
template = "Error in {module}.{function}: {message}"
result = template.format(module="users", function="get", message=error)
```

### Multi-line Structures
```python
# Function calls
result = some_function(
    first_argument,
    second_argument,
    keyword_arg=value,
)

# Lists and dicts
config = {
    "host": "localhost",
    "port": 5432,
    "timeout": 30,
}

items = [
    "first_item",
    "second_item",
    "third_item",
]

# Conditionals
if (
    condition_one
    and condition_two
    and condition_three
):
    do_something()
```

---

## Common Patterns

### Safe JSON Operations
```python
def fromJSON(data: str, fallback: Any = None) -> Any:
    """Safely deserialize JSON"""
    try:
        return json.loads(data)
    except Exception:
        return fallback

def toJSON(data: Any, fallback: Any = None) -> str:
    """Safely serialize to JSON"""
    try:
        return json.dumps(data, cls=DecimalEncoder)
    except Exception:
        return json.dumps(fallback)
```

### Safe Type Conversion
```python
def toInt(data: Any, fallback: int = None) -> Optional[int]:
    """Safely convert to integer"""
    if data is None:
        return fallback
    try:
        return int(data)
    except Exception:
        return fallback
```

### Context Managers for Resources
```python
class TimeoutLock:
    """Lock with timeout support"""
    
    def __init__(self, lock: Lock = None, timeout: float = 0.1):
        self.lock = lock or Lock()
        self.timeout = timeout
    
    def __enter__(self):
        if not self.lock.acquire(timeout=self.timeout):
            raise TimeoutError("Unable to acquire lock")
        return self
    
    def __exit__(self, *args):
        self.lock.release()
```

---

## Testing Considerations

- Write code that's easy to test
- Use dependency injection
- Avoid global state
- Keep functions pure when possible
- Mock external dependencies

---

## Tools and Linting

### Recommended Tools
- **ruff** - Fast linter and formatter
- **mypy** - Static type checking
- **pytest** - Testing framework

### Ruff Configuration
```toml
[tool.ruff]
line-length = 120
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = ["E501"]  # Line too long (handled by formatter)
```

---

## Quick Reference

| Item | Convention | Example |
|------|------------|---------|
| Variables | snake_case | `user_id`, `connection_timeout` |
| Functions | snake_case | `get_user()`, `process_data()` |
| Classes | PascalCase | `UserManager`, `NatsConnector` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRIES`, `LOG_FAIL` |
| Private | _single_underscore | `_internal_state`, `_helper()` |
| Modules | snake_case | `user_service.py`, `nats_connector.py` |

---

## Final Notes

**Remember:**
- Code is read more than written
- Optimize for readability first
- When in doubt, be explicit
- Consistency matters more than any single rule
- If a pattern doesn't fit, document why you deviated
