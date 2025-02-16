"""
Created on 2025-02-13

@author: wf
"""

import json

from ngwidgets.basetest import Basetest

from velorail.kgwalker import KGWalker


class TestKGWalker(Basetest):
    """
    test Knowledge Graph Walker
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_kg_walk(self):
        """
        Test exploring Madeira airport looking for specific property labels
        """
        test_cases = [
            ("named after", "P138"),  # entity that inspired the name
            ("OpenStreetMap way ID", "P10689"),  # identifier for OSM way
        ]
        prefix = "wd"
        node_id = "Q639161"  # Madeira Airport

        # get pids for query
        selected_props = [pid for _label, pid in test_cases]

        walker = KGWalker(endpoint_name="wikidata", debug=self.debug)
        view_record = walker.walk(
            prefix=prefix, node_id=node_id, selected_props=selected_props
        )

        # check that we got a result
        msg = "Expected view record but got None"
        self.assertIsNotNone(view_record, msg)

        if self.debug:
            print(json.dumps(view_record, indent=2, default=str))

        # verify each property is found with correct label
        for label, pid in test_cases:
            found = False
            for value in view_record.values():
                value_str = str(value)
                if label in value_str and pid in value_str:
                    found = True
                    break
            msg = f"Property {pid} with label {label} not found in view record"
            if self.debug:
                print(msg)
            # FIXME - enable this test
            # self.assertTrue(found, msg)
