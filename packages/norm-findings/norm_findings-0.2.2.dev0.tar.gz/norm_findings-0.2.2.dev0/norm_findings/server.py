import asyncio
import logging
import os
import tempfile

import aiofiles
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from starlette import status
from starlette.requests import Request

some_file_path = "large-video-file.mp4"
app = FastAPI()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@app.get('/alive')
def is_alive():
    return True


@app.post("/{parser}")
async def main(parser: str, request: Request, file_type: str):
    input_file_name = tempfile.mktemp() + f'.{file_type}'
    print(input_file_name)
    async with aiofiles.open(input_file_name, "wb") as afp:
        async for row in request.stream():
            await afp.write(row)
    result_file_name = tempfile.mktemp()
    proc = await asyncio.create_subprocess_exec(
        "python",
        'cli.py',
        'convert',
        '--parser', parser,
        '--input-file', input_file_name,
        '--output-file', result_file_name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
        )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error = f'process error: {stderr.decode()}'
        if stderr:
            error = stderr.decode()
        logger.error(error)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

    logger.debug(f'[exited with {proc.returncode}]')
    if stdout:
        logger.debug(f'[stdout]\n{stdout.decode()}')
    if stderr:
        logger.debug(f'[stderr]\n{stderr.decode()}')

    async def iterfile():  #
        try:
            async with aiofiles.open(result_file_name, "rb") as f:
                async for line in f:
                    yield line
        finally:
            # teardown, remove all files
            os.unlink(input_file_name)
            os.unlink(result_file_name)

    return StreamingResponse(iterfile())
