from sqlalchemy.sql import func as sql_func
from sqlmodel import desc, select

from planar.routers.models import SortDirection


def build_paginated_query(
    query, filters=None, offset=None, limit=None, order_by=None, order_direction=None
):
    """
    Helper function to build paginated and filtered queries.

    Args:
        query: The base SQL query to build upon
        filters: Optional list of filter conditions, where each condition is a tuple of
                (column, operator, value). Operator should be one of:
                '==', '!=', '>', '>=', '<', '<=', 'like', 'ilike', 'in', 'not_in'
                For example: [(User.name, '==', 'John'), (User.age, '>', 18)]
                For date ranges: [(Workflow.created_at, '>=', start_date)]
        offset: Optional offset for pagination
        limit: Optional limit for pagination
        order_by: Optional field or list of fields to order by
        order_direction: Optional direction to order by
    Returns:
        Tuple of (paginated query, total count query)
        The count query is guaranteed to work with the session.exec().one() pattern
    """
    # Create a copy of the query for filtering
    filtered_query = query

    # Apply filters if provided
    if filters:
        for column, operator, value in filters:
            if value is not None:  # Skip None values
                if operator == "==" or operator == "=":
                    filtered_query = filtered_query.where(column == value)
                elif operator == "!=":
                    filtered_query = filtered_query.where(column != value)
                elif operator == ">":
                    filtered_query = filtered_query.where(column > value)
                elif operator == ">=":
                    filtered_query = filtered_query.where(column >= value)
                elif operator == "<":
                    filtered_query = filtered_query.where(column < value)
                elif operator == "<=":
                    filtered_query = filtered_query.where(column <= value)
                elif operator == "like":
                    filtered_query = filtered_query.where(column.like(value))
                elif operator == "ilike":
                    filtered_query = filtered_query.where(column.ilike(value))
                elif operator == "in":
                    filtered_query = filtered_query.where(column.in_(value))
                elif operator == "not_in":
                    filtered_query = filtered_query.where(column.not_in(value))

    count_query = select(sql_func.count()).select_from(filtered_query.subquery())

    # Apply pagination
    result_query = filtered_query

    # Apply offset if provided
    if offset is not None:
        result_query = result_query.offset(offset)

    # Apply limit if provided
    if limit is not None:
        result_query = result_query.limit(limit)

    # Apply ordering
    if order_by:
        if order_direction == SortDirection.ASC:
            result_query = result_query.order_by(order_by)
        else:
            result_query = result_query.order_by(desc(order_by))

    return result_query, count_query
