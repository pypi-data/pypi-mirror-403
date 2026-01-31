from .generic_crud_mysql import GenericCrudMysql


def copy_table_definition(source_schema_name: str, source_table_name: str,
                          target_schema_name: str, target_table_name: str,
                          where_clause: str = None):
    entity_name = source_table_name

    generic_crud = GenericCrudMysql(default_entity_name=entity_name,
                                    default_schema_name=source_schema_name,
                                    default_table_name=source_table_name)
    print(f"copy_table.py copy_table_definition() before CREATE SCHEMA IF NOT EXISTS {target_schema_name}")
    generic_crud.cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {target_schema_name};")
    generic_crud.cursor.execute(f"CREATE TABLE {target_schema_name}.{target_table_name} LIKE {source_schema_name}.{source_table_name};")


def copy_table_data(source_schema_name: str, source_table_name: str,
                    target_schema_name: str, target_table_name: str,
                    where_clause: str = None):
    # TODO we should use get_entity_name()
    entity_name = source_table_name

    generic_crud = GenericCrudMysql(default_entity_name=entity_name,
                                    default_schema_name=source_schema_name,
                                    default_table_name=source_table_name)
    generic_crud.cursor.execute(f"INSERT INTO {target_schema_name}.{target_table_name} SELECT * FROM {source_schema_name}.{source_table_name};")


def copy_table(source_schema_name: str, source_table_name: str,
               target_schema_name: str, target_table_name: str,
               where_clause: str = None):
    copy_table_definition(source_schema_name, source_table_name,
                          target_schema_name, target_table_name, where_clause)
    copy_table_data(source_schema_name, source_table_name, target_schema_name,
                    target_table_name, where_clause)
