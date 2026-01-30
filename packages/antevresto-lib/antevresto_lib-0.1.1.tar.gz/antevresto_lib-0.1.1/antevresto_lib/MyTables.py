from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query
from appwrite.permission import Permission
from appwrite.role import Role


client = Client()

client.set_endpoint("https://antevresto.gr/v1") \
    .set_project("696822e80038b3a0526a") \
    .set_key("standard_6a725a6c7feb8a03ce84c18f8807b259fe9d16b4f078d46b3cbb9ec2eae01fc45622147176096adab4ed441c42184d69073ebf6c04b01ac441ed543c1a7c9414b2a4d7f5a694fba846b457da758a865e9bc96ca441909d041a0fe43f6a5afbf7a477bc2c620b2aa4eca4868b0a1faa0ff9fac0c106e36e22d7a0bc4f50c0daf4")

tables_db = TablesDB(client)

tables_info = [
        {
            'name':'Users',
            'database_id':'679b4dba003c94a69c7e',
            'table_id':'67a0cecd0010f4634b15'
        },
        {
            'name':'Matches',
            'database_id':'679b4dba003c94a69c7e',
            'table_id':'67a0cec500061493d1a7'
        },
        {
            'name':'Questions',
            'database_id':'679b4dba003c94a69c7e',
            'table_id':'679b4e03003b5a963467'
        },
    ]

class AVTTable:

    def __init__(self, name: str):
        """Enter table name"""
        for col in tables_info:
            if name == col['name']:
                self.name = col['name']
                self.database_id = col['database_id']
                self.table_id = col['table_id']
        # check for misstyped collection name
        if not hasattr(self, "name"):
            raise ValueError("Wrong table name, the existing tables are: \"" + "\", \"".join([t['name'] for t in tables_info]) + "\"")


    # ------------------------------------------ GET ROWS ------------------------------------------  
    def list_rows(self, extraQueries = []):
        """
        Returns a list of all rows in the table. \n
        A list of extra queries can be given as an attribute. (Default: None)
        """
        result = tables_db.list_rows(
        database_id = self.database_id,
        table_id = self.table_id,
        queries = extraQueries, # optional
        transaction_id = None, # optional
        total = False # optional
        )

        return result


    # ------------------------------------------ GET TABLE ------------------------------------------ 
    def get_row(self, row_id):
        print("bababooey")
        return tables_db.get_row(self.database_id, self.table_id, row_id)
    

    
    # ------------------------------------------ UPDATE ROW ------------------------------------------ 
    def update_row(self, row_id, updated_values: dict[str, any], perm = None, ): # type: ignore
        """
        This function updates the row with id = "row_id".\n
        Only give the attributes you want to change and the new values in the form of a dictionary/json like so:\n
        {"attribute_1": new_value_1, "attribute_2": new_value_2, ...}
        Optional permissions array 
        """
        tables_db.update_row(
            database_id= self.database_id,
            table_id= self.table_id,
            row_id= row_id,
            data= updated_values,
            permissions = perm,
            transaction_id = None # optional
        )
    


    # ------------------------------------------ CREATE ROW ------------------------------------------ 
    def create_row(self, data: dict[str,any], appwrite_id = "unique()"): # type: ignore
        """
        A new row will be created with a unique id if not given. The data should be given in the form of a dictionary/json like so:\n
        {"attribute_1": value_1, "attribute_2": value_2, ...}
        """
        temp_data = data
        temp_data["uid"] = temp_data["uid"].zfill(6) 
        
        result = tables_db.create_row(
            self.database_id,
            self.table_id,
            appwrite_id,
            data
        )

        return result




    # ------------------------------------------ DELETE DOCUMENT ------------------------------------------ 
    def delete_row(self, row_id):
        tables_db.delete_row(
            self.database_id,
            self.table_id,
            row_id
        )
