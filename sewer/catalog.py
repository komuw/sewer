import codecs, importlib, json, os
from typing import Dict, List, Sequence

from .auth import ProviderBase


class ProviderDescriptor:
    def __init__(
        self,
        *,
        name: str,
        desc: str,
        chals: Sequence[str],
        args: Sequence[Dict[str, str]],
        deps: Sequence[str],
        path: str = None,
        cls: str = None,
        features: Sequence[str] = None,
        memo: str = None,
    ) -> None:
        "initialize a driver descriptor from one item in the catalog"

        self.name = name
        self.desc = desc
        self.chals = chals
        self.args = args
        self.deps = deps
        self.path = path
        self.cls = cls
        self.features = [] if features is None else features
        self.memo = memo

    def __str__(self) -> str:
        return "Descriptor %s" % self.name

    def get_provider(self) -> ProviderBase:
        "return the class that implements this driver"

        module_name = self.path if self.path else ("sewer.providers." + self.name)
        module = importlib.import_module(module_name)
        return getattr(module, self.cls if self.cls else "Provider")


class ProviderCatalog:
    def __init__(self, filepath: str = "") -> None:
        "intialize a catalog from either the default catalog.json or one named by filepath"

        if not filepath:
            here = os.path.abspath(os.path.dirname(__file__))
            filepath = os.path.join(here, "catalog.json")
        with codecs.open(filepath, "r", encoding="utf8") as f:
            raw_catalog = json.load(f)

        items = {}  # type: Dict[str, ProviderDescriptor]
        for item in raw_catalog:
            k = item["name"]
            if k in items:
                print("WARNING: duplicate name %s skipped in catalog %s" % (k, filepath))
            else:
                items[k] = ProviderDescriptor(**item)
        self.items = items

    def get_item_list(self) -> List[ProviderDescriptor]:
        "return the list of items in the catalog, sorted by name"

        res = [i for i in self.items.values()]
        res.sort(key=lambda i: i.name)
        return res

    def get_descriptor(self, name: str) -> ProviderDescriptor:
        "return the ProviderDescriptor that matches name"

        return self.items[name]

    def get_provider(self, name: str) -> ProviderBase:
        "return the class that implements the named driver"

        return self.get_descriptor(name).get_provider()
