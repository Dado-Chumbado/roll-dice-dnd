import re


async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative