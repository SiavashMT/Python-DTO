# Python-DTO
[![Build Status](https://travis-ci.org/SiavashMT/Python-DTO.svg?branch=master)](https://travis-ci.org/SiavashMT/Python-DTO)

Simple implementation of Data Transfer Object (DTO) in Python. 

With Python-DTO you can make Immutable/Mutable (or partially mutable - i.e. attribute level control) DTO classes
and parse JSON string and dictionaries to them.

Python-DTO classes support validation of both type and value.

Example:

```
from typing import Optional
from pydto import DTO
from datetime import datetime

class CarDTO(DTO, partial=True):
    year = int, {"validator": lambda value: value > 1980}
    license = str,

class AddressDTO(DTO):
    city = str,

class UserDTO(DTO):
    first_name = str,
    middle_name = str,
    last_name = str,
    birth_date = datetime, {"coerce": lambda value: datetime.strptime(value, '%Y-%m-%d')}
    car = CarDTO,
    address = AddressDTO,
    email = str, {"immutable": False}
    salary = Optional[float],

json_string = '{"salary": null, "middle_name": "kurt", "address": {"city": "scranton"}, "first_name": "dwight", ' \
              '"email": "dshrute@schrutefarms.com", "car": {"license": "4018 JXT", "year": 1987, "color": "red"}, ' \
              '"last_name": "schrute", "birth_date": "1974-01-20"}'

user_dto = UserDTO.from_json(json_string)
```

Notes:
1. DTO classes attributes can be other DTOs or type object (e.g. int, float, string).
2. by default DTO object/attributes are immutable. You can change this by adding `{"immutable": False}` 
to DTO attribute definition tuple.
3. You can add custom value validator (callable object) to a DTO attribute by adding dictionary key `validator` the DTO attribute 
definition tuple e.g. `{"validator": lambda x: x>0}`.
4. by default all attributes of a DTO should be observed in the JSON/dictionary. Partial DTOs (with `partial=False` in their
class definition) can be part of a JSON/dictionary
5. You can define a specific parser for a DTO attribute by adding the dictionary key `coerce` to DTO definition tuple
e.g. `{"coerce": lambda value: datetime.strptime(value, '%Y-%m-%d')}`