**Requirements:**
```
  Python 3.5 or higher
```

**Install requirements**  
`pip3 install datastore_mapper`


# Set google application credentials
```
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/gcp-service-key.json"
```

# Create Model
```
from datastore_mapper import Model, StringProperty, EmailProperty, UidProperty


class Users(Model):
    uid = UidProperty()
    first_name = StringProperty()
    last_name = StringProperty()
    email = EmailProperty()

    __excluded_indexes__ = ['first_name', 'last_name', 'email']

```
> excluded_indexes is to unset properties that it not needed to be indexed. 
datastore set all properties indexed as a default

# Create

```
users = Users(first_name="John", last_name="Doe", email="john_doe@email.com")
users.save()
```

*** Save using ancestor ***
```
users = Users()
users.set_key(ancestor="generatedUID")
users.save()

users_posts = UsersPosts()
users_posts.set_key(ancestor=users.key)
users_posts.save()
```

# Update

```
users = Users(uid="exampleGeneratedUID", first_name="John", last_name="Doe", email="john_doe@email.com")
users.update()
```

# Delete

```
users = Users(uid="exampleGeneratedUID")
users.delete()
```
> delete is a logical deletion where the data 
will be updated the deleted_at property which is a default property model to the current date

# Search query

```
from datastore_mapper import ModelCollection

ModelCollection(Users(), **kwargs).to_json()
```

> **kwargs can be any query that you like example
uid="generatedUID" -> for finding the specific User Model in the datastore

> order="-created_at" for descending order or order="created_at" for ascending order

> limit="15" to set limit per list. DEFAULT is 15

> filters=[('first_name', '=', "john"")]

> Users().find_by_iud("generatedUID")

# errors

```
users = Users(first_name="John", last_name="Doe", email="john_doe@email.com")
users.errors
users.save() or update() or delete()
users.data
```
> errors are list or errors from the library. This implementation is to prevent try catch repetition
> data are lists of results from the query.