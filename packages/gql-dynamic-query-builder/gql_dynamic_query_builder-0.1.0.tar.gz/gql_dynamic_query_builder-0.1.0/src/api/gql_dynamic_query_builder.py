from __future__ import annotations

import json

from core.helpers import (
    construct_operation_value_string,
    construct_where_clause_string,
    handle_skip_if_none,
    recursive_dict_merge,
)
from src.core.grammar.query import prepare_query_grammar


class GQLDynamicQueryBuilder:
    def __init__(self, query: str):
        self.query: str = query
        self.filter_parameters: dict[str, dict[str, dict | str]] = {}
        self.processed_query = query

    def update_where_clauses(
        self, table_name: str, field_name: str, clause: str
    ) -> None:
        current_table_clauses = (
            self.filter_parameters[table_name]
            if self.filter_parameters.get(table_name, None)
            else {}
        )
        fields = field_name.split('.')

        clause_dict = {fields[-1]: f'{fields[-1]}: {clause}'}
        for field in reversed(fields[:-1]):
            clause_dict = {field: clause_dict}

        recursive_dict_merge(current_table_clauses, clause_dict)
        self.filter_parameters[table_name] = current_table_clauses
        print(self.filter_parameters)

    def with_limit(self, table_name: str, limit: int, skip_if_none: bool = False):
        if limit is None:
            handle_skip_if_none(skip_if_none)
        elif self.filter_parameters.get(table_name, None):
            self.filter_parameters[table_name].update({'limit': f'limit: {limit}'})
        else:
            self.filter_parameters.update({table_name: {'limit': f'limit: {limit}'}})

    def with_offset(self, table_name: str, offset: int, skip_if_none: bool = False):
        if offset is None:
            handle_skip_if_none(skip_if_none)
        if self.filter_parameters.get(table_name, None):
            self.filter_parameters[table_name].update({'offset': f'offset: {offset}'})
        else:
            self.filter_parameters.update({table_name: {'offset': f'offset: {offset}'}})

    def with_where_clause(
        self,
        table_name: str,
        field_name: str,
        value: str | int | list[int] | list[str],
        operation: str | list[str],
        skip_if_none: bool = False,
    ):
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
            self.filter_parameters = transformed_clauses
        else:
            for table_name, clause in clauses.items():
                if self.filter_parameters.get(table_name, None):
                    self.filter_parameters[table_name].update(
                        {'explicit_clause': clause}
                    )
                else:
                    self.filter_parameters.update(
                        {table_name: {'explicit_clause': clause}}
                    )
        return self

    def build(self):
        for (
            table_name,
            nested_and_explicit_where_clauses,
        ) in self.filter_parameters.items():
            where_clauses = construct_where_clause_string(
                nested_and_explicit_where_clauses
            )
            query_grammar = prepare_query_grammar(table_name, where_clauses)
            self.processed_query = query_grammar.transform_string(self.processed_query)

        return self.processed_query
