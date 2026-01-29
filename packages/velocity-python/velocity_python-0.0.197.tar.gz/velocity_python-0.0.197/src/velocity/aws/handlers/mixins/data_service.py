"""
DataServiceMixin - Generic CRUD operations for Lambda handlers.

Provides standard database operations that can be mixed into any Lambda handler
that uses velocity.db for database access.
"""

import base64
import datetime
import importlib
import logging
from io import BytesIO

from velocity.misc import export

logger = logging.getLogger(__name__)


class DataServiceMixin:
    """
    Mixin providing generic CRUD operations for Lambda handlers.
    
    This mixin assumes:
    - Handler uses velocity.db engine with @engine.transaction decorator
    - Handler has a context object with payload() and response() methods
    - Database tables follow standard conventions (sys_id primary key)
    
    Usage:
        from velocity.aws.handlers.mixins import DataServiceMixin
        
        @engine.transaction
        class HttpEventHandler(DataServiceMixin, LambdaHandler):
            def __init__(self, aws_event, aws_context):
                super().__init__(aws_event, aws_context)
    
    Override read_hook, write_hook, etc. methods to add custom business logic.
    """
    
    # PostgreSQL type mappings for frontend display
    _pg_types = {
        "bool": "string",
        "char": "string",
        "int2": "string",
        "int4": "string",
        "int8": "string",
        "text": "string",
        "numeric": "number",
        "float4": "number",
        "float8": "number",
        "varchar": "string",
        "date": "string",
        "time": "string",
        "timestamp": "string",
    }
    
    def _get_field_type(self, column_info):
        """Convert database column type to frontend display type"""
        return (
            "string"
            if column_info["name"] in ["id", "sys_id"]
            else self._pg_types.get(column_info["type_name"], "string")
        )
    
    def _call_rwx_hook(self, hook_name, table, *args, **kwargs):
        """
        Call a table-specific RWX hook if it exists.
        
        This method tries to load a hook from the rwx package and call it.
        If the hook doesn't exist, execution continues silently.
        
        Args:
            hook_name: Name of the hook (e.g., 'before_write', 'after_read')
            table: Table name (used to load table-specific module)
            *args: Arguments to pass to the hook
            **kwargs: Keyword arguments to pass to the hook
        """
        
        try:
            m = importlib.import_module(f".{table}", "rwx")
            if hasattr(m, hook_name):
                getattr(m, hook_name)(*args, **kwargs)
        except ImportError:
            # rwx package not available, continue without hooks
            pass
    
    # ========== Hook Methods (Override These) ==========
    
    def read_hook(self, tx, table, sys_id, context):
        row = {}
        if not sys_id:
            raise Exception("An object id was not provided for read operation")
        if sys_id == "@new":
            row = {}
            self._call_rwx_hook("on_new", "common", tx, table, row, context)
            self._call_rwx_hook("on_new", table, tx, table, row, context)
            return row
        sys_id = int(sys_id)
        self._call_rwx_hook("before_read", "common", tx, table, sys_id, context)
        self._call_rwx_hook("before_read", table, tx, table, sys_id, context)
        row = tx.table(table).find(sys_id)
        row = row.to_dict() if row else {}
        self._call_rwx_hook("after_read", "common", tx, table, sys_id, row, context)
        self._call_rwx_hook("after_read", table, tx, table, sys_id, row, context)
        return row

    def find_hook(self, tx, table, where, context):
        row = {}
        if not where:
            raise Exception("An query predicate was not provided for this read operation")
        self._call_rwx_hook("before_find", "common", tx, table, where, context)
        self._call_rwx_hook("before_find", table, tx, table, where, context)
        row = tx.table(table).find(where)
        self._call_rwx_hook("after_find", "common", tx, table, where, row, context)
        self._call_rwx_hook("after_find", table, tx, table, where, row, context)
        if row:
            row = row.to_dict()
        return row
    
    def write_hook(self, tx, table, sys_id, incoming, context):
        row = {}
        incoming.pop("sys_id", None)
        if sys_id == "@new":
            self._call_rwx_hook("before_new", "common", tx, table, sys_id, incoming, context)
            self._call_rwx_hook("before_new", table, tx, table, sys_id, incoming, context)
            row = tx.table(table).new()
            sys_id = row["sys_id"]
            self._call_rwx_hook("after_new", "common", tx, table, sys_id, row, context)
            self._call_rwx_hook("after_new", table, tx, table, sys_id, row, context)
        elif sys_id:
            sys_id = int(sys_id)
        else:
            raise Exception("Object sys_id was not supplied on write operation.")
        self._call_rwx_hook("before_write", "common", tx, table, sys_id, incoming, context)
        self._call_rwx_hook("before_write", table, tx, table, sys_id, incoming, context)
        if not row:
            row = tx.table(table).get(sys_id)
        row.update(incoming)
        self._call_rwx_hook("after_write", "common", tx, table, sys_id, row, context)
        self._call_rwx_hook("after_write", table, tx, table, sys_id, row, context)

        return row.to_dict()
    
    def query_hook(self, tx, table, payload, context):
        self._call_rwx_hook("before_query", "common", tx, table, payload, context)
        self._call_rwx_hook("before_query", table, tx, table, payload, context)
        params = payload.get("params", {})
        result = tx.table(payload["obj"]).select(**params)
        if payload.get("result_format") == "excel":
            data = {
                "headers": payload.get(
                    "headers", [x.replace("_", " ").title() for x in result.headers]
                ),
                "rows": result.as_list().all(),
            }
        else:
            data = {
                "rows": result.all(),
                "config": {
                    "lastFetch": datetime.datetime.now(),
                    "query": result.sql,
                    "format": payload.get("result_format"),
                },
            }
        if payload.get("count"):
            data["count"] = tx.table(payload["obj"]).count(where=params.get("where", None))
        if payload.get("headers"):
            data["columns"] = [
                {
                    "field": x["name"],
                    "headerName": x["name"].replace("_", " ").title(),
                    "type": self._get_field_type(x),
                }
                for x in result.columns.values()
            ]
        self._call_rwx_hook("after_query", "common", tx, table, data, payload, context)
        self._call_rwx_hook("after_query", table, tx, table, data, payload, context)
        return data
    
    def delete_hook(self, tx, table, sys_id, context):
        if sys_id:
            sys_id = int(sys_id)
            self._call_rwx_hook("before_delete", "common", tx, table, sys_id, context)
            self._call_rwx_hook("before_delete", table, tx, table, sys_id, context)
            row = tx.table(table).find(sys_id)
            if row:
                row.clear()
            self._call_rwx_hook("after_delete", "common", tx, table, sys_id, context)
            self._call_rwx_hook("after_delete", table, tx, table, sys_id, context)

    
    # ========== CRUD Action Methods ==========
    
    def OnActionReadObject(self, tx, context):
        payload = context.payload()

        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "object" not in payload:
            raise ValueError("Missing required parameter 'object' in payload")

        table_name = payload["tableName"]
        obj = payload["object"]

        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not obj:
            raise ValueError("Parameter 'object' cannot be empty")

        row = self.read_hook(
            tx,
            table_name,
            obj.get("sys_id"),
            context,
        )
        
        context.response().set_body(
            {
                "object": row,
                "lastFetch": datetime.datetime.now(),
            }
        )
        if row:
            context.response().load_object(row)
        else:
            message = f"Object {obj.get('sys_id')} was not found in the database. You may create it as a new object."
            context.response().toast(message, "warning")

    def OnActionFindObject(self, tx, context):
        payload = context.payload()

        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "query" not in payload:
            raise ValueError("Missing required parameter 'query' in payload")

        table_name = payload["tableName"]
        query = payload["query"]

        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not query or "where" not in query:
            raise ValueError("Parameter 'query' must contain 'where' clause")

        row = self.find_hook(
            tx,
            table_name,
            query["where"],
            context,
        )
        context.response().set_body(
            {
                "object": row,
                "lastFetch": datetime.datetime.now(),
            }
        )
        context.response().load_object(row)

    def OnActionWriteObject(self, tx, context):
        payload = context.payload()

        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        if "object" not in payload:
            raise ValueError("Missing required parameter 'object' in payload")

        table_name = payload["tableName"]
        obj = payload["object"]

        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        if not obj or not isinstance(obj, dict):
            raise ValueError("Parameter 'object' must be a non-empty dictionary")

        # Ensure the object has at least some data
        incoming = obj.copy()
        if not any(value is not None for value in incoming.values()):
            raise ValueError("Parameter 'object' cannot contain only None values")

        logger.debug(
            "Writing to table",
            extra={
                "table_name": table_name,
                "sys_id": incoming.get("sys_id"),
                "object_keys": list(incoming.keys()),
            },
        )

        try:
            row = self.write_hook(
                tx,
                table_name,
                incoming.get("sys_id"),
                incoming,
                context,
            )

            if not row:
                logger.warning(
                    "write_hook returned empty row",
                    extra={"table_name": table_name},
                )
                row = {}

            context.response().set_body(
                {
                    "object": row,
                    "lastFetch": datetime.datetime.now(),
                }
            )
            logger.debug(
                "Successfully wrote to table",
                extra={"table_name": table_name},
            )

        except Exception as e:
            logger.error(
                "Error in OnActionWriteObject",
                extra={
                    "exception": str(e),
                    "table_name": table_name,
                    "incoming_keys": list(incoming.keys()),
                },
            )
            raise
        context.response().load_object(row)

    # Query a table for rows. If the requested result format is excel, then return the
    # data as a downloadedable excel file. If the requested result format is raw,
    # then return the data as rows for the application front end to handle as it wishes.
    # Otherwise, return the data as a dataset to be populated into a datatable,
    # and load the data into 'store.repo' as such.
    # @param self
    # @param tx
    # @param args
    # @param postdata
    # @param response
    #
    # Payload parameters

    def OnActionQuery(self, tx, context):
        payload = context.payload()

        # Validate required parameters
        if "obj" not in payload:
            raise ValueError("Missing required parameter 'obj' in payload")

        table = payload["obj"]
        if not table:
            raise ValueError("Parameter 'obj' cannot be empty")

        data = self.query_hook(tx, table, payload, context)
        if payload.get("result_format") == "excel":
            filebuffer = BytesIO()
            export.create_spreadsheet(data["headers"], data["rows"], filebuffer)
            context.response().file_download(
                {
                    "filename": payload.get("filename", "temp_file.xls"),
                    "data": base64.b64encode(filebuffer.getvalue()).decode(),
                }
            )
            return
        if payload.get("result_format") == "raw":
            context.response().set_body(data)
        else:
            context.response().set_table(
                {payload.get("datatable", payload.get("obj")): data}
            )

    def OnActionDeleteObject(self, tx, context):
        payload = context.payload()

        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")

        table_name = payload["tableName"]
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")

        table = tx.table(table_name)
        deleteList = []
        if "deleteList" in payload:
            deleteList.extend(payload.get("deleteList"))
        if "object" in payload:
            obj = payload["object"]
            if obj and obj.get("sys_id"):
                deleteList.append(obj.get("sys_id"))
        
        for sys_id in deleteList:
            self.delete_hook(tx, table_name, sys_id, context)
            
        if not (deleteList):
            context.response().toast(f"No items were selected.", "warning")
    
    def OnActionGetTables(self, tx, context):
        """Get list of all tables in the database."""
        context.response().set_body({"tables": tx.tables()})
    
    def OnActionUpdateRows(self, tx, context):
        """
        Update multiple rows with the same data.
        
        Payload:
            table: str - Table name
            updateData: dict - Data to update
            updateRows: list - List of sys_id values to update
        """
        payload = context.payload()
        
        # Validate required parameters
        required_fields = ["updateData", "updateRows", "table"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required parameter '{field}' in payload")
        
        data = payload["updateData"]
        rows = payload["updateRows"]
        table = payload["table"]
        
        if not table:
            raise ValueError("Parameter 'table' cannot be empty")
        if not rows:
            raise ValueError("Parameter 'updateRows' cannot be empty")
        
        t = tx.table(table)
        count = t.update(data, {"sys_id": rows})
        context.response().toast(f"Updated {count} item(s).", "success")
    
    def OnActionQueryDirect(self, tx, context):
        """
        Query table directly with velocity.db parameters.
        
        Payload:
            obj: str - Table name
            params: dict - Direct velocity.db select parameters
            result_format: str - 'excel', 'raw', or 'datatable' (default)
            count: bool - Include total count
            headers: bool - Include column metadata
        """
        payload = context.payload()
        
        # Validate required parameters
        if "obj" not in payload:
            raise ValueError("Missing required parameter 'obj' in payload")
        
        table_name = payload["obj"]
        if not table_name:
            raise ValueError("Parameter 'obj' cannot be empty")
        
        params = payload.get("params", {})
        
        if payload.get("result_format") == "excel":
            result = tx.table(table_name).select(**params)
            headers = payload.get(
                "headers", [x.replace("_", " ").title() for x in result.headers]
            )
            rows = result.as_list().all()
            filebuffer = BytesIO()
            export.create_spreadsheet(headers, rows, filebuffer)
            context.response().file_download({
                "filename": payload.get("filename", "temp_file.xls"),
                "data": base64.b64encode(filebuffer.getvalue()).decode(),
            })
            return
        
        result = tx.table(table_name).select(**params)
        data = {
            "rows": result.all(),
            "config": {
                "lastFetch": datetime.datetime.now(),
                "query": result.sql,
                "format": payload.get("result_format"),
            },
        }
        
        if payload.get("count"):
            data["count"] = tx.table(table_name).count(where=params.get("where", None))
        
        if payload.get("headers"):
            data["columns"] = [
                {
                    "field": x["name"],
                    "headerName": x["name"].replace("_", " ").title(),
                    "type": self._get_field_type(x),
                }
                for x in result.columns.values()
            ]
        
        if payload.get("result_format") == "raw":
            context.response().set_body(data)
        else:
            context.response().set_table({
                payload.get("datatable", payload.get("obj")): data
            })
    
    def OnActionGetTableSchema(self, tx, context):
        """
        Get table schema from information_schema.
        
        Payload:
            tableName: str - Name of the table
        """
        payload = context.payload()
        
        # Validate required parameters
        if "tableName" not in payload:
            raise ValueError("Missing required parameter 'tableName' in payload")
        
        table_name = payload["tableName"]
        if not table_name:
            raise ValueError("Parameter 'tableName' cannot be empty")
        
        try:
            # Query information_schema to get table schema
            schema_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale,
                    ordinal_position
                FROM information_schema.columns 
                WHERE table_name = %s 
                    AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            
            schema_data = tx.execute(schema_query, [table_name])
            
            if not schema_data:
                raise ValueError(
                    f"Table '{table_name}' not found or has no accessible columns"
                )
            
            context.response().set_table({
                table_name: {
                    "schema": schema_data.all(),
                }
            })
            
        except Exception as e:
            if hasattr(self, 'log'):
                self.log(
                    f"Error retrieving schema for table {table_name}: {str(e)}",
                    "OnActionGetTableSchema",
                )
            raise Exception(f"Failed to retrieve table schema: {str(e)}")

