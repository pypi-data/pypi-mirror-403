# Pydantic Types

[![Test](https://github.com/yukihiko-shinoda/pydantic-types/workflows/Test/badge.svg)](https://github.com/yukihiko-shinoda/pydantic-types/actions?query=workflow%3ATest)
[![CodeQL](https://github.com/yukihiko-shinoda/pydantic-types/workflows/CodeQL/badge.svg)](https://github.com/yukihiko-shinoda/pydantic-types/actions?query=workflow%3ACodeQL)
[![Code Coverage](https://qlty.sh/gh/yukihiko-shinoda/projects/pydantic-types/coverage.svg)](https://qlty.sh/gh/yukihiko-shinoda/projects/pydantic-types)
[![Maintainability](https://qlty.sh/badges/11a7c146-f6ee-4d74-8b63-2d2e963ef988/maintainability.svg)](https://qlty.sh/gh/yukihiko-shinoda/projects/pydantic-types)
[![Dependabot](https://flat.badgen.net/github/dependabot/yukihiko-shinoda/pydantic-types?icon=dependabot)](https://github.com/yukihiko-shinoda/pydantic-types/security/dependabot)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pydantictypes)](https://pypi.org/project/pydantictypes)
[![Twitter URL](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Fyukihiko-shinoda%2Fpydantic-types)](http://twitter.com/share?text=Pydantic%20Types&url=https://pypi.org/project/pydantictypes/&hashtags=python)

Common used type definitions with Pydantic.

## Advantage

- Out of the box

### Out of the box

You don't need to define customized types for common use cases. This package provides a set of commonly used types that can be directly imported and used in your Pydantic models.

## Quickstart

```bash
pip install pydantictypes
```

## Supported Types

| Category | Type | Description |
|----------|------|-------------|
| **Integer Conversion** | `ConstrainedStringToOptionalInt` | String to optional int |
| | `StrictStringWithCommaToInt` | String with comma ("1,000") to int |
| | `StrictStringWithCommaToOptionalInt` | String with comma to optional int |
| | `StrictKanjiYenStringToInt` | Japanese yen string ("1,000円") to int |
| | `StrictSymbolYenStringToInt` | Backslash yen string ("\\1,000") to int |
| **String Validation** | `HalfWidthString` | Validates half-width characters only |
| | `OptionalHalfWidthString` | Optional half-width string |
| | `ConstrainedStringWithLength` | String with length constraints |
| | `ConstrainedOptionalStringWithLength` | Optional string with length constraints |
| | `StringToOptionalStr` | Optional string with transformations |
| **Boolean Conversion** | `StringToBoolean` | Flag enum for "1"/"0" strings |
| | `StringToOptionalBool` | String ("1", "0", "") to optional bool |
| **DateTime Conversion** | `StringSlashToDateTime` | "YYYY/MM/DD" to datetime |
| | `StringSlashMonthDayOnlyToDatetime` | "MM/DD" to datetime |
| **Special** | `EmptyStringToNone` | Empty string to None |

### Constraint Functions

These functions create types with numeric or length constraints:

| Function | Description |
|----------|-------------|
| `constringtooptionalint(ge=, le=, gt=, lt=, multiple_of=)` | Create constrained optional int type |
| `constringwithcommatooptionalint(ge=, le=, gt=, lt=, multiple_of=)` | Create constrained optional int type (with comma support) |
| `constrained_string(min_length=, max_length=, equal_to=)` | Create string with length constraints |
| `constrained_optional_string(min_length=, max_length=, equal_to=)` | Create optional string with length constraints |
| `constringtooptionalstr(min_length=, max_length=, regex=, ...)` | Create optional string with various constraints |

## API

### Integer Conversion Types

#### ConstrainedStringToOptionalInt

```python
from pydantictypes import ConstrainedStringToOptionalInt
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    optional_int: ConstrainedStringToOptionalInt

# Successful conversions:
model1 = MyModel(optional_int="123")     # Result: model1.optional_int = 123
model2 = MyModel(optional_int="0")       # Result: model2.optional_int = 0
model3 = MyModel(optional_int="")        # Result: model3.optional_int = None
model4 = MyModel(optional_int=None)      # Result: model4.optional_int = None

# These inputs raise ValidationError:
try:
    MyModel(optional_int="1,000")        # Commas not supported
except ValidationError:
    pass
```

#### constringtooptionalint (with constraints)

```python
from pydantictypes import constringtooptionalint
from pydantic import BaseModel, ValidationError

# Create a type with constraints
Optional10Digits = constringtooptionalint(ge=0, le=9999999999)

class MyModel(BaseModel):
    value: Optional10Digits

# Successful conversions:
model1 = MyModel(value="1234567890")     # Result: model1.value = 1234567890
model2 = MyModel(value="")               # Result: model2.value = None

# Constraint violations raise ValidationError:
try:
    MyModel(value="10000000000")         # Exceeds le=9999999999
except ValidationError:
    pass

try:
    MyModel(value="-1")                  # Less than ge=0
except ValidationError:
    pass
```

#### StrictStringWithCommaToInt

```python
from pydantictypes import StrictStringWithCommaToInt
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    number: StrictStringWithCommaToInt

# Successful conversions:
model1 = MyModel(number="1")             # Result: model1.number = 1
model2 = MyModel(number="1,000")         # Result: model2.number = 1000
model3 = MyModel(number="1,000,000")     # Result: model3.number = 1000000

# These inputs raise ValidationError:
try:
    MyModel(number="1.0")                # Decimals not supported
except ValidationError:
    pass
```

#### StrictStringWithCommaToOptionalInt

```python
from pydantictypes import StrictStringWithCommaToOptionalInt
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    optional_number: StrictStringWithCommaToOptionalInt

# Successful conversions:
model1 = MyModel(optional_number="1")           # Result: model1.optional_number = 1
model2 = MyModel(optional_number="1,000")       # Result: model2.optional_number = 1000
model3 = MyModel(optional_number="")            # Result: model3.optional_number = None
model4 = MyModel(optional_number=None)          # Result: model4.optional_number = None

# These inputs raise ValidationError:
try:
    MyModel(optional_number="1.0")              # Decimals not supported
except ValidationError:
    pass
```

#### constringwithcommatooptionalint (with constraints)

```python
from pydantictypes import constringwithcommatooptionalint
from pydantic import BaseModel, ValidationError

# Create a type with constraints
BoundedNumber = constringwithcommatooptionalint(ge=0, le=1000000, multiple_of=100)

class MyModel(BaseModel):
    amount: BoundedNumber

# Successful conversions:
model1 = MyModel(amount="1,000")         # Result: model1.amount = 1000
model2 = MyModel(amount="500,000")       # Result: model2.amount = 500000
model3 = MyModel(amount="")              # Result: model3.amount = None

# Constraint violations raise ValidationError:
try:
    MyModel(amount="1,500")              # Not a multiple of 100
except ValidationError:
    pass
```

#### StrictKanjiYenStringToInt

```python
from pydantictypes import StrictKanjiYenStringToInt
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    price: StrictKanjiYenStringToInt

# Successful conversions:
model1 = MyModel(price="1円")           # Result: model1.price = 1
model2 = MyModel(price="1,000円")       # Result: model2.price = 1000
model3 = MyModel(price="1,000,000円")   # Result: model3.price = 1000000

# These inputs raise ValidationError:
try:
    MyModel(price="1.0円")      # Decimals not supported
except ValidationError:
    pass

try:
    MyModel(price="1000")       # Missing 円 character
except ValidationError:
    pass
```

#### StrictSymbolYenStringToInt

```python
from pydantictypes import StrictSymbolYenStringToInt
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    price: StrictSymbolYenStringToInt

# Successful conversions:
model1 = MyModel(price=r"\1")           # Result: model1.price = 1
model2 = MyModel(price=r"\1,000")       # Result: model2.price = 1000
model3 = MyModel(price=r"\1,000,000")   # Result: model3.price = 1000000

# These inputs raise ValidationError:
try:
    MyModel(price=r"\1.0")              # Decimals not supported
except ValidationError:
    pass

try:
    MyModel(price="$1")                 # Dollar symbol not supported
except ValidationError:
    pass
```

### String Validation Types

#### HalfWidthString / OptionalHalfWidthString

```python
from pydantictypes import HalfWidthString, OptionalHalfWidthString
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    code: HalfWidthString
    optional_code: OptionalHalfWidthString

# Successful conversions:
model1 = MyModel(code="ABC123", optional_code="XYZ")
model2 = MyModel(code="hello", optional_code="")      # optional_code = None
model3 = MyModel(code="test", optional_code=None)     # optional_code = None

# These inputs raise ValidationError:
try:
    MyModel(code="ABC", optional_code=None)         # Full-width characters not allowed
except ValidationError:
    pass
```

#### constrained_string / constrained_optional_string

```python
from pydantictypes import constrained_string, constrained_optional_string
from pydantic import BaseModel, ValidationError

# Create types with length constraints
Code5Chars = constrained_string(equal_to=5)
Name = constrained_optional_string(min_length=1, max_length=50)

class MyModel(BaseModel):
    code: Code5Chars
    name: Name

# Successful conversions:
model1 = MyModel(code="ABCDE", name="John")
model2 = MyModel(code="12345", name="")           # name = None

# These inputs raise ValidationError:
try:
    MyModel(code="ABC", name="John")              # code length != 5
except ValidationError:
    pass
```

#### StringToOptionalStr / constringtooptionalstr

```python
from pydantictypes import StringToOptionalStr, constringtooptionalstr
from pydantic import BaseModel, ValidationError

# Create type with transformations and constraints
TrimmedLowerName = constringtooptionalstr(
    strip_whitespace=True,
    to_lower=True,
    min_length=1,
    max_length=100,
    regex=r"^[a-z\s]+$"
)

class MyModel(BaseModel):
    name: TrimmedLowerName

# Successful conversions:
model1 = MyModel(name="  JOHN DOE  ")     # Result: model1.name = "john doe"
model2 = MyModel(name="")                  # Result: model2.name = None

# These inputs raise ValidationError:
try:
    MyModel(name="John123")               # Contains numbers (regex mismatch)
except ValidationError:
    pass
```

### Boolean Conversion Types

#### StringToBoolean / StringToOptionalBool

```python
from pydantictypes import StringToBoolean, StringToOptionalBool
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    is_active: StringToOptionalBool

# Successful conversions:
model1 = MyModel(is_active="1")      # Result: model1.is_active = StringToBoolean.TRUE
model2 = MyModel(is_active="0")      # Result: model2.is_active = StringToBoolean.FALSE
model3 = MyModel(is_active="")       # Result: model3.is_active = None

# String representation:
print(str(model1.is_active))         # Output: "1"
print(str(model2.is_active))         # Output: "0"

# These inputs raise ValidationError:
try:
    MyModel(is_active="true")        # Must be "1", "0", or ""
except ValidationError:
    pass
```

### DateTime Conversion Types

#### StringSlashToDateTime

```python
from pydantictypes import StringSlashToDateTime
from pydantic import BaseModel, ValidationError
import datetime

class MyModel(BaseModel):
    date: StringSlashToDateTime

# Successful conversions:
model1 = MyModel(date="2020/01/01")   # Result: model1.date = datetime.datetime(2020, 1, 1, 0, 0)
model2 = MyModel(date="2020/12/31")   # Result: model2.date = datetime.datetime(2020, 12, 31, 0, 0)
model3 = MyModel(date="2020/02/29")   # Result: model3.date = datetime.datetime(2020, 2, 29, 0, 0)

# These inputs raise ValidationError:
try:
    MyModel(date="2020/02/30")        # Invalid date
except ValidationError:
    pass

try:
    MyModel(date="2020-01-01")        # Wrong format (uses hyphens)
except ValidationError:
    pass
```

#### StringSlashMonthDayOnlyToDatetime

```python
from pydantictypes import StringSlashMonthDayOnlyToDatetime
from pydantic import BaseModel, ValidationError
import datetime

class MyModel(BaseModel):
    date: StringSlashMonthDayOnlyToDatetime

# Successful conversions:
model1 = MyModel(date="01/01")    # Result: model1.date = datetime.datetime(1904, 1, 1, 0, 0)
model2 = MyModel(date="12/31")    # Result: model2.date = datetime.datetime(1904, 12, 31, 0, 0)
model3 = MyModel(date="02/29")    # Result: model3.date = datetime.datetime(1904, 2, 29, 0, 0)

# These inputs raise ValidationError:
try:
    MyModel(date="01/32")         # Invalid day
except ValidationError:
    pass

try:
    MyModel(date="2020/01/01")    # Wrong format (includes year)
except ValidationError:
    pass
```

### Special Types

#### EmptyStringToNone

```python
from pydantictypes import EmptyStringToNone
from pydantic import BaseModel, ValidationError

class MyModel(BaseModel):
    empty_field: EmptyStringToNone

# Successful conversion:
model1 = MyModel(empty_field="")      # Result: model1.empty_field = None

# These inputs raise ValidationError:
try:
    MyModel(empty_field="not empty")  # Only empty string allowed
except ValidationError:
    pass

try:
    MyModel(empty_field=None)         # Must be a string
except ValidationError:
    pass
```

## Credits

This package was created with [Cookiecutter] and the [yukihiko-shinoda/cookiecutter-pypackage] project template.

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[yukihiko-shinoda/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
