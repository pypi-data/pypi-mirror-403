from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any

JsonDict = dict[str, Any]
JsonList = list[Any]
JsonMap = Mapping[str, Any]
MutJsonMap = MutableMapping[str, Any]
IterAny = Iterable[Any]

def convert_to_serializable(obj: Any) -> Any:
    """ Recursively convert objects to JSON-serializable forms.

\tObjects with a `to_dict()` or `asdict()` method are converted to their dictionary representation.
\tDictionaries and lists are recursively processed.

\tCan also be used to convert nested structures containing custom objects,
\tsuch as defaultdict, dataclasses, or other user-defined types.

\tArgs:
\t\tobj (Any): The object to convert
\tReturns:
\t\tAny: The JSON-serializable version of the object
\tExamples:
\t\t>>> from typing import defaultdict
\t\t>>> my_dict = defaultdict(lambda: defaultdict(int))
\t\t>>> my_dict['a']['b'] += 6
\t\t>>> my_dict['c']['d'] = 4
\t\t>>> my_dict['a']
\t\tdefaultdict(<class 'int'>, {'b': 6})
\t\t>>> my_dict['c']
\t\tdefaultdict(<class 'int'>, {'d': 4})
\t\t>>> convert_to_serializable(my_dict)
\t\t{'a': {'b': 6}, 'c': {'d': 4}}

\t\t>>> from dataclasses import dataclass
\t\t>>> @dataclass
\t\t... class Point:
\t\t...     x: int
\t\t...     y: int
\t\t>>> convert_to_serializable(Point(3, 4))
\t\t{'x': 3, 'y': 4}
\t"""
