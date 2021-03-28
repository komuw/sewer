# windns - Windows DNSServer module

windns driver uses PowerShell DNSServer module for Let's Encrypt dns challenge.

Before reading further, [check the following link](https://docs.microsoft.com/en-us/powershell/module/dnsserver) to 
understand what this driver offers and how it works.

The driver uses a wrapper python library, which is called 
[windowsdnsserver-py](https://github.com/bilalekremharmansa/windowsdnsserver-py), to interact with PowerShell DnsServer
module. Basically, the driver performs process calls to DNSServer over python subprocess module. Since commands are
made on local machine (remote session is not supported), this driver has to be used on windows server
where dns server is located, either using sewer as a cli and as a library.

# Installation

DNSServer has any requirements but DNSServer module, which must be installed to PowerShell on windows server.

Microsoft documentation:
> DnsServer Module can be obtained either by installing DNS Server role or adding the DNS Server Tools part of
> Remote Server Administration Tools (RSAT) feature.

## Usage

windns driver needs to know which dns zone to put TXT record for dns challenge because DNSServer module
expects dns zone and dns name respectively. Nevertheless, domain should be provided to sewer as other dns drivers.

For instance, to start a dns challenge to "test.example.com" at zone "example.com", domain and zone should be defined
below;

    domain = test.example.com
    zone = example.com
    
If zone and domain are exactly same (both example.com), following definition work as well;

    domain = example.com
    zone = example.com 

### sewer-cli

    python3 -m sewer ... --provider=windns --p_opts zone=example.com

### sewer as library
    zone = "example.com"
    provider = WinDNS(zone)
    client = client.Client(domain="...", provider=provider, ...)


### Overriding default PowerShell path
 
windowsdnsserver-py uses the following PowerShell path to run commands; 

    'C:\Windows\syswow64\WindowsPowerShell\\v1.0\powershell.exe'

If you prefer sewer to use as library, you can always override this while creating dns provider instance like below;

    overrided_power_shell_path = '...'
    WinDNS(zone=..., power_shell_path=overrided_power_shell_path)

and if you prefer sewer-cli, the following parameters should work fine;

    python3 -m sewer ... --provider=windns --p_opts zone=example.com power_shell_path=C:\Program Files...

### One thing to be kept in mind while aliasing

Since ```zone``` parameter is getting used by the driver to put TXT record to correct zone on DNS challenge. You should
provide **the aliasing domain zone** which **CNAME points to**. Not that the domain that CNAME records live.

As an example; domain names are used in [sewer's aliasing](https://github.com/komuw/sewer/blob/master/docs/Aliasing.md)
documentation, you need to provide the following parameters;

    python3 -m sewer --domain name.example.com --provider=windns --p_opts zone=alias.org alias=alias.org

    
### If you installed DNSServer module and the driver is not able to initiate itself

If the error statement is like below, 

    DNSServer module seems it's not installed..
    
You should know that, if you are using 64 bit windows server, probably, there are two PowerShell variant on your
machine. One supports 64 bit and other one support 32 bit, PowerShell (x86). The driver uses 64 bit one as default
If you're comfortable to use 64 bit version, please, consider installing the DNSServer module to 64 bit one.
On the other hand, if you want to keep forward with 32 bit version, I suggest you to override PowerShell path for sewer,
which is mentioned in this document above.

----

**If you're problem is not related with that, you may want to create an issue about it.** 