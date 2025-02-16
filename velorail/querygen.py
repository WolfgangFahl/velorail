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

    def get_prefixed_property(self, prop: str) -> str:
        """
        Convert a full URI into a prefixed SPARQL property if a matching prefix is found.

        Args:
            prop (str): The full URI of the property.

        Returns:
            str: The prefixed property if a matching prefix is found, otherwise the original URI in angle brackets.
        """
        longest_match = None
        for prefix, uri in self.prefixes.items():
            if prop.startswith(uri) and (
                longest_match is None or len(uri) > len(longest_match)
            ):
                longest_match = uri
                best_prefix = prefix

        if longest_match:
            return prop.replace(longest_match, f"{best_prefix}:")

        return f"<{prop}>"

    def gen(
        self,
        lod,
        main_var: str,
        main_value: str,
        max_cardinality: int = None,
        first_x: int = None,
        comment_out: bool = False,
    ):
        """
        Generates a SPARQL query dynamically based on the provided list of dictionaries (lod).

        Args:
            lod (list[dict]): List of dictionaries containing property data.
            main_var (str): The main variable in the SPARQL query.
            main_value (str): The value assigned to the main variable.
            max_cardinality (int, optional): Maximum allowed cardinality for properties. Defaults to a large number.
            first_x (int, optional): Number of properties to include before commenting out the rest. Defaults to a large number.
            comment_out (bool, optional): If True, comments out properties that are filter by the first_x or max cardinality condition

        Returns:
            str: The generated SPARQL query as a string.
        """
        if first_x is None:
            first_x = 10**9  # a billion properties? should not happen
        if max_cardinality is None:
            max_cardinality = 10**16  # how much energy for the RAM to keep this?
        sparql_query = "# generated Query"
        properties = {}
        tracker = VarNameTracker()
        for i, record in enumerate(lod):
            prop = record["p"]
            # do we have an injected wikidata_property?
            wikidata_property = record.get("wikidata_property")
            prefixed_prop = self.get_prefixed_property(prop)
            base_var_name = self.sanitize_variable_name(prefixed_prop)
            var_name = tracker.get_unique_name(base_var_name)
            card = int(record.get("count", 1))
            comment = "" if i < first_x and card <= max_cardinality else "#"
            properties[var_name] = (
                prop,
                prefixed_prop,
                card,
                comment,
                wikidata_property,
            )
        for key, value in self.prefixes.items():
            sparql_query += f"\nPREFIX {key}: <{value}>"

        sparql_query += f"\nSELECT ?{main_var}"

        for i, (var_name, (prop, prefixed_prop, card, comment, wdp)) in enumerate(
            properties.items()
        ):
            if not (comment_out and comment):
                sparql_query += f"\n  {comment}?{var_name}"

        sparql_query += "\nWHERE {\n"

        sparql_query += f"  VALUES (?{main_var}) {{ ({main_value}) }}\n"
        sparql_query += "  OPTIONAL {\n"

        for i, (var_name, (prop, prefixed_prop, card, comment, wdp)) in enumerate(
            properties.items()
        ):
            if not (comment_out and comment):
                sparql_query += f"    # {prop}\n"
                if (
                    wdp
                ):  # label but not description to avoid url encoding and other issues like param length overrun
                    sparql_query += f"    # {wdp.plabel}\n"
                sparql_query += (
                    f"    {comment}?{main_var} {prefixed_prop} ?{var_name} .\n"
                )

        sparql_query += "  }\n"  # Closing Optional clause
        sparql_query += "}"  # Closing WHERE clause

        return sparql_query
