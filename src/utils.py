import re

async def sanitize_input(data):
    if data == "+" or data == "-":
        data = ""
    data = data.replace("++", "+")
    data = data.replace("--", "-")
    return data

async def clean_dex(value):
    negative = True if "-" in value else False
    return int(re.sub('[^0-9]', '', value)), negative