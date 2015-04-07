#
# Abbas Razaghpanah (arazaghpanah@cs.stonybrook.edu)
# March 2015, Stony Brook University
#
# as_info.py: a library to lookup AS number and AS owner information
# for IP addresses.
#

from netaddr import IPNetwork, IPAddress

class ASInfo:

    # using a cache is very useful since lookups are expensive
    cache = {}
    # array of prefix information
    pref_to_as = []
    # array AS number owner information
    as_info = {}

    def __init__(self, pref_to_as_file_address, as_info_file_address):
        self.as_info_file = open(as_info_file_address)
        self.pref_to_as_file = open(pref_to_as_file_address)
        self.pref_to_as = []
        for line in self.pref_to_as_file:
            line = line.strip()
            pref,asn  = line.split(None, 1)
            bits = int(pref.split('/')[1])
            self.pref_to_as.append({ 'net'  : IPNetwork(pref),
                         'bits' : bits,
                         'asn'  : int(asn)})

        self.as_info = {}
        for line in self.as_info_file:
            line = line.strip()
            asn, owner = line.split(None, 1)
            self.as_info[int(asn)] = owner

    def ip_to_asn(self, ip_address):
        # check if there's a cache hit
        if ip_address in self.cache:
            return self.cache[ip_address]

        result = None
        for row in self.pref_to_as:
            if IPAddress(ip_address) in row['net']:
                if result is None:
                    result = row
                    continue
                # replace if it is a longer match
                elif row['bits'] > result['bits']:
                    result = row

        if result is None:
            self.cache[ip_address] = 0
            return 0

        # cache it for later before returning
        self.cache[ip_address] = result['asn']
        return result['asn']

    def asn_to_owner(self, as_number):
        if int(as_number) < 1:
            raise Exception("Invalid AS number %s" % (as_number))
        return self.as_info[as_number]
