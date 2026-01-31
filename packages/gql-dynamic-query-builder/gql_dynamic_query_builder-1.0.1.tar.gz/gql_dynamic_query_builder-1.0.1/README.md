## About this project

This project emerged from the frustrating experience when trying to
write gql queries with dynamic filters. In some cases, think of a UI
to beautifully display database contents, one desires to be able to set filters 
dynamically if some value is provided, yet just ignore it if not.

This behavior was guaranteed by Hasura versions 1.3.3v and below - but disabled by default in later versions,
as described [here](https://hasura.io/docs/2.0/queries/postgres/filters/index/#pg-null-value-evaluation).

The env var `HASURA_GRAPHQL_V1_BOOLEAN_NULL_COLLAPSE` preserves this functionality globally. However,
this as well is not always desired, when a more fine-grained control over when a value is strictly necessary
for where conditions, and when not, is of importance.

This project therefore provides a **lightweight query builder** that takes a simple gql query string
as input and inserts the respective clauses if a value is presented, and does nothing, if not.
This avoids nasty, error-prone, string concatenations while avoiding heavy-weight ASTs and the necessity
of schema declarations as with [gql-DSL](https://gql.readthedocs.io/en/v3.0.0/modules/dsl.html).

## Usage

All a user should be interacting with is located in the `src.api` package.
As of now it only contains the `GQLDynamicQueryBuilder` which is the heart of the project and
provides all the necessary functionality. To extend a query by an optional where clause one can do the
following:

~~~
    query = """
        query TestQuery {
            product {
                name
                brand
            }
        }
    """
    
    builder = GQLDynamicQueryBuilder(query)
    builder = builder.with_where_clause(
                table_name='product', 
                field_name='name', 
                value='tomato', 
                operation='_ilike',
                skip_if_none=True
              )
    result = builder.build() # returns the transformed query as a string
~~~

This also works for queries with existing where clauses and other query parameters (e.g. limit).
To access nested fields, simply use '.' as the delimiter:

~~~
    builder.with_where_clause(
        'product', 
        'brand.name', # will build brand { name: ...
        'ABC', 
        '_eq',
        skip_if_none=True
    )
    result = builder.build()
~~~

Furthermore, it is also possible to provide the following to `with_where_clause`:
- `values: list` and `operation: str` which allows for set-operations like `_in`
- `values: list` and `operation: list[str]` which allows for multiple operations for the same field
  (e.g. `timestamp {_gte: <ts1> lt: <ts2>}`)

As a fallback also explicit where clauses are supported via `table_name: clause` dictionaries:

~~~
    builder.with_where_clauses(
        {'product': 'name: {_ilike : "tomato"}'}
    )
    result = builder.build()
~~~