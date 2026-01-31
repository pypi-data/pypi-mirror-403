def construct_operation_value_string(value: str | int | list, operation: str) -> str:
    if operation in ['_like', '_ilike']:
        value = f'"%{value}%"'
    elif isinstance(value, str):
        value = f'"{value}"'

    return f'{operation}: {value}'


def construct_where_clause_string(nested_anc_explicit_where_clauses: dict) -> str:
    nested_field_clauses = []
    for key, value in nested_anc_explicit_where_clauses.items():
        if isinstance(value, dict):
            nested_field_clauses.append(
                f'{key}: {{{construct_where_clause_string(value)}}}'
            )
        else:
            nested_field_clauses.append(value)

    return ' '.join(nested_field_clauses)

def construct_filter_parameters_except_where_clause_string(limit: int | None, offset: int | None) -> str:
    limit_clause = f'limit: {limit}' if limit else None

    offset_clause = f'offset: {offset}' if offset else None
    filter_params_except_where_clause_string = f' {' '.join([c for c in [offset_clause, limit_clause] if c is not None])} '
    return filter_params_except_where_clause_string


def recursive_dict_merge(dict_to_merge_into: dict, dict_to_merge: dict) -> dict:
    for k, v in dict_to_merge.items():
        if (
            k in dict_to_merge_into
            and isinstance(dict_to_merge_into[k], dict)
            and isinstance(v, dict)
        ):
            recursive_dict_merge(dict_to_merge_into[k], v)
        else:
            dict_to_merge_into[k] = v
    return dict_to_merge_into


def handle_skip_if_none(skip_if_none: bool, to_return=None):
    if skip_if_none:
        return to_return
    else:
        raise ValueError(
            'Encountered None value in with_where_clause - '
            'if you want to skip it set skip_if_none=True'
        )
