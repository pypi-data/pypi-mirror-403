# ETL Transformation Guide

The ETL orchestrator supports three levels of transformation complexity, applied in order:

1. **Simple Operations** (declarative, easy to use)
2. **JSONata** (powerful query language for complex transformations)
3. **Custom Functions** (Python functions for advanced logic)

## Transformation Pipeline Order

```
Raw Data → Simple Operations → JSONata → Custom Functions → Transformed Data
```

Each step is optional and can be used independently or together.

## 1. Simple Operations (Recommended for Most Use Cases)

Simple, declarative operations that handle 90% of transformation needs.

### Configuration Format

You can use either the **new format** (grouped under `transform:`) or **legacy format** (top-level keys):

**New Format (Recommended):**
```yaml
transform:
  rename:
    oldName: new_name
    camelCase: snake_case
  convert:
    price: float
    quantity: integer
  defaults:
    status: "pending"
  add:
    full_name: "${first_name} ${last_name}"
    created_at: "now()"
  select:
    - field1
    - field2
  drop:
    - internal_id
```

**Legacy Format (Backward Compatible):**
```yaml
rename:
  oldName: new_name
convert:
  price: float
defaults:
  status: "pending"
```

### Available Operations

#### 1. `rename` - Rename Fields

Maps old field names to new field names.

```yaml
rename:
  oldName: new_name
  camelCase: snake_case
  userId: user_id
```

**Example:**
```python
# Input
[{"oldName": "test", "camelCase": "value"}]

# Output
[{"new_name": "test", "snake_case": "value"}]
```

#### 2. `convert` - Type Conversion

Converts field types automatically.

**Supported types:**
- `string` / `str`
- `integer` / `int`
- `float` / `number` / `numeric`
- `boolean` / `bool`
- `datetime`
- `date`

```yaml
convert:
  price: float
  quantity: integer
  active: boolean
  created_at: datetime
  birth_date: date
```

**Example:**
```python
# Input
[{"price": "10.5", "quantity": "5", "active": "true"}]

# Output
[{"price": 10.5, "quantity": 5, "active": True}]
```

#### 3. `defaults` - Default Values

Sets default values for missing or null fields.

```yaml
defaults:
  status: "pending"
  priority: 0
  category: "uncategorized"
```

**Example:**
```python
# Input
[{"name": "test"}, {"name": "test2", "status": "active"}]

# Output
[{"name": "test", "status": "pending"}, {"name": "test2", "status": "active"}]
```

#### 4. `add` - Add Computed Fields

Adds new fields with computed values.

**Supported expressions:**
- Field references: `"${field_name}"`
- String concatenation: `"${first_name} ${last_name}"`
- Functions: `"now()"`, `"uuid()"`
- Literal values: `"static_value"`

```yaml
add:
  full_name: "${first_name} ${last_name}"
  created_at: "now()"
  record_id: "uuid()"
  source: "api"
```

**Example:**
```python
# Input
[{"first_name": "John", "last_name": "Doe"}]

# Output
[{
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "created_at": "2024-01-01T12:00:00",
  "record_id": "123e4567-e89b-12d3-a456-426614174000",
  "source": "api"
}]
```

#### 5. `select` - Keep Only Specified Fields

Keeps only the specified fields (removes all others).

```yaml
select:
  - field1
  - field2
  - field3
```

**Example:**
```python
# Input
[{"field1": "a", "field2": "b", "field3": "c", "unwanted": "x"}]

# Output
[{"field1": "a", "field2": "b", "field3": "c"}]
```

#### 6. `drop` - Remove Specified Fields

Removes specified fields (keeps all others).

```yaml
drop:
  - internal_id
  - debug_info
  - temp_field
```

**Example:**
```python
# Input
[{"name": "test", "internal_id": "123", "debug_info": "x"}]

# Output
[{"name": "test"}]
```

### Operation Order

Operations are applied in this order:
1. `rename`
2. `convert`
3. `defaults`
4. `add`
5. `select`
6. `drop`

### Complete Example

```yaml
# transform.yaml
transform:
  rename:
    userId: user_id
    firstName: first_name
    lastName: last_name
  convert:
    age: integer
    price: float
    active: boolean
  defaults:
    status: "pending"
    priority: 0
  add:
    full_name: "${first_name} ${last_name}"
    created_at: "now()"
    record_id: "uuid()"
  drop:
    - internal_id
    - debug_info
```

## 2. JSONata (Advanced Transformations)

JSONata is a powerful query and transformation language for JSON data. Use it when simple operations aren't sufficient.

### Configuration

```yaml
jsonata:
  expression: |
    $.{
      "ticker": symbol,
      "avg_price": $average(prices),
      "total_volume": $sum(volumes),
      "price_change": price - previousClose
    }
  mode: "batch"  # or "record"
```

### Mode Options

- **`batch`**: Apply expression to entire dataset
- **`record`**: Apply expression to each record individually

### JSONata Examples

**Simple rename and calculation:**
```yaml
jsonata:
  expression: |
    $.{
      "ticker": symbol,
      "price_change": price - previousClose,
      "price_change_pct": ((price - previousClose) / previousClose) * 100
    }
  mode: "record"
```

**Aggregation:**
```yaml
jsonata:
  expression: |
    {
      "total_records": $count($),
      "avg_price": $average($.price),
      "max_price": $max($.price),
      "min_price": $min($.price)
    }
  mode: "batch"
```

**Filtering:**
```yaml
jsonata:
  expression: |
    $[price > 100]
  mode: "record"
```

**Nested transformations:**
```yaml
jsonata:
  expression: |
    $.{
      "user": {
        "id": userId,
        "name": userName
      },
      "metadata": {
        "created": created_at,
        "updated": updated_at
      }
    }
  mode: "record"
```

### JSONata Resources

- [JSONata Documentation](https://docs.jsonata.org/)
- [JSONata Playground](https://try.jsonata.org/)

## 3. Custom Functions (Python Code)

For complex business logic that can't be expressed declaratively, use custom Python functions.

### Configuration

```yaml
custom_function:
  module: "myproject.transforms"
  function: "optimize_data"
  mode: "batch"  # or "record"
  kwargs:
    method: "min_volatility"
    solver: "ipopt"
```

**Alternative format (using callable path):**
```yaml
custom_function:
  callable: "myproject.transforms.optimize_portfolio"
  mode: "batch"
```

### Function Signature

**Batch mode:**
```python
def my_transform(data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    # Process entire dataset
    return transformed_data
```

**Record mode:**
```python
def my_transform(record: Dict[str, Any], **kwargs) -> Optional[Dict[str, Any]]:
    # Process single record
    return transformed_record  # or None to skip
```

### Example Custom Function

```python
# myproject/transforms.py
def calculate_metrics(data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    """Calculate additional metrics for each record."""
    result = []
    for record in data:
        record['total_value'] = record.get('price', 0) * record.get('quantity', 0)
        record['discount_applied'] = record.get('price', 0) < record.get('original_price', 0)
        result.append(record)
    return result
```

**Usage in transform.yaml:**
```yaml
custom_function:
  module: "myproject.transforms"
  function: "calculate_metrics"
  mode: "batch"
```

### Class-Based Functions

If your function is a class, PyCharter will automatically detect and use:
- `optimize()` method
- `run()` method
- `__call__()` method

```python
# myproject/transforms.py
class PortfolioOptimizer:
    def optimize(self, data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        # Optimization logic
        return optimized_data
```

**Usage:**
```yaml
custom_function:
  module: "myproject.transforms"
  function: "PortfolioOptimizer"
  mode: "batch"
  kwargs:
    method: "min_volatility"
```

## Combining All Three

You can use simple operations, JSONata, and custom functions together:

```yaml
# transform.yaml

# Step 1: Simple operations
transform:
  rename:
    oldName: new_name
  convert:
    price: float
  defaults:
    status: "pending"

# Step 2: JSONata (applied after simple operations)
jsonata:
  expression: |
    $.{
      "calculated_field": price * quantity,
      "formatted_date": $fromMillis(timestamp)
    }
  mode: "record"

# Step 3: Custom function (applied last)
custom_function:
  module: "myproject.transforms"
  function: "final_validation"
  mode: "batch"
```

## Best Practices

1. **Start Simple**: Use simple operations for basic transformations
2. **Use JSONata for Complex Logic**: When you need aggregations, filtering, or complex calculations
3. **Use Custom Functions Sparingly**: Only for business logic that can't be expressed declaratively
4. **Test Incrementally**: Test each transformation step separately
5. **Document Complex Expressions**: Add comments explaining complex JSONata expressions

## Error Handling

- **Missing Fields**: Warnings are logged, transformation continues
- **Type Conversion Failures**: Original value is kept, warning is logged
- **JSONata Errors**: Transformation fails with clear error message
- **Custom Function Errors**: Transformation fails with function error details

## Examples

See `data/stock_examples/` for real-world examples of transformation configurations.
