"""
Created on 2025-02-02

@author: wf
"""

class VarNameTracker:
    """
    Tracks variable names and ensures uniqueness by appending a suffix (_2, _3, etc.).
    """

    def __init__(self):
        self.var_name_count = {}

    def get_unique_name(self, base_name):
        """
        Get a unique variable name by appending a suffix if needed.
        """
        if base_name in self.var_name_count:
            self.var_name_count[base_name] += 1
            return f"{base_name}_{self.var_name_count[base_name]}"
        else:
            self.var_name_count[base_name] = 1
            return base_name

class QueryGen:
    """
    Generator for SPARQL queries based on property count query results.
    """

    def __init__(self, prefixes, debug: bool = False):
        """
        Initialize the QueryGen with a dictionary of prefixes.
        """
        self.prefixes = prefixes
        self.debug = debug

    def sanitize_variable_name(self, prop):
        """
        Convert a prefixed prop into a valid SPARQL variable name.
        """
        parts = prop.split(":")
        var_name = ""
        if parts:
            var_name = parts[-1]
            for invalid in ["-", ":", "#"]:
                var_name = var_name.replace(invalid, "_")
        var_name = f"{var_name}"
        return var_name

    def get_prefixed_property(self, prop):
        """
        Convert a full URI into a prefixed SPARQL property if a matching prefix is found.
        """
        prefixed_prop = f"<{prop}>"
        for prefix, uri in self.prefixes.items():
            # if self.debug:
            #    print(prop)
            #    print(uri)
            if prop.startswith(uri):
                prefixed_prop = prop.replace(uri, f"{prefix}:")
                break
        return prefixed_prop


    def gen(self, lod, main_var: str, main_value: str, first_x: int = None):
        """
        Generate a SPARQL query dynamically based on the lod results.
        """
        if first_x is None:
            first_x = 10**9 # a billion properties? should not happen
        sparql_query = "# generated Query"
        properties = {}
        tracker = VarNameTracker()
        for record in lod:
            if record["count"] == "1":
                prop = record["p"]
                prefixed_prop = self.get_prefixed_property(prop)
                base_var_name = self.sanitize_variable_name(prefixed_prop)
                var_name = tracker.get_unique_name(base_var_name)
                properties[var_name] = (prop, prefixed_prop)
        for key, value in self.prefixes.items():
            sparql_query += f"\nPREFIX {key}: <{value}>"

        sparql_query += f"\nSELECT ?{main_var}"

        for i, var_name in enumerate(properties.keys()):
            comment = "" if i < first_x else "#"
            sparql_query += f"\n{comment}  ?{var_name}"

        sparql_query += "\nWHERE {\n"

        sparql_query += f"  VALUES (?{main_var}) {{ ({main_value}) }}\n"
        sparql_query += "  OPTIONAL {\n"

        for i, (var_name, (prop, prefixed_prop)) in enumerate(properties.items()):
            comment = "" if i < first_x else "#"
            sparql_query += f"    # {prop}\n"
            sparql_query += f"   {comment} ?{main_var} {prefixed_prop} ?{var_name} .\n"

        sparql_query += "  }\n"  # Closing Optional clause
        sparql_query += "}"  # Closing WHERE clause

        return sparql_query
