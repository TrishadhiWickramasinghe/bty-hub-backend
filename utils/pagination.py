from typing import Any, Dict, List, Optional, Tuple
from fastapi import Query


class PaginationParams:
    """Pagination parameters handler"""
    
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(20, ge=1, le=100, description="Number of items to return (max 100)")
    ):
        self.skip = skip
        self.limit = limit
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dict for database queries"""
        return {"skip": self.skip, "limit": self.limit}


class SortParams:
    """Sorting parameters handler"""
    
    def __init__(
        self,
        sort_by: str = Query("created_at", description="Field to sort by"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order
    
    def to_tuple(self) -> Tuple[str, int]:
        """Convert to tuple for MongoDB sort"""
        direction = 1 if self.sort_order == "asc" else -1
        return (self.sort_by, direction)
    
    def get_direction_int(self) -> int:
        """Get sort direction as integer (1 for asc, -1 for desc)"""
        return 1 if self.sort_order == "asc" else -1


class FilterParams:
    """Base filtering parameters"""
    
    @staticmethod
    def build_search_query(search: Optional[str], search_fields: List[str]) -> Dict[str, Any]:
        """Build MongoDB search query for multiple fields"""
        if not search:
            return {}
        
        return {
            "$or": [
                {field: {"$regex": search, "$options": "i"}} 
                for field in search_fields
            ]
        }
    
    @staticmethod
    def build_range_query(
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        field_name: str = "price"
    ) -> Dict[str, Any]:
        """Build MongoDB range query"""
        if min_value is None and max_value is None:
            return {}
        
        query = {}
        if min_value is not None:
            query[f"{field_name}"] = {"$gte": min_value}
        if max_value is not None:
            if f"{field_name}" in query:
                query[f"{field_name}"]["$lte"] = max_value
            else:
                query[f"{field_name}"] = {"$lte": max_value}
        
        return query
    
    @staticmethod
    def build_date_range_query(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        field_name: str = "created_at"
    ) -> Dict[str, Any]:
        """Build MongoDB date range query"""
        if not start_date and not end_date:
            return {}
        
        from datetime import datetime
        query = {}
        
        if start_date:
            try:
                query[f"{field_name}"] = {"$gte": datetime.fromisoformat(start_date)}
            except:
                pass
        
        if end_date:
            try:
                dt = datetime.fromisoformat(end_date)
                if f"{field_name}" in query:
                    query[f"{field_name}"]["$lte"] = dt
                else:
                    query[f"{field_name}"] = {"$lte": dt}
            except:
                pass
        
        return query


class PaginatedResponse:
    """Paginated response wrapper"""
    
    def __init__(
        self,
        items: List[Any],
        total: int,
        skip: int,
        limit: int
    ):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
        self.page = (skip // limit) + 1 if limit > 0 else 1
        self.pages = (total + limit - 1) // limit if limit > 0 else 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON response"""
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "skip": self.skip,
                "limit": self.limit,
                "page": self.page,
                "pages": self.pages,
                "has_next": self.page < self.pages,
                "has_prev": self.page > 1
            }
        }
