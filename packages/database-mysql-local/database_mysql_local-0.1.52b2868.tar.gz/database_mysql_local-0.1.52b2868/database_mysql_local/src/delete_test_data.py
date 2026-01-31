from .generic_crud_ml import GenericCRUDML
from mysql.connector import ProgrammingError

from .utils import generate_id_column_name  # noqa: E402

from .copy_table import copy_table

# init(autoreset=True) # Automatically resets style after every print

# TODO Check the number of records in the begging and in the end in all tables involved
# TODO Present graphically (character base) the recursive
# TODO Make sure all errors are in stderr and we have option to open Jira Work Items

# We can be both in safe mode and max_rows_to_delete is high, but we must get the approval of the user or -Force
# is_safe mode, if not, then if null or columns don't exist then we assume test data and delete
# double pointing, recursive pointing

# Need to implement recursive deleting in order for this to work
DEFAULT_MAX_ROWS_TO_DELETE = 999999  # Maximum number of rows to delete at once
is_show_progress = True  # is_debug, debug_mode


# TODO Do we need to inherit as we create a new class in the method
class DeleteTestData(GenericCRUDML):

    # the same method with the same name in the OurOpenSearch Class
    # TODO Should not delete the line with the lowest id (i.e. we want to keep the campaign with the lowest id which is is_test_data as this campaign is used for message-send-local-python)  # noqa: E501
    def delete_test_data(self,
                         entity_name: str,
                         schema_name: str = None,
                         table_name: str = None,
                         is_safe_mode: bool = True,
                         max_rows_to_delete_requested: int = None,
                         is_interactive: bool = True,
                         is_debug: bool = False):
        # TODO Shall we use self.default_schema_name or entity_name
        print(f"schema_name={schema_name} self.default_schema_name={self.default_schema_name}")
        schema_name = schema_name or self.default_schema_name
        table_name = table_name or self.default_table_name
        print(f"Deleting test data from table_name={table_name} with environment in the table name")
        if is_safe_mode:
            max_rows_to_delete = 1
            print("Safe mode is on.", end=" ")
        else:
            if (max_rows_to_delete_requested):
                max_rows_to_delete = max_rows_to_delete_requested
            else:
                max_rows_to_delete = DEFAULT_MAX_ROWS_TO_DELETE
            print("Safe mode is off.", end=" ")
        print("Setting max_rows_to_delete=" + str(max_rows_to_delete))
        # print('THIS IS THE CORRECT CODE')
        self.is_interactive = is_interactive
        if not self.is_interactive:
            is_safe_mode = True  # safe mode is to make sure that we delete in child tables ONLY records with is_test_data = 1

        # TODO do we need both to inherit and create instance? Why ML?
        gcrml = GenericCRUDML(default_entity_name=entity_name,
                              default_schema_name=schema_name,
                              default_table_name=table_name,
                              is_translate_object_name_per_environment=False)
        # original_schema_name = self.default_schema_name
        # original_table_name = self.default_table_name

        print(f"self.get_table_name={self.get_table_name()}")
        print(f"table_name={table_name} self.default_table_name={self.default_schema_name} gcrml.get_table_name()={gcrml.get_table_name()}")

        # get a list of all the referenced tables of the main table
        # TODO rename to references_to_column_query
        # TODO Why do we need the WHERE clause columns in the SELECT clause?
        select_query = """
            SELECT
              TABLE_SCHEMA,
              TABLE_NAME,
              COLUMN_NAME,
              CONSTRAINT_NAME,
              REFERENCED_TABLE_NAME,
              REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE
              REFERENCED_TABLE_NAME LIKE %s
              AND REFERENCED_COLUMN_NAME = %s
              AND TABLE_NAME != %s
        """
        # REFERENCES_TO_COLUMN_QUERY_TABLE_SCHEMA_INDEX = 0
        # REFERENCES_TO_COLUMN_QUERY_TABLE_NAME_INDEX = 1
        REFERENCES_TO_COLUMN_QUERY_COLUMN_NAME_INDEX = 2
        # REFERENCES_TO_COLUMN_QUERY_CONSTRAINT_NAME_INDEX = 3
        # REFERENCES_TO_COLUMN_QUERY_REFERENCED_TABLE_NAME_INDEX = 4
        # REFERENCES_TO_COLUMN_QUERY_REFERENCED_COLUMN_NAME_INDEX = 5

        id_column_name = generate_id_column_name(table_name)

        # params = (f'{schema_name}_table', id_column_name)
        params = (table_name, id_column_name, table_name)
        self.connection.commit()  # Ensure the connection is committed
        results = None
        try:
            print(f"Before executing {select_query} with params {params}")
            self.cursor.execute(select_query, params)
            results = self.cursor.fetchall()
        # 1451 "Cannot delete or update a parent row: a foreign key constraint fails" is ok
        except Exception as e:
            print(f"Error: {e} while executing {select_query} with params {params}")

        print(f"results={results}")
        if results is None:
            number_of_references = 0
        else:
            number_of_references = len(results)
        print(f"The number of references we have to table is {schema_name} {table_name} " + str(number_of_references), end=" ")  # print continue later

        # in MySQL Workbench when using 100,000 we got Lost Connection
        delete_where_is_test_data_true_query = f"DELETE FROM {schema_name}.{table_name} WHERE is_test_data=1 LIMIT 100000"
        if (results is None) or (len(results) == 0):
            print("")  # append to last print
            print("No references/foreign keys found. So we can try to do fast delete.")
            # Do to connection problem we limited to 100000, we need to build a loop around it
            print(f"delete_where_is_test_data_true_query={delete_where_is_test_data_true_query}")
            delete_where_is_test_data_true_execute_result = None
            try:
                delete_where_is_test_data_true_execute_result = self.cursor.execute(delete_where_is_test_data_true_query)
            except ProgrammingError as e:
                if e.errno == 1146:
                    print(f"Error: {e} while executing with references {delete_where_is_test_data_true_query}. We need to copy the table {table_name}.")
                    copy_table(source_schema_name=schema_name, source_table_name=table_name,
                               target_schema_name=gcrml.get_schema_name(), target_table_name=gcrml.get_table_name())
                else:
                    print(f"Error: {e} while executing with references {delete_where_is_test_data_true_query}")
            print(f"delete_where_is_test_data_true_execute_result={delete_where_is_test_data_true_execute_result}")
            self.connection.commit()
            # Shall we return or move the other code to else
            # We return something just that the test will not fail
            if delete_where_is_test_data_true_execute_result is None:
                delete_where_is_test_data_true_execute_result = 0
            return delete_where_is_test_data_true_execute_result
        else:
            column_name = results[REFERENCES_TO_COLUMN_QUERY_COLUMN_NAME_INDEX]
            print(f"column_name = {column_name}")  # append to last print
            # print("Found references. So we can't do fast delete. We need to do a loop around it. delete_where_is_test_data_true_query=" + delete_where_is_test_data_true_query)
            print("We try to delete also although there are references")
            try:
                delete_where_is_test_data_true_execute_result = self.cursor.execute(delete_where_is_test_data_true_query)
                print(f"delete_where_is_test_data_true_execute_result={delete_where_is_test_data_true_execute_result}")
            except ProgrammingError as e:
                if e.errno == 1054:
                    # print(f"Error: {e} while executing with references {delete_where_is_test_data_true_query}. This is ok as the column is_test_data doesn't exist in the table {table_name}")
                    print(f"As expected we can't DELETE FROM {schema_name}.{table_name} WHERE is_test_data=1 as there are foreign keys pointing to it.")
                else:
                    print(f"Error: {e} while executing with references {delete_where_is_test_data_true_query}")
            except Exception as e:
                print(f"Error: {e} while executing with references {delete_where_is_test_data_true_query}")

        # get a list of all the rows in the table which contain test data
        test_data_list = gcrml.select_multi_value_by_column_and_value(select_clause_value=id_column_name,
                                                                      column_name='is_test_data',
                                                                      column_value=1,
                                                                      limit=max_rows_to_delete,)

        to_delete = []
        schema_printed = {}
        # This can be very slow
        for row_id in test_data_list:
            if (is_show_progress and (row_id % 100 == 0)):
                # TODO Fore.YELLOW +
                print(f"\nschema_name={schema_name} table_name={table_name} row_id={row_id} ")
            for result in results:
                # There are always the same
                # if (is_show_progress):
                #     print(f"  schema[0]={result[0]}", end=None)
                #     print(f"  schema[1]={result[0]}", end=None)
                if not isinstance(result[1], str) and isinstance(result[1], bytearray):
                    result_table_name = result[1].decode()
                else:
                    result_table_name = result[1]

                if not isinstance(result[0], str) and isinstance(result[0], bytearray):
                    result_schema_name = result[0].decode()
                else:
                    result_schema_name = result[0]

                if (is_show_progress and result_schema_name not in schema_printed):
                    print(f"  schema={result_schema_name}", end=" ")
                    schema_printed[result_schema_name] = True
                    print(f"schema_printed1={schema_printed}")
                    print(f"result_schema_name1 not in schema_printed={result_schema_name} not in schema_printed")
                    # += can't work between dict and str
                    # schema_printed += result_table_name
                    # print(f"schema_printed2={schema_printed}")
                    # print(f"result_schema_name2 not in schema_printed={result_schema_name} not in schema_printed")
                gcrml1 = GenericCRUDML(default_entity_name=entity_name,
                                       default_schema_name=result_schema_name,
                                       default_table_name=result_table_name)
                # print(f"Changing the table name to {result[1]}")
                gcrml1.default_table_name = result_table_name
                if result_table_name.endswith('table'):
                    gcrml1.default_view_table_name = result_table_name.replace("table", "with_deleted_and_test_data_view")
                if result_table_name.endswith('old'):
                    # TODO {Fore.RED}
                    print(f"\n  Skipping {result_table_name} as it ends with old")
                    continue
                if is_safe_mode:
                    # global to_delete made this a comment for test purposes
                    try:
                        id_column_name = generate_id_column_name(result_table_name)
                        to_delete = gcrml1.select_multi_value_by_column_and_value(
                            select_clause_value="is_test_data",
                            column_name=id_column_name,
                            column_value=row_id,
                            view_table_name=gcrml1.default_view_table_name,
                            limit=max_rows_to_delete,)
                    except ProgrammingError as e:
                        if e.errno == 1054:
                            print(
                                f"The column is_test_data does not exist in {gcrml1.default_table_name}. This column will be added to the table now.")
                            try:
                                gcrml1.create_column(schema_name=gcrml1.default_schema_name,
                                                     table_name=gcrml1.default_table_name,
                                                     column_name='is_test_data',
                                                     data_type='TINYINT',
                                                     default_value=0)
                            except ProgrammingError as e:
                                try:
                                    print("exception: ", e)
                                    gcrml1.create_view()
                                except ProgrammingError as e:
                                    print("exception: ", e)
                                    continue

                            # TODO This code is duplicated. take it to a function.
                            to_delete = gcrml1.select_multi_value_by_column_and_value(select_clause_value="is_test_data",
                                                                                      column_name=id_column_name,
                                                                                      column_value=row_id,
                                                                                      view_table_name=gcrml1.default_view_table_name,
                                                                                      limit=max_rows_to_delete,)
                            continue
                        # TODO Change Magic Number to const/enum
                        elif e.errno == 1146:
                            print(f"Got 1146 error. At this point the default_schema_name is {gcrml1.default_schema_name}. Creating view {gcrml1.default_view_table_name}.")
                            gcrml1.create_view(
                                schema_name=gcrml1.default_schema_name,
                                table_name=gcrml1.default_table_name,
                                view_name=gcrml1.default_view_table_name,
                            )
                            # print(f"view_created: {gcrml1.default_view_table_name}")
                            to_delete = gcrml1.select_multi_value_by_column_and_value(select_clause_value="is_test_data",
                                                                                      column_name=id_column_name,
                                                                                      column_value=row_id,
                                                                                      view_table_name=gcrml1.default_view_table_name,
                                                                                      limit=max_rows_to_delete,)
                            continue
                    for entry in to_delete:
                        # TODO Change Magic Number 1 to const
                        if entry == 1:
                            delete_query = f"""
                            DELETE from {result_schema_name}.{result_table_name}
                            WHERE {result[2]} = {row_id} and is_test_data = 1;
                            """
                            if (is_show_progress and (row_id % 100 == 0)):
                                print("    entry1={entry} planning delete_query={delete_query}", end=None)
                            if self.is_interactive:
                                if self.ask_user_confirmation(delete_query) == 'yes':
                                    self.cursor.execute(delete_query)
                            else:
                                # print(delete_query)
                                self.cursor.execute(delete_query)

                            # TODO Why this is commented
                            # self.delete_test_data(
                            #     schema_name=result[0],
                            #     table_name=result[1],
                            #     is_safe_mode=True,
                            #     is_interactive=is_interactive,
                            # )
                        else:
                            print("ERROR: Trying to delete non-test-data")
                else:
                    to_delete = gcrml1.select_multi_value_by_column_and_value(select_clause_value=id_column_name,
                                                                              column_name=id_column_name,
                                                                              column_value=row_id,
                                                                              view_table_name=gcrml1.default_view_table_name,
                                                                              limit=max_rows_to_delete,)

                for entry in to_delete:
                    if (is_show_progress):
                        print(f"entry2={entry} ", end=None)
                    id_column_name = generate_id_column_name(result_table_name)
                    delete_query = f"""
                    DELETE from {result_schema_name}.{result_table_name}
                    WHERE {id_column_name} = {row_id};
                    """
                    # WHERE {original_schema_name}_id = {row_id};

                    if self.is_interactive:
                        if self.ask_user_confirmation(delete_query) == 'yes':
                            self.cursor.execute(delete_query)
                    else:
                        self.cursor.execute(delete_query)
            # If no errors, delete from the original table
            # delete_query = f"""DELETE from {original_schema_name}.{original_table_name} Where {original_schema_name}_id = {row_id};"""
            id_column_name = generate_id_column_name(table_name)
            delete_query = f"""DELETE from {schema_name}.{table_name} Where {id_column_name} = {row_id};"""
            if self.is_interactive:
                if self.ask_user_confirmation(delete_query) == 'yes':
                    self.cursor.execute(delete_query)
            else:
                if (is_show_progress and (row_id % 100 == 0)):
                    print(f"delete_query={delete_query}")
                self.cursor.execute(delete_query)
            if (row_id % 100 == 0):
                print(f"Committing after row_id={row_id}")
                self.connection.commit()
            if (is_debug):
                input("Continue?")

        self.connection.commit()

        delete_results = {}
        delete_results['schema_name'] = schema_name
        delete_results['table_name'] = table_name
        delete_results['deleted_rows'] = len(test_data_list)

        # TODO Run MySQL Optimizer to release the storage we deleted
        table_optimize_sql_statement = f"OPTIMIZE TABLE {schema_name}.{table_name}"
        self.cursor.execute(table_optimize_sql_statement)

        print(f"Deleted {delete_results['deleted_rows']} rows from {delete_results['schema_name']}.{delete_results['table_name']}")
        return delete_results

    def ask_user_confirmation(self, sql_query):
        global user_preference
        print(f"SQL Query:\n{sql_query}")
        user_choice = input("Do you want to execute this query? (yes/no/all): ").strip().lower()
        if user_choice in ['yes', 'no']:
            user_preference = (user_choice == 'yes')
            return user_preference
        elif user_choice in ['all']:
            self.is_interactive = False
        else:
            print("Invalid choice. Please enter 'yes' or 'no'.")
            message: str = self.ask_user_confirmation(sql_query)
            return message
