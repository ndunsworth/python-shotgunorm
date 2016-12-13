
__all__ = [
  'SgEntitySearchFilters',
  'SgSearchFilter',
  'SgSearchFilters',
  'SgSearchFilterBasic',
  'SgSearchFilterLogicalOp',
  'SgSearchParameters',
  'SgTextSearchParameters'
]

# Python imports
from abc import abstractmethod
import copy

# This module imports
import ShotgunORM

class SgSearchFilter(object):
  '''

  '''

  BASIC_FILTER = 0
  LOGICAL_OP_FILTER = 1

  def __init__(self):
    pass

  @abstractmethod
  def copy(self):
    '''
    Copies the filter.
    '''

    raise NotImplementedError('SgSearchFilter.copy')

  @abstractmethod
  def field(self):
    '''

    '''

    raise NotImplementedError('SgSearchFilter.field')

  def isEmpty(self):
    '''
    Returns True if the filter is empty.
    '''

    return False

  def isLogicalOp(self):
    '''
    Returns False
    '''

    return False

  @abstractmethod
  def toFilter(self):
    '''
    Returns a value suitable for sending to Shotgun.
    '''

    raise NotImplementedError('SgSearchFilter.toFilter')

class SgSearchFilterBasic(SgSearchFilter):
  '''

  '''

  @classmethod
  def flattenFilters(cls, sgFilters):
    '''
    Internal function used to flatten Shotgun filter lists.  This will convert
    SgEntity objects into their equivalent Shotgun search pattern.

    Example:
    myProj = myConnection.findOne('Project', [['id', 'is', 65]])
    randomAsset = myConnection.findOne('Asset', [['project', 'is', myProj]])

    sgFilters becomes [['project', 'is', {'type': 'Project', 'id': 65}]]
    '''

    def flattenDict(obj):
      result = {}

      for key, value in obj.items():
        if isinstance(value, ShotgunORM.SgEntity):
          result[key] = value.toEntityFieldData()
        elif isinstance(value, ShotgunORM.SgField):
          result[key] = value.toFieldData()
        elif isinstance(value, (list, set, tuple)):
          result[key] = flattenList(value)
        elif isinstance(value, dict):
          result[key] = flattenDict(value)
        else:
          result[key] = value

      return result

    def flattenList(obj):
      result = []

      for i in obj:
        if isinstance(i, ShotgunORM.SgEntity):
          result.append(i.toEntityFieldData())
        elif isinstance(i, ShotgunORM.SgField):
          result.append(i.toFieldData())
        elif isinstance(i, (list, set, tuple)):
          result.append(flattenList(i))
        elif isinstance(i, dict):
          result.append(flattenDict(i))
        else:
          result.append(i)

      return result

    if sgFilters == None or sgFilters == []:
      return []

    if isinstance(sgFilters, int):
      return [['id', 'is', sgFilters]]
    elif isinstance(sgFilters, (list, set, tuple)):
      return flattenList(sgFilters)
    elif isinstance(sgFilters, dict):
      return flattenDict(sgFilters)
    else:
      return sgFilters

  def __repr__(self):
    return '<SgSearchFilterBasic(field: "%s", relation: "%s")>' % (
      self._field,
      self._relation
    )

  def __eq__(self, item):
    if not isinstance(item, SgSearchFilterBasic):
      return False

    return (
      self._field == item._field,
      self._relation == item._relation,
      self._values == item._values
    )

  def __init__(self, field, relation, values):
    super(SgSearchFilterBasic, self).__init__()

    feild, relation, values = self.flattenFilters(
      [field, relation, values]
    )

    self._field = field
    self._relation = relation
    self._values = values

  def copy(self):
    '''
    Returns a copy of this search filter.
    '''

    return SgSearchFilterBasic(
      self._field,
      self._relation,
      self._values
    )

  def field(self):
    '''
    Returns the field name.
    '''

    return self._field

  def relation(self):
    '''
    Returns the relation.
    '''

    return self._relation

  def setField(self, field):
    '''
    Sets the field name.
    '''

    self._field = field

  def setRelation(self, relation):
    '''
    Sets the relation.
    '''

    self._relation = relation

  def setValues(self, values):
    '''
    Sets the values.
    '''

    self._values = copy.deepcopy(values)

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgSearchFilterBasic):
      raise TypeError('other must be of type SgSearchFilterBasic')

    if id(other) == id(self):
      return

    field = self._field
    relation = self._relation
    values = self._values

    self._field = other._field
    self._relation = other._relation
    self._values = other._values

    other._field = field
    other._relation = relation
    other._values = values

  def toFilter(self):
    '''
    Returns a value suitable for sending to Shotgun.
    '''

    return [self._field, self._relation, self.values()]

  def type(self):
    '''
    Returns the filter type BASIC_FILTER.
    '''

    return SgSearchFilter.BASIC_FILTER

  def values(self):
    '''
    Returns the values.
    '''

    return copy.deepcopy(self._values)

class SgSearchFilterLogicalOp(SgSearchFilter):
  '''

  '''

  def __repr__(self):
    return '<SgSearchFilterLogicalOp("%s")>' % (
      self._op.operator()
    )

  def __eq__(self, item):
    if not isinstance(item, SgSearchFilterLogicalOp):
      return False

    return self._op == item._op

  def __init__(self, logicalOp):
    self._op = None

    self.setLogicalOp(logicalOp)

  def copy(self):
    '''
    Returns a copy of this search filter.
    '''

    return SgSearchFilterLogicalOp(self._op)

  def field(self):
    '''
    Returns the field the logical operator is for.
    '''

    return self._op.path()

  def isEmpty(self):
    '''
    Returns true if the logical operator is empty.
    '''

    return self._op.isEmpty()

  def isLogicalOp(self):
    '''
    Returns True
    '''

    return True

  def logicalOp(self):
    '''
    Returns the logical operator.
    '''

    return self._op.copy()

  def setLogicalOp(self, logicalOp):
    '''
    Sets the logical operator
    '''

    if isinstance(logicalOp, SgSearchFilterLogicalOp):
      self._op = logicalOp._op.copy()
    else:
      self._op = ShotgunORM.SgLogicalOp(logicalOp)

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgSearchFilterLogicalOp):
      raise TypeError('other must be of type SgSearchFilterLogicalOp')

    if id(other) == id(self):
      return

    self._op.swap(self._op)

  def toFilter(self):
    '''
    Returns a value suitable for sending to Shotgun.
    '''

    return self._op.toFilter()

  def type(self):
    '''
    Returns the filter type LOGICAL_OP_FILTER.
    '''

    return SgSearchFilter.LOGICAL_OP_FILTER

class SgSearchFilters(object):
  '''

  '''

  def __repr__(self):
    return '<SgSearchFilters>'

  def __iter__(self, *args):
    return self._filters.__iter__(*args)

  def __eq__(self, item):
    if not isinstance(item, SgSearchFilters):
      return False

    return self._filters == item._filters

  def __init__(self, filters=[]):
    self._filters = []

    if filters != None and len(filters) > 0:
      self.setFilters(filters)

  def addFilter(self, sgFilter):
    '''
    Adds the filter to the head of the filter list.
    '''

    if isinstance(sgFilter, SgSearchFilters):
      for i in sgFilter._filters[::-1]:
        self._filters.insert(0, i.copy())
    elif isinstance(sgFilter, SgSearchFilter):
      self._filters.insert(0, sgFilter.copy())
    else:
      if isinstance(sgFilter, (list, tuple)):
        f = SgSearchFilterBasic.flattenFilters(sgFilter)

        if len(f) > 3:
          raise ValueError('invalid filter %s' % f)

        self._filters.insert(
          0,
          SgSearchFilterBasic(f[0], f[1], f[2])
        )
      elif isinstance(sgFilter, (dict, ShotgunORM.SgLogicalOp)):
        self._filters.insert(
          0,
          SgSearchFilterLogicalOp(sgFilter)
        )
      else:
        raise TypeError('invalid filter %s' % sgFilter)

  def appendFilter(self, sgFilter):
    '''
    Appends the filter to the end of the filter list.
    '''

    if isinstance(sgFilter, SgSearchFilters):
      for i in sgFilter._filters:
        self._filters.append(i.copy())
    elif isinstance(sgFilter, SgSearchFilter):
      self._filters.append(sgFilter.copy())
    else:
      if isinstance(sgFilter, (list, tuple)):
        f = SgSearchFilterBasic.flattenFilters(sgFilter)

        if len(f) > 3:
          raise ValueError('invalid filter %s' % f)

        self._filters.append(
          SgSearchFilterBasic(f[0], f[1], f[2])
        )
      elif isinstance(sgFilter, dict):
        self._filters.append(
          SgSearchFilterLogicalOp(sgFilter)
        )
      else:
        raise TypeError('invalid filter %s' % sgFilter)

  def clear(self):
    '''
    Clears the filters.
    '''

    self._filters = []

  def copy(self):
    '''
    Returns a copy of this search filter.
    '''

    return SgSearchFilters(self._filters)

  def filters(self):
    '''
    Returns the search parameters.
    '''

    return list(self._filters)

  def hasLogicalOp(self):
    '''

    '''

    for i in self._filters:
      if i.type() == SgSearchFilter.LOGICAL_OP_FILTER:
        return True

    return False

  def hasFilterForField(self, field):
    '''

    '''

    for i in self._filters:
      if i.field() == field:
        return True

    return False

  def popFilter(self, index):
    '''
    Pops the filter at index and returns it.
    '''

    return self._filters.pop(index)

  def removeFilter(self, index):
    '''
    Removes the filter at index.
    '''

    del self._filters[index]

  def setFilters(self, filters):
    '''
    Sets the search filters.
    '''

    self._filters = []

    if filters != None:
      for i in filters:
        self.appendFilter(i)

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgSearchFilters):
      raise TypeError('other must be of type SgSearchFilters')

    if id(other) == id(self):
      return

    filters = self._filters

    self._filters = other._filters
    other._filters = filters

  def toSearchFilters(self):
    '''
    Returns a value suitable for sending to Shotgun.
    '''

    result = []

    if self.hasLogicalOp() == True:
      raise RuntimeError('SgSearchFilters contains a logical op')

    for i in self._filters:
      if i.isEmpty() == False:
        result.append(i.toFilter())

    return result

class SgEntitySearchFilters(SgSearchFilters):
  '''

  '''

  def __repr__(self):
    return '<SgEntitySearchFilters("%s")>' % self._entity_type

  def __iter__(self, *args):
    return self._filters.__iter__(*args)

  def __eq__(self, item):
    if isinstance(item, (SgSearchFilters, SgEntitySearchFilters)):
      return self._filters == item._filter

    return False

  def __init__(self, entityType, filters=[]):
    super(SgEntitySearchFilters, self).__init__(filters)

    self._entity_type = entityType

  def copy(self):
    '''
    Returns a copy of this search filter.
    '''

    return SgEntitySearchFilters(self._entity_type, self._filters)

  def entityType(self):
    '''
    Returns the Entity type.
    '''

    return self._entity_type

  def setEntityType(self, entityType):
    '''
    Sets the Entity search type.
    '''

    if not isinstance(entityType, str):
      raise TypeError('entityType arg must be of type str')

    self._entity_type = entityType

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgSearchFilters):
      raise TypeError(
        'other must be of type SgSearchFilters or SgEntitySearchFilters'
      )

    if id(other) == id(self):
      return

    super(SgEntitySearchFilters, self).swap(other)

    if isinstance(other, SgEntitySearchFilters):
      entity_type = self._entity_type

      self._entity_type = other._entity_type
      other._entity_type = entity_type

  def toSearchString(self, sgConnection):
    '''
    Returns a search string of this search filter.
    '''

    return ShotgunORM.parseFromLogicalOp(self.toLogicalOp())

  def toLogicalOp(self, sgConnection, operator='and'):
    '''
    Returns a SgLogicalOp of this search filter.
    '''

    if operator != 'and' and operator != 'or':
      raise ValueError('invalid operator name "%s"' % operator)

    logical_op = ShotgunORM.SgLogicalOp()

    e_info = sgConnection.schema().entityInfo(self._entity_type)

    filters = self.toSearchFilters()

    for i in self._filters:
      if i.isLogicalOp() == True:
        logical_op.appendCondition(i)
      else:
        op_cond = ShotgunORM.convertToLogicalOpCond(
          e_info,
          i.toFilter()
        )

        logical_op.appendCondition(
          ShotgunORM.SgLogicalOpCondition(**op_cond)
        )

    return logical_op

class SgSearchParameters(SgEntitySearchFilters):
  '''

  '''

  def __repr__(self):
    return '<SgSearchParameters("%s")>' % self.entityType()

  def __init__(
    self,
    entity_type,
    filters,
    fields=None,
    order=None,
    filter_operator=None,
    limit=0,
    retired_only=False,
    page=0,
    include_archived_projects=True,
    additional_filter_presets=None,
    sgQueryFieldTemplate=None,
    connection=None
  ):
    super(SgSearchParameters, self).__init__(entity_type, filters)

    self._fields = []
    self._order = None
    self._filter_operator = None
    self._limit = 0
    self._retired_only = False
    self._page = 0
    self._include_archived_projects = True
    self._additional_filter_presets = None
    self._query_field_template = None
    self._connection = None

    self.setFields(fields)
    self.setOrder(order)
    self.setFilterOperator(filter_operator)
    self.setLimit(limit)
    self.setRetiredOnly(retired_only)
    self.setPage(page)
    self.setIncludeArchivedProjects(include_archived_projects)
    self.setAdditionalFilterPresets(additional_filter_presets)
    self.setQueryFieldTemplate(sgQueryFieldTemplate)
    self.setConnection(connection)

  def additionalFilterPresets(self):
    '''
    Returns the additional filter presets.
    '''

    if self._additional_filter_presets == None:
      return None
    else:
      return copy.deepcopy(self._additional_filter_presets)

  def connection(self):
    '''
    Returns the Shotgun connection.
    '''

    return self._connection

  def copy(self):
    '''
    Returns a copy of the search parameters.
    '''

    return SgSearchParameters(
      connection=self._connection,
      **self.parameters()
    )

  def copyFilters(self):
    '''
    Returns a copy of the search filters.
    '''

    result = []

    for i in self._filters:
      result.append(i.copy())

    return result

  def fields(self):
    '''
    Returns the fields that will be returend for results.
    '''

    if self._fields == None:
      return None
    else:
      return list(self._fields)

  def filterOperator(self):
    '''
    Returns the filter operator.
    '''

    if self._filter_operator == None:
      return None
    else:
      return copy.deepcopy(self._filter_operator)

  def includeArchivedProjects(self):
    '''
    Returns True if archived projects will be included in search
    results.
    '''

    return self._include_archived_projects

  def limit(self):
    '''
    Returns the search limit.
    '''

    return self._limit

  def order(self):
    '''
    Returns the search order.
    '''

    if self._order == None:
      return self._order
    else:
      return copy.deepcopy(self._order)

  def page(self):
    '''
    Returns the search page.
    '''

    return self._page

  def parameters(self):
    '''
    Returns a dictionary contain all the search parameters.
    '''

    return {
      'entity_type': self.entityType(),
      'filters': self.toSearchFilters(),
      'fields': self.fields(),
      'order': self.order(),
      'filter_operator': self.filterOperator(),
      'limit': self.limit(),
      'retired_only': self.retiredOnly(),
      'page': self.page(),
      'include_archived_projects': self.includeArchivedProjects(),
      'additional_filter_presets': self.additionalFilterPresets(),
      'setQueryFieldTemplate': self.queryFieldTemplate()
    }

  def queryFieldTemplate(self):
    '''
    Returns the query field template parameter.
    '''

    return self._query_field_template

  def retiredOnly(self):
    '''
    Returns True if retired only will be searched.
    '''

    return self._retired_only

  def setAdditionalFilterPresets(self, additionalFilterPresets):
    '''
    Set the additionial filter presets.
    '''

    if additionalFilterPresets == None:
      self._additional_filter_presets = None
    else:
      self._additional_filter_presets = copy.deepcopy(
        additionalFilterPresets
      )

  def setConnection(self, sgConnection):
    '''
    Set the Shotgun connection.
    '''

    if (
      sgConnection != None and
      not isinstance(sgConnection, ShotgunORM.SgConnection)
    ):
      raise TypeError('sgConnection must be of type SgConnection')

    self._connection = sgConnection

  def setFields(self, fields):
    '''
    Set the fields to return.
    '''

    if fields == None:
      self._fields = None
    else:
      self._fields = list(fields)

  def setFilterOperator(self, filterOperator):
    '''
    Set the filter operator.
    '''

    self._filter_operator = copy.deepcopy(filterOperator)

  def setIncludeArchivedProjects(self, state):
    '''
    Set the include archived projects filter.
    '''

    self._include_archived_projects = bool(state)

  def setLimit(self, limit):
    '''
    Set the search limit.
    '''

    self._limit = int(limit)

  def setOrder(self, order):
    '''
    Set the search result order.
    '''

    self._order = copy.deepcopy(order)

  def setPage(self, page):
    '''
    Set the search page.
    '''

    self._page = int(page)

  def setQueryFieldTemplate(self, template):
    '''

    '''

    self._query_field_template

  def setRetiredOnly(self, state):
    '''
    Set searched retired items only.
    '''

    self._retired_only = bool(state)

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgSearchFilters):
      raise TypeError(
        'other must be of type SgSearchParameters, SgSearchFilters or SgEntitySearchFilters'
      )

    if id(other) == id(self):
      return

    super(SgEntitySearchFilters, self).swap(other)

    if isinstance(other, SgSearchParameters):
      fields = self._fields
      order = self._order
      filter_operator = self._filter_operator
      limit = self._limit
      retired_only = self._retired_only
      page = self._page
      include_archived_projects = self._include_archived_projects
      additional_filter_presets = self._additional_filter_presets
      query_template = self._query_field_template
      connection = self._connection

      self._fields = other._fields
      self._order = other._order
      self._filter_operator = other._filter_operator
      self._limit = other._limit
      self._retired_only = other._retired_only
      self._page = other._page
      self._include_archived_projects = other._include_archived_projects
      self._additional_filter_presets = other._additional_filter_presets
      self._query_field_template = other._query_field_template
      self._connection = other._connection

      other._fields = fields
      other._order = order
      other._filter_operator = filter_operator
      other._limit = limit
      other._retired_only = retired_only
      other._page = page
      other._include_archived_projects = include_archived_projects
      other._additional_filter_presets = additional_filter_presets
      other._query_field_template = query_field_template
      other._connection = connection

class SgTextSearchParameters(object):
  '''

  '''

  def __init__(
    self,
    text,
    entity_types,
    project_ids=None,
    limit=None,
    connection=None
  ):
    self._text = ''
    self._entity_types = {}
    self._project_ids = None
    self._limit = None
    self._connection = connection

    self.set(text, entity_types, project_ids, limit)

  def connection(self):
    '''
    Returns the Shotgun connection.
    '''

    return self._connection

  def copy(self):
    '''
    Returns a copy of this text search parameters.
    '''

    return SgTextSearchParameters(
      self._text,
      self._entity_types,
      self._project_ids,
      self._limit,
      self._connection
    )

    return result

  def limit(self):
    '''
    Returns the search limit.
    '''

    return self._limit

  def entityTypes(self):
    '''
    Returns a dict containing search type filters.
    '''

    result = {}

    for e_type, filters in self._entity_types.items():
      result[e_type] = filters.toSearchFilters()

    return result

  def parameters(self):
    '''
    Returns a dictionary of all parameters.
    '''

    return {
      'text': self._text,
      'entity_types': self.entityTypes(),
      'project_ids': self.projectIds(),
      'limit': self._limit
    }

  def projectIds(self):
    '''
    Returns the project ids.
    '''

    if self._project_ids == None:
      return None
    else:
      return list(self._project_ids)

  def set(
    self,
    text,
    entity_types,
    project_ids=None,
    limit=None
  ):
    '''
    Configure all parameters.
    '''

    self.setText(text)
    self.setEntityTypes(entity_types)
    self.setProjectIds(project_ids)
    self.setLimit(limit)

  def setConnection(self, sgConnection):
    '''
    Sets the Shotgun connection
    '''

    if (
      sgConnection != None and
      not isinstance(sgConnection, ShotgunORM.SgConnection)
    ):
      raise TypeError('sgConnection must be of type SgConnection')

    self._connection = sgConnection

  def setEntityTypes(self, entityTypes):
    '''
    Set the entity types.
    '''

    self._entity_types = {}

    for e_type, filters in entityTypes.items():
      self._entity_types[e_type] = SgSearchFilters(filters)

  def setLimit(self, limit):
    '''
    Set the search result limit.
    '''

    if limit == None:
      self._limit = None
    else:
      self._limit = int(limit)

  def setProjectIds(self, projectIds):
    '''
    Set the search project ids.
    '''

    if projectIds == None or len(projectIds) <= 0:
      self._project_ids = None
    else:
      self._project_ids = list(projectIds)

  def setText(self, text):
    '''
    Set the search text, must be a minimum of 3 chars long or a
    ValueError is raised.
    '''

    if len(text) < 3:
      raise ValueError('text must be a min of 3 chars long')

    self._text = text

  def swap(self, other):
    '''
    Swaps the values between this and other.
    '''

    if not isinstance(other, SgTextSearchParameters):
      raise TypeError('other must be of type SgTextSearchParameters')

    if id(other) == id(self):
      return

    text = self._text
    entity_types = self._entity_types
    project_ids = self._project_ids
    limit = self._limit
    connection = self._connection

    self._text = other._text
    self._entity_types = other._entity_types
    self._project_ids = other._project_ids
    self._limit = other._limit
    self._connection = other._connection

    other._text = text
    other._entity_types = entity_types
    other._project_ids = project_ids
    other._limit = limit
    other._connection = connection

  def text(self):
    '''
    Returns the search text.
    '''

    return self._text
