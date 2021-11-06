async def check_if_num(input, max_len):
    try:
        int(input)
    except:
        return False
    return len(input) <= max_len
    