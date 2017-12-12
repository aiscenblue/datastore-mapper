from http import HTTPStatus

from gcloud.datastore import Client, Entity
import datetime
import uuid
import re
import string
import random

from services.responses import HTTPResponse


""" prevent calling all instances using wildcard imports """
__all__ = ['Model']


def model_error_handler(fn):
    """ decorator for handling errors
        if errors list is more than 0 it will cancel the current transaction and return an error result
        without having an Exception error
    """
    def wrapper(*args):
        m = args[0]

        if isinstance(m, Model):
            if len(m.errors):
                return "Cannot proceed to transaction {}. There are errors encountered.".format(fn)
            else:
                fn(*args)
        else:
            raise PropertyException("Invalid model.")

    return wrapper


class PropertyException(Exception):
    """ extends Exception class """
    pass


class AbstractProperty(object):
    _property_value = None

    def __init__(self, default=None):
        if not self._property_value and default:
            self.set_value(default)

    def set_value(self, val):
        if len(val):
            self.is_entity(val[0])
        self._property_value = val

    def is_entity(self, en):
        if not isinstance(en, Entity):
            raise PropertyException("Invalid {} format".format(self.__class__.__name__))


class Property(AbstractProperty):

    """ Physical layer of the Model Properties """

    def set_value(self, val):
        self._property_value = val

    def get_value(self):
        return self._property_value

    def to_string(self):
        return self.get_value()


class UidProperty(Property):
    pass


class EntityProperty(Property):
    pass


class StringProperty(Property):
    def set_value(self, val):
        if not isinstance(val, str):
            raise PropertyException("Invalid {} format".format(self.__class__.__name__))
        self._property_value = val


class UrlProperty(Property):

    __regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def set_value(self, val):
        if not self.__regex.match(val):
            raise PropertyException("Invalid {} format".format(self.__class__.__name__))
        self._property_value = val


class RandomStringProperty(Property):

    def __init__(self, min_length=8, max_length=12):
        super().__init__()
        self.__min = min_length
        self.__max = max_length

    def set_value(self, val):
        self._property_value = self.randomize()

    def randomize(self):
        all_characters = string.ascii_letters + string.punctuation + string.digits
        return "".join(random.choice(all_characters) for x in range(random.randint(self.__min, self.__max)))


class EmailProperty(Property):
    def set_value(self, val):
        if not re.match("[^@]+@[^@]+\.[^@]+", val):
            raise PropertyException("Invalid {} format".format(self.__class__.__name__))


class Properties:
    uid = None
    createdAt = None
    updatedAt = None
    deletedAt = None
    __index = False

    def __init__(self, index=False, ):
        self.uid = str(uuid.uuid1())
        self.createdAt = datetime.datetime.now()
        self.updatedAt = self.createdAt
        self.__index = index

    def add_attribute(self, key, value):
        setattr(self, key, value)


class ModelErrorLogs:
    """
        set error logs to filter out the parameter assigned
        carefully to make sure its an array to prevent runtime error
    """
    def __init__(self):
        self.__error_logs = []

    def set_error_log(self, error):
        """ setter for errors property
            :param error -> list
        """
        if isinstance(error, list):
            self.__error_logs.extend(error)
        else:
            raise ValueError("error parameter must be a list.")

    @property
    def errors(self):
        """ no setters for errors to prevent redundant assignment.
            it receives an array that extends the current existing data
            instead of using an assignmet implementation its better to use set_error_log as a setter
            function. we may gonna use the setter property of errors in the future.
        """
        return self.__error_logs


class ModelEnums(ModelErrorLogs):
    __DEFAULT_EXCLUDE_INDEXES = ['createdAt', 'updatedAt']
    _EXCLUDE_INDEXES = __DEFAULT_EXCLUDE_INDEXES


class ModelEnumsImpl(ModelEnums):
    """ an abstract class supposedly for extending enum to prevent TypeError: Cannot extend enumerations
        then creating another class layer that sets all the attributes needed

        this class purpose is just to implements the behaviors needed in the ModelEnums
    """
    __excluded_indexes__ = []

    def set_excluded_indexes(self, items):
        if isinstance(items, list):
            self._EXCLUDE_INDEXES.extend(items)
        else:
            raise ValueError("items must be a list instance")

    def __extend_custom_excluded_indexes(self):
        self.set_excluded_indexes(self.__excluded_indexes__)

    def get_excluded_indexes(self):
        self.__extend_custom_excluded_indexes()
        return self._EXCLUDE_INDEXES


class ClientModel(ModelEnumsImpl):
    """
        setters and getters of the required AbstractModel
        This class is all about settings the properties needed for the logical class layer ( AbstractModel )
        to minimize the footprint of the logic layer class
    """
    __key = None
    __kind = None
    __key_uid = None

    def __init__(self):

        self.client = Client()

        """
            assign all the required attributes from the AbstractModel class in order for the behaviors to run
        """
        self.__properties = Properties()
        self.kind = self.__class__.__name__
        self.key_id = self.properties.uid
        self.set_key()
        self.data = []

        super().__init__()

    @property
    def properties(self):
        return self.__properties

    @property
    def kind(self):
        if self.__kind is None:
            raise ValueError("Cannot define a none type kind.")
        return self.__kind

    @kind.setter
    def kind(self, new_kind):
        self.__kind = new_kind

    def set_key(self, *args, **kwargs):
        if not self.key_id:
            raise PropertyException("Invalid uid value.")

        self.__key = self.client.key(self.kind, self.key_id, *args, **kwargs)

    @property
    def key(self):
        if self.__key is None:
            try:
                self.__key = self.set_key()
            except Exception as e:
                self.__error_logs.extend([e])
        return self.__key

    @property
    def key_id(self):
        return self.__key_uid

    @key_id.setter
    def key_id(self, value):
        self.__key_uid = value


class AbstractModel(ClientModel):
    """
        This class layer is about the behaviors needed for the View layer class (Model)
    """

    def __init__(self):
        super().__init__()

    def query(self, **kwargs):
        return self.client.query(kind=self.kind, **kwargs)

    """
        :param params ->list[tuple]
            -> tuple(property_name<string>, operator<string symbols>, value<any>)
    """
    def filters(self, params):
        if not isinstance(params, (list, tuple)):
            self.set_error_log(["Filters must be a list."])

        q = self.client.query()

        for _ in params:
            if len(_) == 3:
                property_name, operator, value = _
                q.add_filter(property_name, operator, value)
                return q.fetch()
            else:
                self.set_error_log(["Filters must consist of tuple(property_name, operator, value)."])

    """
        :param kwargs:
        :return: iterator matching queries
    """
    def all_items(self, **kwargs):
        q = self.query()

        return q.fetch(**kwargs)

    """
        :param id
        finds the current data based on id
    """
    def find_by_id(self, model_uid, **kwargs):
        if isinstance(model_uid, int):
            self.set_key(model_uid)
        else:
            self.set_key(int(model_uid))

        query = self.query()
        query.key_filter(self.key)
        return list(query.fetch(**kwargs))

    def find_by_iud(self, uid, **kwargs):
        self.filters([('uid', '=', uid)])
        return list(self.query().fetch(**kwargs))

    """
        :param self
        :returns dict[str]
    """
    def delete(self):
        self.properties.deletedAt = datetime.datetime.now()
        return self.update()

    """
        :param self
        :returns dict[str]
    """
    def update(self):
        self.key_id = self.properties.uid
        self.set_key()
        return self.save()

    @model_error_handler
    def save(self):
        transaction = self.client.transaction()
        transaction.begin()
        try:
            """
                Expected type 'tuple[str]', got 'list' instead in the IDE issue is okay.
                it's because they set the default parameter as a tuple but in their docs
                it can be either tuple or list
            """
            entity = Entity(key=self.key, exclude_from_indexes=self.get_excluded_indexes())
            iter_items = self.properties.__dict__.items()
            dict_items = {}

            for key, value in iter_items:
                if not key.startswith('_'):
                    entity[key] = value
                    dict_items.update({key: value})

            transaction.put(entity)
            transaction.commit()

            self.data = [dict_items]
            return self.data

        except Exception as e:

            self.set_error_log([e])
            transaction.rollback()

            return "Unexpected error occurred."


class Model(AbstractModel):

    def __init__(self, *args, **kwargs):
        """
            instantiate super class Abstractmodel
            calling it last because it inherits Property class which are needed to transact the abstractmodel methods
        """
        super().__init__()

        """ get Model kwargs parameter """
        for key, value in kwargs.items():
            """ get the child class attribute and properties"""
            attr_class = self.__class__
            attr_key = attr_class.__dict__.get(key)
            """ checking if its a public attribute """
            if not key.startswith('_') and attr_key and isinstance(attr_key, Property):
                try:
                    if hasattr(attr_key, "set_value"):
                        attr_key.set_value(val=value)
                except PropertyException as e:
                    self.set_error_log([e])
                self.properties.add_attribute(key, attr_key.get_value())

    """ 
        displays the whole information of the superclass and the child class 
        and everything associated with it including the public declaration associations
    """
    def get_info(self):
        return HTTPResponse(message="Success", data=self, status=HTTPStatus.OK).to_json()

    def string_attribute(self, attrib):
        return "{}{}".format(self.__class__.__name__, attrib)


class ModelCollection(HTTPResponse):

    data = []
    more_results = False
    next_cursor = None

    def __init__(self, model, **kwargs):
        self.__cursor = None
        self.__order = '-createdAt'
        self.__limit = 15
        self.__model_id = None
        self.__model_filters = None

        if isinstance(model, Model):
            if "cursor" in kwargs:
                self.__cursor = kwargs.get('cursor')[0]
            if "order" in kwargs:
                self.__order = kwargs.get('order')[0]
            if "limit" in kwargs:
                self.__limit = int(kwargs.get('limit')[0])
            if "uid" in kwargs:
                self.__model_id = kwargs.get('uid')[0]
            if "filters" in kwargs:
                self.__model_filters = kwargs.get('filters')[0]
            self.__order = [self.__order]

            page, more_results, start_cursor = list(self.model_query(model))

            """ instance setters for class constant properties """
            self.data = page,
            self.more_results = more_results,
            self.next_cursor = start_cursor

            """ HTTPResponse superlative class implementation after the ModelCollection class layer transaction """
            super().__init__(status=200, data=page, more_results=more_results, next_cursor=start_cursor)
        else:
            raise TypeError("Invalid object type.")

    def model_query(self, model):
        if isinstance(model, Model):
            model.query(order=self.__order)

            if self.__model_id:
                return model.filters([("uid", "=", self.__model_id)]), False, None

            if self.__model_filters and isinstance(self.__model_filters, (list, tuple)):
                # TODO :: multiple filters cannot get list instance
                return model.filters(self.__model_filters), False, None

            iter_items = model.all_items(start_cursor=self.__cursor, limit=self.__limit)

            """ returns (page, more_results, start_cursor) """
            return iter_items.next_page()
        else:
            raise AttributeError("model must be a Model instance.")
