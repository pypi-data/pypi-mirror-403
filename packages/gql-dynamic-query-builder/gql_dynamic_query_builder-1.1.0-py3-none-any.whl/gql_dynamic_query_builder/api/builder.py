from __future__ import annotations

import json

from gql_dynamic_query_builder.core.grammar.query import prepare_query_grammar
from gql_dynamic_query_builder.core.helpers import (
    construct_operation_value_string,
    construct_where_clause_string,
    handle_skip_if_none,
    recursive_dict_merge, construct_filter_parameters_except_where_clause_string,
)


class GQLDynamicQueryBuilder:
    def __init__(self, query: str):
        self.query: str = query
        self.where_clauses: dict[str, dict[str, dict | str]] = {}
        self.processed_query = query
        self.limits: dict = {}
        self.offsets: dict = {}

    def update_where_clauses(
        self, table_name: str, field_name: str, clause: str
    ) -> None:
        current_table_clauses = (
            self.where_clauses[table_name]
            if self.where_clauses.get(table_name, None)
            else {}
        )
        fields = field_name.split('.')

        clause_dict = {fields[-1]: f'{fields[-1]}: {clause}'}
        for field in reversed(fields[:-1]):
            clause_dict = {field: clause_dict}

        recursive_dict_merge(current_table_clauses, clause_dict)
        self.where_clauses[table_name] = current_table_clauses


    def with_limit(self, table_name: str, limit: int, skip_if_none: bool = False) -> GQLDynamicQueryBuilder:
        if limit is None:
            handle_skip_if_none(skip_if_none)
        elif self.limits.get(table_name, None):
            self.limits[table_name] = limit
        else:
            self.limits.update({table_name: limit})
        return self

    def with_offset(self, table_name: str, offset: int, skip_if_none: bool = False) -> GQLDynamicQueryBuilder:
        if offset is None:
            handle_skip_if_none(skip_if_none)
        if self.offsets.get(table_name, None):
            self.offsets[table_name] = offset
        else:
            self.offsets.update({table_name: offset})
        return self

    def with_where_clause(
        self,
        table_name: str,
        field_name: str,
        value: str | int | list[int] | list[str],
        operation: str | list[str],
        skip_if_none: bool = False,
    ) -> GQLDynamicQueryBuilder:
        if value is None:
            return handle_skip_if_none(skip_if_none, self)

        if isinstance(value, list):
            if isinstance(operation, list):
                pairs = [
                    construct_operation_value_string(v, o)
                    for v, o in zip(value, operation, strict=True)
                ]
                self.update_where_clauses(
                    table_name, field_name, f'{{{" ".join(pairs)}}}'
                )
            else:
                value = json.dumps(value)
                self.update_where_clauses(
                    table_name, field_name, f'{{{operation}: {value}}}'
                )
        else:
            if isinstance(operation, list):
                raise TypeError('Operation should be scalar if value is scalar')
            self.update_where_clauses(
                table_name,
                field_name,
                f'{{{construct_operation_value_string(value, operation)}}}',
            )

        return self

    def with_where_clauses(
        self, clauses: dict[str, str], overwrite: bool = False
    ) -> GQLDynamicQueryBuilder:
        if overwrite:
            transformed_clauses = {
                table_name: {'explicit_clause': clause}
                for table_name, clause in clauses.items()
            }
            self.where_clauses = transformed_clauses
        else:
            for table_name, clause in clauses.items():
                if self.where_clauses.get(table_name, None):
                    self.where_clauses[table_name].update(
                        {'explicit_clause': clause}
                    )
                else:
                    self.where_clauses.update(
                        {table_name: {'explicit_clause': clause}}
                    )
        return self

    def build(self) -> str:
        for (
            table_name
        ) in set(list(self.where_clauses.keys()) + list(self.limits.keys()) + list(self.offsets.keys())):
            nested_and_explicit_where_clauses = self.where_clauses.get(table_name, {})
            where_clauses = construct_where_clause_string(
                nested_and_explicit_where_clauses
            )

            limit = self.limits.get(table_name, None)
            offset = self.offsets.get(table_name, None)
            filter_parameters_except_where_clause = construct_filter_parameters_except_where_clause_string(limit, offset)
            query_grammar = prepare_query_grammar(table_name, where_clauses, filter_parameters_except_where_clause)
            self.processed_query = query_grammar.transform_string(self.processed_query)

        return self.processed_query
