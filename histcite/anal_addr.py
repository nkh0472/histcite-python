"""This module is used to analyse the Address info.

Only support WOS data:
- I2
- CO
"""

def SumAddrInfo(df, column='I2'):
    def merge_lists(row):
        # Merge a list without duplicates
        return set([sublist.strip() for sublist in row])

    result = sorted(set().union(*df[column].apply(merge_lists)))
    return result
