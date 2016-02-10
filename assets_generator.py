#!/usr/bin/python

import argparse
import csv
import codecs

import sqlalchemy

# These two classes were adopted from 
# https://docs.python.org/2/library/csv.html#examples
# UnicodeReader was slightly modified to return a DictReader
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")
        
class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.DictReader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return {k: unicode(v, "utf-8") for (k, v) in row.iteritems()}

    def __iter__(self):
        return self

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=["tables", "model", "yamls"])
    args = parser.parse_args()
    
    if args.job == "tables":
        engine = sqlalchemy.create_engine('sqlite:////var/local/openapc_cubes/cubes.sqlite')
        create_openapc_cubes_tables(engine, "apc_de.csv")
    elif args.job == "model":
        generate_model_file()
    elif args.job == "yamls":
        generate_yamls()
        
        
def init_table(table, fields, create_id=False):
    
    type_map = {"integer": sqlalchemy.Integer,
                "float": sqlalchemy.Numeric,
                "string": sqlalchemy.String(256),
                "text": sqlalchemy.Text,
                "date": sqlalchemy.Text,
                "boolean": sqlalchemy.Integer}
    
    if create_id:
        col = sqlalchemy.schema.Column('id', sqlalchemy.Integer, primary_key=True)
        table.append_column(col)

    for (field_name, field_type) in fields:
        col = sqlalchemy.schema.Column(field_name, type_map[field_type.lower()])
        table.append_column(col)

    table.create()

def create_openapc_cubes_tables(connectable, file_name, schema=None):
    
    fields = [
        ("institution", "string"),
        ("period", "string"),
        ("euro", "float"),
        ("doi", "string"),
        ("is_hybrid", "string"),
        ("publisher", "string"),
        ("journal_full_title", "string"),
        ("issn", "string"),
        ("issn_print", "string"),
        ("issn_electronic", "string"),
        ("license_ref", "string"),
        ("indexed_in_crossref", "string"),
        ("pmid", "string"),
        ("pmcid", "string"),
        ("ut", "string"),
        ("url", "string"),
        ("doaj", "string"),
    ]

    metadata = sqlalchemy.MetaData(bind=connectable)
    
    full_table = sqlalchemy.Table("openapc", metadata, autoload=False, schema=schema)
    if full_table.exists():
        full_table.drop(checkfirst=False)
    init_table(full_table, fields)
    openapc_insert_command = full_table.insert()
    
    # a dict to store individual insert commands for every table
    tables_insert_commands = {
        "openapc": openapc_insert_command
    }
    
    reader = UnicodeReader(open("static/institutions.csv", "rb"))
    for row in reader:
        cubes_name = row["institution_cubes_name"]
        institution_name = row["institution"]
        if institution_name not in tables_insert_commands:
            table = sqlalchemy.Table(cubes_name, metadata, autoload=False, schema=schema)
            if table.exists():
                table.drop(checkfirst=False)
            init_table(table, fields)
            insert_command = table.insert()
            tables_insert_commands[institution_name] = insert_command
    
    reader = UnicodeReader(open(file_name, "rb"))
    for row in reader:
        institution = row["institution"]
        tables_insert_commands[institution].execute(row)
        tables_insert_commands["openapc"].execute(row)

def generate_model_file():
    content = u""
    with open("static/templates/MODEL_FIRST_PART", "r") as model:
        content += model.read()
        
    with open("static/templates/MODEL_CUBE_STATIC_PART", "r") as model:
        static_part = model.read()

    reader = UnicodeReader(open("static/institutions.csv", "rb"))
    for row in reader:
        content += u"        ,\n        {\n"
        content += u'            "name": "{}",\n'.format((row["institution_cubes_name"]))
        content += u'            "label": "{} openAPC data cube",\n'.format((row["institution_full_name"]))
        content += static_part
        
    with open("static/templates/MODEL_LAST_PART", "r") as model:
        content += model.read()
    
    with open("model.json", "w") as model:
        model.write(content.encode("utf-8"))
        
def generate_yamls():
    with open("static/templates/YAML_STATIC_PART", "r") as yaml:
        yaml_static = yaml.read()
    
    reader = UnicodeReader(open("static/institutions.csv", "rb"))
    for row in reader:
        content = u"name: " + row["institution_full_name"] + u"\n"
        content += u"slug: " + row["institution_cubes_name"] + u"\n"
        content += u"tagline: " + row["institution_full_name"] + u" APC data\n"
        content += u"source: Open APC\n"
        content += u"source_url: https://github.com/OpenAPC/openapc-de\n"
        content += u"data_url: https://github.com/OpenAPC/openapc-de/blob/master/data/apc_de.csv\n" 
        content += u"state: " + row["state"] + u"\n"
        content += u"level: kommune\n"
        content += u"dataset: '" + row["institution_cubes_name"] + "'\n"
        content += yaml_static
        
        out_file_name = row["institution_cubes_name"] + ".yaml"
        with open(out_file_name, "w") as outfile:
            outfile.write(content.encode("utf-8"))

if __name__ == '__main__':
    main()