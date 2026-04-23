def success(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}

def error(code, message):
    return {"code": code, "message": message, "data": None}
