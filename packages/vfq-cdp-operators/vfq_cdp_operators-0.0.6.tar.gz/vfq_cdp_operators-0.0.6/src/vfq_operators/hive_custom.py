from __future__ import annotations

from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.utils.context import Context
from typing import Any, Sequence
import re


class HiveSQLExecuteQueryOperator(SQLExecuteQueryOperator):
    
    template_ext: Sequence[str] = (".sql", ".hql", ".json")
    
    template_fields: Sequence[str] = (
        "sql", 
        "parameters", 
        "hql_parameters",
        "conn_id",
        "database",
        "hook_params"
    )
    
    def __init__(
        self,
        *,
        sql: str | list[str],
        hql_parameters: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(sql=sql, **kwargs)
        self.hql_parameters = hql_parameters or {}
    
    def _replace_hql_parameters(self, sql_content: str) -> str:
        if not self.hql_parameters:
            return sql_content
        
        pattern = r'\$\{([^}]+)\}'
        
        def replace_match(match):
            param_name = match.group(1).strip()
            if param_name in self.hql_parameters:
                return str(self.hql_parameters[param_name])
            else:
                self.log.warning(
                    f"Parameter '${{{param_name}}}' not found in hql_parameters. "
                    f"Keeping original value."
                )
                return match.group(0)
        
        return re.sub(pattern, replace_match, sql_content)
    
    def execute(self, context: Context):
        if isinstance(self.sql, str):

            self.sql = self._replace_hql_parameters(self.sql)

            self.sql = [
                statement.strip()
                for statement in self.sql.split(';')
                if statement.strip()
            ]
            
            self.split_statements = False
            
            self.log.info(
                "HQL Parameters replaced and split into %d statements", 
                len(self.sql)
            )
            for idx, stmt in enumerate(self.sql, 1):
                self.log.debug("Statement %d:\n%s", idx, stmt)
        
        elif isinstance(self.sql, list):
            processed_queries = []
            for query in self.sql:
                if not query.strip():
                    continue
                
                replaced = self._replace_hql_parameters(query)
                
                split_queries = [
                    stmt.strip() 
                    for stmt in replaced.split(';')
                    if stmt.strip()
                ]
                
                processed_queries.extend(split_queries)
            
            self.sql = processed_queries
            self.split_statements = False
            self.log.info("Processed %d total statements", len(self.sql))
        
        return super().execute(context)