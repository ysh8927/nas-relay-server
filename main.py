# -*- coding: utf-8 -*-
"""
main.py — 안드로이드 앱 <-> NAS 사이의 중계 서버

안드로이드 앱은 이 서버에만 파일을 보내고, 이 서버가 공식 synology-api
라이브러리(FileStation 클래스)를 통해 NAS에 업로드합니다.

배포: Render (무료 웹 서비스)
    빌드 명령어: pip install -r requirements.txt
    시작 명령어: uvicorn main:app --host 0.0.0.0 --port $PORT

필요한 환경변수 (Render 대시보드 > Environment 에서 설정):
    NAS_HOST            예: nnl-lab.synology.me
    NAS_PORT            예: 33001
    NAS_ACCOUNT         예: api-uploader
    NAS_PASSWORD        api-uploader 계정 비밀번호
    RELAY_SECRET        안드로이드 앱과 이 서버만 아는 비밀 값
    RAW_UPLOADS_ROOT    기본값 /raw_uploads (안 바꿔도 됨)
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from synology_api.filestation import FileStation

app = FastAPI()

NAS_HOST = os.environ["NAS_HOST"]
NAS_PORT = os.environ["NAS_PORT"]
NAS_ACCOUNT = os.environ["NAS_ACCOUNT"]
NAS_PASSWORD = os.environ["NAS_PASSWORD"]
RELAY_SECRET = os.environ["RELAY_SECRET"]
RAW_UPLOADS_ROOT = os.environ.get("RAW_UPLOADS_ROOT", "/raw_uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    project: str = Form("기타"),
    x_relay_secret: str = Header(...),
):
    if x_relay_secret != RELAY_SECRET:
        raise HTTPException(status_code=403, detail="인증 실패")

    remote_folder = f"{RAW_UPLOADS_ROOT}/{project}"

    tmp_path = None
    try:
        # synology-api의 upload_file은 로컬 파일 경로를 받으므로
        # 업로드된 파일을 잠깐 원래 파일명 그대로 임시 폴더에 저장한다.
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, file.filename)
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        fs = FileStation(
            NAS_HOST,
            NAS_PORT,
            NAS_ACCOUNT,
            NAS_PASSWORD,
            secure=True,
            cert_verify=True,
            dsm_version=7,
            debug=False,
        )

        result = fs.upload_file(
            remote_folder,
            tmp_path,
            create_parents=True,
            overwrite=True,
        )

        # synology-api는 실패 시 문자열(에러메시지) 또는 (code, dict)를 반환하고,
        # 성공 시 dict를 반환하는 경우가 많으므로 형태를 보고 판단한다.
        if isinstance(result, str):
            raise RuntimeError(f"업로드 실패: {result}")
        if isinstance(result, tuple):
            raise RuntimeError(f"업로드 실패: {result}")
        if isinstance(result, dict) and result.get("success") is False:
            raise RuntimeError(f"업로드 실패: {result}")

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NAS 업로드 실패: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            try:
                os.rmdir(os.path.dirname(tmp_path))
            except OSError:
                pass

    return {"success": True, "remote_folder": remote_folder, "filename": file.filename}
