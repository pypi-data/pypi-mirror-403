from typing import Dict, List, Any, Tuple
"""

"""

def build_where_clause(where: Dict[str, Any], start_index: int = 1) -> Tuple[str, list]:
    """
    Build a sql where clause for postinal placeholder.

    Docstring for build_where_clause
    
    :param where: Description
    :type where: Dict[str, Any]
    :param start_index: Description
    :type start_index: int
    :return: Description
    :rtype: Tuple[str, list]


    #Example:
        input:
            >> build_where_clause(where={"user_id": 42",status":"active"})

        output: 
            >> retutn clause = (user_id = $1 AND status = $2) | values = [42, "active"]
    """

    conditions = []
    values = []

    for idx, (key, value) in enumerate(where.items()):
        conditions.append(f"{key} = ${start_index + idx}")
        values.append(value)

    clause = " AND ".join(conditions)
    return clause, values


def build_insert(table: str, schema: str, values: List[Dict[str, Any]]) -> Tuple[str, List[Any]]:
    """
    Build a SQL INSERT query with positional placeholders for multiple rows.

    :param table: Name of the database table
    :param schema: Schema name
    :param values: List of column-value dictionaries for insert
    :return: SQL INSERT query and flattened values list

    # Example:
        input:
            build_insert(
                table="users",
                schema="public",
                values=[
                    {"name": "Aravindh", "age": 24},
                    {"name": "Vikas", "age": 30}
                ]
            )
        output:
            sql = "INSERT INTO public.users (name, age) VALUES ($1, $2), ($3, $4)"
            values = ["Aravindh", 24, "Vikas", 30]
    """

    if not values:
        raise ValueError("Values list cannot be empty")

    # Extract column names from the first dict
    columns = ", ".join(values[0].keys())
    
    # Build placeholders for each row
    placeholders_list = []
    flattened_values = []
    for idx, row in enumerate(values):
        placeholders = ", ".join(f"${idx*len(row) + i + 1}" for i in range(len(row)))
        placeholders_list.append(f"({placeholders})")
        flattened_values.extend(row.values())

    sql = f"INSERT INTO {schema}.{table} ({columns}) VALUES {', '.join(placeholders_list)}"
    return sql, flattened_values



def build_update(table: str, schema:str,  values: Dict[str, Any], where: Dict[str, Any]):
    """
    Build a SQL UPDATE query with positional placeholders.
    Docstring for build_update
    # Example:
        input:
            >> build_update(
                   table="users",
                   schema="public",
                   values={"name": "Aravindh", "age": 27},
                   where={"id": 10}
                )

        output:
            >> return sql = (
                   UPDATE public.users SET name = $1, age = $2 WHERE id = $3) values = ["Aravindh", 27, 10]
    """

    set_clause = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(values.keys()))
    where_clause, where_values = build_where_clause(where, start_index=len(values) + 1)

    sql = f"UPDATE {schema}.{table} SET {set_clause} WHERE {where_clause}"
    return sql, list(values.values()) + where_values



def build_select(table: str, schema:str,  columns: List[str], where: Dict[str, Any] | None):
    """
    Build a SQL SELECT query with optional WHERE clause.

    Docstring for build_select

    :param table: Name of the database table
    :param scehma: Name of the Schema 
    :type table: str
    :param columns: List of columns to select
    :type columns: List[str]
    :param where: Optional column-value mapping for WHERE clause
    :type where: Dict[str, Any] | None
    :return: SQL SELECT query and values list
    :rtype: Tuple[str, list]

    # Example (without WHERE):
        input:
            >> build_select(
                   table="users",
                   schema="public",
                   columns=["id", "name"],
                   where=None
               )

        output:
            >> return sql = (
                   SELECT id, name FROM public.users) values = []

    # Example (with WHERE):
        input:
            >> build_select(
                   table="users",
                   schema="public",
                   columns=["id", "name"],
                   where={"status": "active"}
               )

        output:
            >> return sql = (
                   SELECT id, name FROM public.users WHERE status = $1) values = ["active"]
    """
    col_str = ", ".join(columns)
    sql = f"SELECT {col_str} FROM {schema}.{table}"

    if not where:
        return sql, []

    where_clause, values = build_where_clause(where)
    sql += f" WHERE {where_clause}"
    return sql, values
