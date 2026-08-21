# NAS 업로드 중계 서버

안드로이드 앱이 NAS(Synology File Station API)에 직접 말 거는 대신,
이 서버에만 파일을 보내면, 이 서버가 공식 `synology-api` 라이브러리를 통해
대신 NAS에 업로드합니다.

```
[안드로이드 앱] --파일만 전달--> [이 서버] --synology-api(검증된 방식)--> [NAS]
```

---

## Render에 배포하는 방법

1. 이 폴더(`relay_server`)를 GitHub 저장소에 올리기 (새 저장소 하나 만들어서 push)
2. [render.com](https://render.com) 접속 → **New** → **Web Service**
3. 방금 만든 GitHub 저장소 연결
4. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment** 탭에서 아래 값들 추가:

| 키 | 값 |
|---|---|
| `NAS_HOST` | `nnl-lab.synology.me` |
| `NAS_PORT` | `33001` |
| `NAS_ACCOUNT` | `api-uploader` |
| `NAS_PASSWORD` | (api-uploader 계정 비밀번호) |
| `RELAY_SECRET` | 아무 문자열이나 직접 정하기 (예: 랜덤 문자열 20자 이상) — 안드로이드 앱 코드에도 동일하게 넣어야 함 |

6. 배포 완료되면 `https://무언가.onrender.com` 같은 주소가 생성됩니다. 이 주소를 안드로이드 앱의 `RELAY_URL`에 넣으면 됩니다.

---

## 동작 확인

배포 후 브라우저에서 `https://그주소/health` 접속했을 때 `{"status":"ok"}`가 뜨면 정상입니다.

## 참고

- 이 서버는 [공식 synology-api 라이브러리](https://github.com/N4S4/synology-api)의 `FileStation` 클래스를 사용합니다. 직접 만든 requests 코드 대신 이미 검증된 패키지를 씁니다.
- Render 무료 플랜은 일정 시간 요청이 없으면 서버가 잠들었다가, 다음 요청이 올 때 다시 깨어나는 데 몇십 초 걸릴 수 있습니다.
- `RELAY_SECRET`은 아무나 이 서버를 통해 NAS에 파일을 올리지 못하도록 막는 최소한의 보안 장치입니다. 외부에 노출되지 않게 주의하세요.
