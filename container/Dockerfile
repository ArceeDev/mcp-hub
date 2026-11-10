# Imagen del Cloudflare Container: los 5 MCP desde su rama main, servidos por uvicorn en :8080.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ARG REF=main
ARG CONTABRIDGE_VERSION=v0.4.0
RUN pip install --no-cache-dir "uvicorn>=0.30" \
    "web-intel-mcp @ git+https://github.com/ArceeDev/web-intel-mcp@${REF}" \
    "norma43-mcp @ git+https://github.com/ArceeDev/norma43-mcp@${REF}" \
    "contabridge-mcp @ git+https://github.com/ArceeDev/contabridge-mcp@${REF}" \
    "verifactu-keyflint-mcp @ git+https://github.com/ArceeDev/verifactu-mcp@${REF}" \
    "dataclean-mcp @ git+https://github.com/ArceeDev/dataclean-mcp@${REF}"
WORKDIR /srv
COPY app.py despacho.py ./
ENV WEB_INTEL_TRANSPORT=http NORMA43_TRANSPORT=http CONTABRIDGE_TRANSPORT=http VERIFACTU_TRANSPORT=http \
    DATACLEAN_TRANSPORT=http PYTHONUNBUFFERED=1
EXPOSE 8080
USER nobody
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--no-server-header"]
