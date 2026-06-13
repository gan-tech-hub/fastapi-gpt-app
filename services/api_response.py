from fastapi.responses import JSONResponse


def success_response(
    message: str,
    status_code: int = 200,
    meta: dict | None = None,
) -> JSONResponse:
    data = {"message": message}
    if meta is not None:
        data["meta"] = meta

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "error": None,
        },
    )


def error_response(code: str, message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )
