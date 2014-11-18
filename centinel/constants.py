# constants for the centinel server


# constants for informed consent lookups
# lookup table to map country codes to freedom house pages
freedom_house_url_base = "http://www.freedomhouse.org/report/freedom-net/2012/"
freedom_house_lookup = {'AR': 'argentina', 'AU': 'australia', 'AZ': 'azerbaijan',
                        "BH": 'bahrain', "BY": 'belarus', "BR": 'brazil',
                        "CN": 'china', "CU": 'Cuba', "EG": 'Egypt',
                        "EE": 'estonia', "ET": 'Ethiopia', "GE": 'Georgia',
                        "DE": 'fermany', "HU": 'Hungary', "IN": 'India',
                        "ID": 'indonesia', "IR": 'Iran', "IT": 'Italy',
                        "JO": 'jordan', "KZ": 'Kazakhstan', "KE": 'Kenya',
                        "KG": 'krygyzstan', "LY": 'Libya', "MY": 'Malaysia',
                        "MX": 'mexico', "MM": 'burma', "NG": 'Nigeria',
                        "PK": 'Pakistan', "PH": 'Philippines', "RU": 'Russia',
                        "RW": 'Rwanda', "SA": 'Saudi-Arabia', "ZA": 'South-Africa',
                        "KR": 'South-Korea', "LK": 'Sri-Lanka', "SY": 'Syria',
                        "TH": 'Thailand', "TN": 'Tunisia', "TR": 'Turkey',
                        "UG": 'Uganda', "UA": 'Ukraine', "GB": 'United-Kingdom',
                        "US": 'United-States', "UZ": 'Uzbekistan',"VE": 'Venezuela',
                        "VN": 'Vietnam', "ZW": 'Zimbabwe'}
def freedom_house_url(country_code):
    return freedom_house_url_base + freedom_house_lookup[country_code]

# economist_url_base = "http://www.eiu.com/public/thankyou_download.aspx?activity=download&campaignid=DemocracyIndex12"
# economist_url_lookup =
# def economist_url(country_code):
#     return economist_url_base + economist_url_lookup.get(country_code)

canada_url_base = "http://travel.gc.ca/destinations/"
canada_url_lookup =  {'AR': 'argentina', 'AU': 'australia', 'AZ': 'azerbaijan',
                        "BH": 'bahrain', "BY": 'belarus', "BR": 'brazil',
                        "CN": 'china', "CU": 'Cuba', "EG": 'Egypt',
                        "EE": 'estonia', "ET": 'Ethiopia', "GE": 'Georgia',
                        "DE": 'fermany', "HU": 'Hungary', "IN": 'India',
                        "ID": 'indonesia', "IR": 'Iran', "IT": 'Italy',
                        "JO": 'jordan', "KZ": 'Kazakhstan', "KE": 'Kenya',
                        "KG": 'krygyzstan', "LY": 'Libya', "MY": 'Malaysia',
                        "MX": 'mexico', "MM": 'burma-myanmar', "NG": 'Nigeria',
                        "PK": 'Pakistan', "PH": 'Philippines', "RU": 'Russia',
                        "RW": 'Rwanda', "SA": 'Saudi-Arabia', "ZA": 'South-africa',
                        "KR": 'South-Korea', "LK": 'Sri-Lanka', "SY": 'Syria',
                        "TH": 'Thailand', "TN": 'Tunisia', "TR": 'Turkey',
                        "UG": 'Uganda', "UA": 'Ukraine', "GB": 'United-Kingdom',
                        "US": 'united-states', "UZ": 'Uzbekistan',"VE": 'Venezuela',
                        "VN": 'Vietnam', "ZW": 'Zimbabwe'}
def canada_url(country_code):
    return canada_url_base + canada_url_lookup[country_code]
