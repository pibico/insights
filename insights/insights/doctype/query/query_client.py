# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from json import dumps, loads
from copy import deepcopy
from pandas import DataFrame

import frappe
from frappe.utils import cstr, cint
from frappe.model.document import Document


class QueryClient(Document):
    @frappe.whitelist()
    def get_visualizations(self):
        return frappe.get_all(
            "Query Visualization",
            filters={"query": self.name},
            pluck="name",
        )

    @frappe.whitelist()
    def add_table(self, table):
        new_table = {
            "label": table.get("label"),
            "table": table.get("table"),
        }
        self.append("tables", new_table)
        self.save()

    @frappe.whitelist()
    def update_table(self, table):
        for row in self.tables:
            if row.get("name") != table.get("name"):
                continue

            if table.get("join"):
                row.join = dumps(
                    table.get("join"),
                    default=cstr,
                    indent=2,
                )
            else:
                row.join = ""

            self.save()
            return

    @frappe.whitelist()
    def remove_table(self, table):
        for row in self.tables:
            if row.get("name") == table.get("name"):
                self.remove(row)
                break

        self.save()

    @frappe.whitelist()
    def add_column(self, column):
        new_column = {
            "type": column.get("type"),
            "label": column.get("label"),
            "table": column.get("table"),
            "column": column.get("column"),
            "table_label": column.get("table_label"),
            "aggregation": column.get("aggregation"),
            "is_expression": column.get("is_expression"),
            "expression": dumps(column.get("expression"), default=cstr, indent=2),
        }
        self.append("columns", new_column)
        self.save()

    @frappe.whitelist()
    def move_column(self, from_index, to_index):
        self.columns.insert(to_index, self.columns.pop(from_index))
        for row in self.columns:
            row.idx = self.columns.index(row) + 1
        self.save()

    @frappe.whitelist()
    def update_column(self, column):
        for row in self.columns:
            if row.get("name") == column.get("name"):
                row.label = column.get("label")
                row.table = column.get("table")
                row.column = column.get("column")
                row.order_by = column.get("order_by")
                row.aggregation = column.get("aggregation")
                row.table_label = column.get("table_label")
                row.expression = dumps(column.get("expression"), indent=2)
                row.aggregation_condition = column.get("aggregation_condition")
                row.format_option = dumps(column.get("format_option"), indent=2)
                break

        self.save()

    @frappe.whitelist()
    def remove_column(self, column):
        for row in self.columns:
            if row.get("name") == column.get("name"):
                self.remove(row)
                break

        self.save()

    @frappe.whitelist()
    def update_filters(self, filters):
        sanitized_conditions = self.sanitize_conditions(filters.get("conditions"))
        filters["conditions"] = sanitized_conditions or []
        self.filters = dumps(filters, indent=2, default=cstr)
        self.save()

    def sanitize_conditions(self, conditions):
        if not conditions:
            return

        _conditions = deepcopy(conditions)

        for idx, condition in enumerate(_conditions):
            if "conditions" not in condition:
                # TODO: validate if condition is valid
                continue

            sanitized_conditions = self.sanitize_conditions(condition.get("conditions"))
            if sanitized_conditions:
                conditions[idx]["conditions"] = sanitized_conditions
            else:
                # remove the condition if it has zero conditions
                conditions.remove(condition)

        return conditions

    @frappe.whitelist()
    def apply_transform(self, type, data):
        self.transform_type = type
        self.transform_data = dumps(data, indent=2, default=cstr)
        if type == "Pivot":
            self.pivot(data)

        self.save()

    def pivot(self, transform_data):

        # TODO: validate if two columns doesn't have same label

        result = loads(self.result)
        columns = [d.get("label") for d in self.get("columns")]

        dataframe = DataFrame(columns=columns, data=result)
        pivoted = dataframe.pivot(
            index=transform_data.get("index_columns"),
            columns=transform_data.get("pivot_columns"),
        )

        self.transform_result = pivoted.to_html()
        self.transform_result = self.transform_result.replace("NaN", "-")

    @frappe.whitelist()
    def fetch_tables(self):
        _tables = []
        if not self.tables:

            def get_all_tables():
                return frappe.get_all(
                    "Table",
                    filters={"data_source": self.data_source},
                    fields=["table", "label"],
                    debug=True,
                )

            _tables = frappe.cache().get_value(
                f"query_tables_{self.data_source}", get_all_tables
            )

        else:
            tables = [d.table for d in self.tables]
            Table = frappe.qb.DocType("Table")
            TableLink = frappe.qb.DocType("Table Link")
            query = (
                frappe.qb.from_(Table)
                .from_(TableLink)
                .select(
                    TableLink.foreign_table.as_("table"),
                    TableLink.foreign_table_label.as_("label"),
                )
                .where((TableLink.parent == Table.name) & (Table.table.isin(tables)))
            )
            _tables = query.run(as_dict=True)

        return _tables

    @frappe.whitelist()
    def fetch_columns(self):
        if not self.tables:
            return []

        data_source = frappe.get_cached_doc("Data Source", self.data_source)
        columns = []
        join_tables = []
        for table in self.tables:
            if table.join:
                join = loads(table.join)
                join_tables.append(
                    {
                        "table": join.get("with").get("value"),
                        "label": join.get("with").get("label"),
                    }
                )

        for table in self.tables + join_tables:
            columns += data_source.get_columns(table)
        return columns

    @frappe.whitelist()
    def set_limit(self, limit):
        sanitized_limit = cint(limit)
        if not sanitized_limit or sanitized_limit < 0:
            frappe.throw("Limit must be a positive integer")
        self.limit = sanitized_limit
        self.save()

    @frappe.whitelist()
    def fetch_column_values(self, column, search_text):
        data_source = frappe.get_cached_doc("Data Source", self.data_source)
        return data_source.get_distinct_column_values(column, search_text)

    @frappe.whitelist()
    def fetch_operator_list(self, fieldtype=None):
        operator_list = [
            {"label": "equals", "value": "="},
            {"label": "not equals", "value": "!="},
            {"label": "is", "value": "is"},
        ]

        if not fieldtype:
            return operator_list

        text_data_types = ("char", "varchar", "enum", "text", "longtext")
        number_data_types = ("int", "decimal", "bigint", "float", "double")
        date_data_types = ("date", "datetime", "time", "timestamp")

        fieldtype = fieldtype.lower()
        if fieldtype in text_data_types:
            operator_list += [
                {"label": "contains", "value": "contains"},
                {"label": "not contains", "value": "not contains"},
                {"label": "starts with", "value": "starts with"},
                {"label": "ends with", "value": "ends with"},
                {"label": "is one of", "value": "in"},
                {"label": "is not one of", "value": "not in"},
            ]
        if fieldtype in number_data_types:
            operator_list += [
                {"label": "is one of", "value": "in"},
                {"label": "is not one of", "value": "not in"},
                {"label": "greater than", "value": ">"},
                {"label": "smaller than", "value": "<"},
                {"label": "greater than equal to", "value": ">="},
                {"label": "smaller than equal to", "value": "<="},
                {"label": "between", "value": "between"},
            ]

        if fieldtype in date_data_types:
            operator_list += [
                {"label": "greater than", "value": ">"},
                {"label": "smaller than", "value": "<"},
                {"label": "greater than equal to", "value": ">="},
                {"label": "smaller than equal to", "value": "<="},
                {"label": "between", "value": "between"},
                {"label": "within", "value": "timespan"},
            ]

        return operator_list

    @frappe.whitelist()
    def fetch_join_options(self, table):
        doc = frappe.get_cached_doc(
            "Table",
            {
                "table": table.get("table"),
                "data_source": self.data_source,
            },
        )

        return [
            {
                "key": d.foreign_key,
                "table": d.foreign_table,
                "label": d.foreign_table_label,
            }
            for d in doc.get("table_links")
        ]

    @frappe.whitelist()
    def run(self):
        self.execute()
        self.update_result()

        # skip processing and updating query since it's already done
        self.skip_before_save = True
        self.save()

    @frappe.whitelist()
    def reset(self):
        self.tables = []
        self.columns = []
        self.filters = dumps(
            {
                "group_operator": "&",
                "level": "1",
                "position": "1",
                "conditions": [],
            },
            indent=2,
        )
        self.sql = None
        self.result = None
        self.status = "Pending Execution"
        self.limit = 10
        self.execution_time = 0
        self.last_execution = None
        self.transform_type = None
        self.transform_data = None
        self.transform_result = None
        self.skip_before_save = True

        self.save()
