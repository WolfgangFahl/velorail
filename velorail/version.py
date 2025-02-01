"""
Created on 2025-02-01

@author: wf
"""
import velorail
from dataclasses import dataclass


@dataclass
class Version:
    """
    Version handling for velorail
    """

    name = "velorail"
    version = velorail.__version__
    date = "2025-02-01"
    updated = "2025-02-01"
    description = "Multimodal bike and train route planning support"

    authors = "Wolfgang Fahl"

    doc_url = "https://wiki.bitplan.com/index.php/velorail"
    chat_url = "https://github.com/WolfgangFahl/velorail/discussions"
    cm_url = "https://github.com/WolfgangFahl/velorail"

    license = f"""Copyright 2025 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""

    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
