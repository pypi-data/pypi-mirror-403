# Result and Option Types

Neva uses `Result` and `Option` types for explicit error handling. Instead of raising exceptions that callers might forget to handle, functions return values that make success and failure states visible in the type system.

## The Option Type

`Option[T]` represents a value that may or may not exist. It has two variants:

- `Some(value)` — Contains a value
- `Nothing()` — Contains no value

```python
from neva import Some, Nothing, Option

def find_user(user_id: int) -> Option[User]:
    user = database.get(user_id)
    if user:
        return Some(user)
    return Nothing()
```

### Working with Option

**Pattern matching:**

```python
match find_user(123):
    case Some(user):
        print(f"Found: {user.name}")
    case Nothing():
        print("User not found")
```

**Unwrap with default:**

```python
user = find_user(123).unwrap_or(default_user)
```

**Transform the value:**

```python
# map: transform if Some, pass through Nothing
name = find_user(123).map(lambda u: u.name)  # Option[str]

# and_then: chain operations that return Option
email = find_user(123).and_then(lambda u: u.get_email())  # Option[str]
```

**Convert to Result:**

```python
# ok_or: convert Option to Result with an error message
result = find_user(123).ok_or("User not found")  # Result[User, str]
```

## The Result Type

`Result[T, E]` represents an operation that can succeed or fail. It has two variants:

- `Ok(value)` — Contains a success value of type `T`
- `Err(error)` — Contains an error value of type `E`

```python
from neva import Ok, Err, Result

def divide(a: float, b: float) -> Result[float, str]:
    if b == 0:
        return Err("Cannot divide by zero")
    return Ok(a / b)
```

### Working with Result

**Pattern matching:**

```python
match divide(10, 2):
    case Ok(value):
        print(f"Result: {value}")
    case Err(error):
        print(f"Error: {error}")
```

**Check the variant:**

```python
result = divide(10, 2)

if result.is_ok:
    print("Success!")

if result.is_err:
    print("Failed!")
```

**Extract values:**

```python
# unwrap: get value or raise UnwrapError
value = divide(10, 2).unwrap()  # 5.0
value = divide(10, 0).unwrap()  # raises UnwrapError

# unwrap_or: get value or use default
value = divide(10, 0).unwrap_or(0.0)  # 0.0

# unwrap_err: get error or raise UnwrapError
error = divide(10, 0).unwrap_err()  # "Cannot divide by zero"
```

## Transforming Results

### map

Transform the success value, leaving errors unchanged:

```python
result = divide(10, 2).map(lambda x: x * 2)
# Ok(10.0)

result = divide(10, 0).map(lambda x: x * 2)
# Err("Cannot divide by zero") — unchanged
```

### map_err

Transform the error value, leaving successes unchanged:

```python
result = divide(10, 0).map_err(lambda e: f"Math error: {e}")
# Err("Math error: Cannot divide by zero")
```

### and_then

Chain operations that return `Result`. If the first operation fails, the chain short-circuits:

```python
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"Invalid integer: {s}")

def safe_divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)

# Chain operations
result = (
    parse_int("10")
    .and_then(lambda a: parse_int("2").map(lambda b: (a, b)))
    .and_then(lambda pair: safe_divide(pair[0], pair[1]))
)
# Ok(5.0)

result = (
    parse_int("10")
    .and_then(lambda a: parse_int("zero").map(lambda b: (a, b)))
    .and_then(lambda pair: safe_divide(pair[0], pair[1]))
)
# Err("Invalid integer: zero") — short-circuited
```

## Common Patterns

### Early Return with Pattern Matching

```python
def process_order(order_id: str) -> Result[Receipt, str]:
    match find_order(order_id):
        case Err(e):
            return Err(e)
        case Ok(order):
            pass

    match validate_order(order):
        case Err(e):
            return Err(e)
        case Ok(validated):
            pass

    match charge_payment(validated):
        case Err(e):
            return Err(e)
        case Ok(receipt):
            return Ok(receipt)
```

### Collecting Results

When you have multiple operations that can fail:

```python
def process_all_users(user_ids: list[int]) -> Result[list[User], str]:
    users = []
    for user_id in user_ids:
        match find_user(user_id):
            case Ok(user):
                users.append(user)
            case Err(e):
                return Err(f"Failed to find user {user_id}: {e}")
    return Ok(users)
```

### Converting from Exceptions

Wrap code that might raise exceptions:

```python
def safe_json_parse(data: str) -> Result[dict, str]:
    try:
        return Ok(json.loads(data))
    except json.JSONDecodeError as e:
        return Err(f"Invalid JSON: {e}")
```

### Default Values with Context

```python
def get_config_value(key: str) -> str:
    return (
        Config.get(key)
        .map_err(lambda e: f"Config error for '{key}': {e}")
        .unwrap_or("default")
    )
```

## Usage in Neva

Throughout Neva, operations that can fail return `Result`:

**Service resolution:**

```python
service = app.make(MyService)  # Result[MyService, str]
```

**Configuration access:**

```python
value = Config.get("app.name")  # Result[Any, str]
```

**Service provider registration:**

```python
def register(self) -> Result[Self, str]:
    # Must return Ok(self) or Err("message")
```

## Why Not Exceptions?

Traditional exception handling has drawbacks:

1. **Hidden control flow**: Exceptions can be raised anywhere and caught anywhere, making code harder to follow
2. **Easy to forget**: Nothing in the type signature indicates a function can fail
3. **Broad catches**: `except Exception` catches everything, often hiding bugs

`Result` types make failure explicit:

```python
# With exceptions — caller might not know this can fail
def get_user(id: int) -> User:
    raise UserNotFoundError()

# With Result — failure is visible in the signature
def get_user(id: int) -> Result[User, str]:
    return Err("User not found")
```

## See Also

- [Dependency Injection](02-dependency-injection.md) — `make()` returns `Result`
- [Service Providers](03-service-providers.md) — `register()` returns `Result`
- [Facades](04-facades.md) — Many facade methods return `Result`
