# Python-DTO

Simple implementation of Data Transfer Object (DTO) in Python. 

With Python-DTO you can make Immutable/Mutable (or partially mutable - i.e. attribute level control) DTO classes
and parse JSON and dictionary to them.

Python-DTO classes support validation of both type and value.

Example:

```
from typing import Optional
from pydto import DTO


class CarDTO(DTO):
    year = int, {"validator": lambda value: value > 1980}
    license = str,


class AddressDTO(DTO):
    city = str,


class UserDTO(DTO):
    first_name = str,
    middle_name = str,
    last_name = str,
    birth_date = str,
    car = CarDTO,
    address = AddressDTO,
    email = str, {"immutable": False}
    salary = Optional[float],


json_string = '{"salary": null, "middle_name": "kurt", "address": {"city": "scranton"}, "first_name": "dwight", ' \
              '"email": "dshrute@schrutefarms.com", "car": {"license": "4018 JXT", "year": 1987}, ' \
              '"last_name": "schrute", "birth_date": "January 20, 1974"}'

user_dto = UserDTO.from_json(json_string)    
```

