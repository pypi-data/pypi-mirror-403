# ecl-api

[![PyPI - Version](https://img.shields.io/pypi/v/ecl-api.svg)](https://pypi.org/project/ecl-api)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ecl-api.svg)](https://pypi.org/project/ecl-api)
![pylint](https://github.com/marcodeltutto/ecl-api/actions/workflows/pylint.yml/badge.svg)

-----

The Electronic Collaboration Logbook ([ECL](https://cdcvs.fnal.gov/redmine/projects/crl)) is an e-logbook used at FNAL. This package allows retrieving and posting entries via Python using the ECL [XML/REST API](https://cdcvs.fnal.gov/redmine/projects/crl/wiki/ECL_XML_API).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install ecl-api
```

## Usage

Start a connection with the ECL:

```python
from ecl_api import ECL, ECLEntry

password = "your_ecl_pwd"
url = "your_ecl_link" # e.g. 'https://dbweb9.fnal.gov:8443/ECL/sbnd/E'

ecl = ECL(url=url, user='sbndprm', password=password)
```

Post a generic entry:
```python
entry = ECLEntry(category='Purity Monitors', text='Example text', preformatted=True)

entry.add_image(name='Image Name', filename='/path/to/image.png')

ecl.post(entry, do_post=False)
```

Post a form:
```python
entry = ECLEntry(category='Shift', formname='Shift run start checklist - v1')

form = {
    "Maximize the window": "Yes",
    "Date": "07/23/24",
    "Time": "19:39:58",
    "Run number": "00000",
    "DAQ Components": "testentry",
    "Configuration": "testentry" 
}

entry.set_form_elements(form)

print(entry.show(pretty=True))

ecl.post(entry, do_post=False)
```

Retrieve an entry
```python

ecl.get_entry(entry_id=7252)
```

Retrieve the last N entries in a certain category

```python
text = ecl.search(category='Shift', limit=3)
```

Unpack content of `text`:
```python
import xml.etree.ElementTree as ET

xml = ET.fromstring(text)
entries = xml.findall('./entry')
for entry in entries:
	print(entry.attrib, entry.tag)
	...
```


## License

`ecl-api` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
