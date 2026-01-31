from faker import Faker
import random

fake = Faker()

class DataGenerator:
    def __init__(self):
        pass

    def generate_row(self, columns):
        row = []
        for col in columns:
            val = self._generate_value(col['type'], col['name'])
            row.append(val)
        return tuple(row)

    def _generate_value(self, type_name, col_name):
        type_name = type_name.upper()
        
        # Heuristics based on column name for better realism
        lower_name = col_name.lower()
        if "email" in lower_name:
            return fake.email()
        if "name" in lower_name:
            return fake.name()
        if "address" in lower_name:
            return fake.address()
        if "phone" in lower_name:
            return fake.phone_number()
        
        # Type based generation
        if type_name in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT']:
            return fake.random_int(min=0, max=10000)
        elif type_name in ['VARCHAR', 'CHAR', 'TEXT']:
            return fake.text(max_nb_chars=50)
        elif type_name in ['DATE']:
            return fake.date_object()
        elif type_name in ['DATETIME', 'TIMESTAMP']:
            return fake.date_time()
        elif type_name in ['BOOLEAN', 'BOOL']:
            return fake.boolean()
        elif type_name in ['FLOAT', 'DOUBLE', 'DECIMAL']:
            return fake.pyfloat(right_digits=2, positive=True)
        
        return fake.word()
