# The Catalog of Drivers

The driver catalog, `sewer/catalog.json`, replaces scattered facilities that
were used to stitch things together.  The import farms in `sewer.__init__`
and `sewer.dns_providers.__init__` have already been removed; with the
catalog in place, redundant lists in cli.py and setup.py are also removed,
replaced by use of the catalog's data and a few lines of code.  The
`dns_provider_name` is deprecated in favor of the catalog as well.

`catalog.py` wraps the catalog in a class, adding some convenience methods
for listing the known drivers, looking up a driver's data by name, and
loading a driver's implementation class by name.  But using the catalog
without `catalog.py` is as easy as loading it using the standard lib's json
facilities - it's all lists & dicts (see eg. setup.py which loads the
catalog this way to avoid potential issues with trying to call into the
package's code before it's installed).

## Catalog structure

The catalog resides in a JSON file that loads as an array of dictionaries,
one element for each registered driver.  The per-driver record contains the
following items (some optional):

- **name** The name used to identify this driver, eg., `--provider <name>`
  to `sewer-cli`.  These names need to be unique, but are not required to
  match the module or implementing class names.  (legacy DNS drivers usually
  matched the module name, but not always)
- **desc** A brief description of the driver, intended for display to humans
  to help them understand what each driver is, eg. in --known_providers output
- **chals** list of strings for the type of challenge(s) this driver
  handles.  (if more than one type, in order of preference?)
- **args** A list of the driver-specific [parameters](#args-parameter-descriptors)
- **path** The path to use to import the driver's Python module.
  _Default_ is `sewer.providers.{name}`
- **cls** Name of module attribute which is called with parameters to get a
  working instance of the driver.  Usually a class, but a factory function
  may be used.  _Default_ is `Provider`.
- **features** - a list of strings that name the optional features that this
  driver supports.  _Default_ is an empty list.
- **memo** Additional text/comments about the driver, the descriptor, etc.
- **deps** list of additional projects this driver requires (for setup)

## args - parameter desciptors

This is a bit of a mess due to legacy drivers that ignored the established
conventions.  To be fair to them, those conventions weren't clearly
documented (then - see below).  This adds some complications to preserve
compatibility, as usual.  Let's begin with a minimal descriptor for a driver
that conforms to the new convention (hint: it's imaginary at this time):

    {
      "name": "well_behaved",
      "desc": "made-up example driver that's mostly defaults",
      "chals": ["dns-01"],
      "args": [
        { "name": "api_id", "req": 1 },
        { "name": "api_key", "req": 1},
      ],
      "features": [ "alias" ],
    }

This describes a dns-01 challenge driver that is found in the module
`sewer.providers.well_behaved`, constructed from a class named `Provider`.
The constructor takes two required arguments, `api_id` and `api_key`, which
the program should accept from environment variables `WELL_BEHAVED_API_ID"
and "WELL_BEHAVED_API_KEY".  Since it is a `dns-01` challenge provider and
up to date, it adds the claim that it supports the `alias` feature.  It
doesn't support the "unpropagated" feature - perhaps the DNS service has no
API to check the propagation of changes.

If this had been a difficult old legacy driver, the descriptor might have
looked more like this:

    {
      "name": "difficult",
      "desc": "made-up example driver that's as non-default as can be",
      "chals": ["dns-01"],
      "args": [
        { "name": "api_id",
          "req": 1,
          "param": "difficult_api_id",
          "envvar": "DIFFICULT_DNS_API_ID",
        },
        { "name": "api_key",
          "req": 1,
          "param": "DIFFICULT_API_KEY",
          "envvar": "DIFFICULT_DNS_API_KEY"},
        },
	{ "name": "api_base_url",
	  "param": "API_BASE_URL",
	  "envvar": "",
	},
      ],
      "path": "sewer.dns_providers.difficultdns",
      "cls": "DifficultDNSDns",
      "features": [],
      "memo", "difficult, indeed..."
    }

This driver has both parameter names and envvar names that defy convention,
so both the parameter and envvar name must be given explicitly.  There is
also an optional parameter that has never had an associated envvar that the
implementation used.

## driver parameter and environment variable names

The convention is that the envvar name (if any) SHOULD be formed from the
driver name and the individual args' names (see the first envvar rule
below).  This gives envvar names similar to, sometimes identical to, the
ones already used with legacy DNS drivers.  One thing that is changing is
that the parameter names, which in the old convention were
THE_SAME_AS_ENVVAR_NAMES, are changing to be lower case and losing
driver-name prefixes, etc.  Where appropriate, the new names will use just a
few shared names, viz., `id`, `key`, `token`.

Obviously the drivers and envvar names are not so consistent among the
legacy DNS drivers.  Therefore the descriptor has both `param` and `envvar`
values, along with a set of rules for resolving the names to be used.

### parameter name rules

1. `descriptor.args[n].name` is the "modern" name for the nth parameter
2. if `param` is given, it overrides the "modern" name

### environment name rules

1. f"{descriptor.name}_{descriptor.args[n].name}".upper() is the default
2. if `envvar` is given, it overrides the default

Two guidelines for the use of envvars:

1. If `envvar` is given, is not the empty string, and the so-named envvar is
   not found, the invoking code MAY also look for the default-named envvar
   before reporting a missing envvar.

2. If `envvar` is set to the empty string, then catalog using code will not
   look for a matching envvar at all.

## catalog representation in Python

For now, see the brief implementation in sewer/catalog.py for the way the
JSON structure is mapped into a ProviderDescriptor instance.
