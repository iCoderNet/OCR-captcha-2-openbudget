from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from predict import predict_full_captcha
from PIL import Image
from fastapi.encoders import jsonable_encoder
import io
import base64

app = FastAPI(title="OCR openbudget captcha solver")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detail = jsonable_encoder(exc.errors())
    first_msg = detail[0].get("msg", "Invalid input")
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": first_msg,
            "detail": detail
        }
    )


class OCRPayload(BaseModel):
    image: str 


@app.post("/ocr")
async def predict_ocr(payload: OCRPayload):
    try:
        image_data = base64.b64decode(payload.image)
        image = io.BytesIO(image_data)
        
        if len(image_data) > 1 * 1024 * 1024:
            return JSONResponse(status_code=413, content={"ok": False, "error": "Image too large"})

        result = predict_full_captcha(image)
        try: solution = eval(result)
        except (ValueError, SyntaxError): solution = None
        return {"ok": True, "text": result, "math_solution": solution}

    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8520)