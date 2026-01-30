# Design Principles

> Core principles guiding architecture and code design.

---

## 1. SSOT (Single Source of Truth)

### Principle
Each piece of data should have one authoritative source.

### Application

```python
# ❌ Wrong - multiple config sources
class ComponentA:
    config = yaml.load(open("config.yaml"))

class ComponentB:
    config = yaml.load(open("config.yaml"))

# ✅ Correct - single config manager
class ConfigManager:
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls._load_config()
        return cls._instance

# All components use
config = ConfigManager.get()
```

---

## 2. Dependency Injection

### Principle
Dependencies should be injected, not created internally.

### Application

```python
# ❌ Wrong - hard dependency
class UserService:
    def __init__(self):
        self.db = PostgresDB()  # Hard to test

# ✅ Correct - dependency injection
class UserService:
    def __init__(self, db: Database):
        self.db = db

# Usage
service = UserService(db=PostgresDB())
# Testing
test_service = UserService(db=MockDB())
```

---

## 3. Simplicity First

### Principle
Choose the simplest solution that works. Don't over-engineer.

### Guidelines
- Start with the simplest implementation
- Add complexity only when needed
- Refactor when patterns emerge

```python
# ❌ Over-engineered for simple case
class UserRepositoryFactoryBuilder:
    def build_factory(self):
        return UserRepositoryFactory()

# ✅ Simple and direct
def get_user(user_id: int) -> User:
    return db.query(User).get(user_id)
```

---

## 4. Separation of Concerns

### Principle
Each module/function should have one responsibility.

### Application

```python
# ❌ Mixed concerns
def process_order(order_data):
    # Validation
    if not order_data.get('items'):
        raise ValueError("No items")
    # Business logic
    total = sum(item['price'] for item in order_data['items'])
    # Persistence
    db.save(Order(total=total))
    # Notification
    email.send(order_data['email'], "Order confirmed")

# ✅ Separated concerns
def validate_order(order_data):
    if not order_data.get('items'):
        raise ValueError("No items")

def calculate_total(items):
    return sum(item['price'] for item in items)

def save_order(order):
    return db.save(order)

def notify_customer(email, order):
    email_service.send(email, "Order confirmed")
```

---

## 5. Fail Fast

### Principle
Detect and report errors as early as possible.

### Application

```python
# ❌ Late failure
def process_file(path):
    content = open(path).read()  # May fail late
    # ... 100 lines of processing ...
    return result

# ✅ Fail fast
def process_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.suffix == '.txt':
        raise ValueError(f"Expected .txt file, got: {path.suffix}")
    
    content = path.read_text(encoding='utf-8')
    # ... processing ...
```

---

## 6. Interface Segregation

### Principle
Clients should not depend on interfaces they don't use.

### Application

```python
# ❌ Fat interface
class Repository:
    def find(self, id): ...
    def find_all(self): ...
    def save(self, entity): ...
    def delete(self, id): ...
    def export_to_csv(self): ...  # Not all repos need this

# ✅ Segregated interfaces
class Readable:
    def find(self, id): ...
    def find_all(self): ...

class Writable:
    def save(self, entity): ...
    def delete(self, id): ...

class Exportable:
    def export_to_csv(self): ...

class UserRepository(Readable, Writable):
    ...
```

---

*This file is a generic engine rule, must not contain any project-specific information*
*Protocol version: 2.1.0*
