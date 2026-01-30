# Pydantricks

Faker for pydantic models.



## Start simple

```python
>>> from pydantic import BaseModel
>>> from pydantricks import FieldFactory, ModelFactory
>>>
>>>
>>> class User(BaseModel):
...     username: str
...
>>>
>>> class UserFactory(ModelFactory[User]):
...     username = FieldFactory.field.user_name
...
>>> UserFactory()
User(username='qmiller')
>>> UserFactory()
User(username='harrisamanda')
>>> UserFactory()
User(username='jamesamy')
```

pydantricks support composed models as well.
