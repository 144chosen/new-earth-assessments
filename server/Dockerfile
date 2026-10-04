FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY server /app/server
RUN python -c "import urllib.request,pathlib,hashlib; p=pathlib.Path('/app/server/data/de440s.bsp'); p.parent.mkdir(parents=True,exist_ok=True); urllib.request.urlretrieve('https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp',p); assert hashlib.sha256(p.read_bytes()).hexdigest()=='c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2', 'Planetary data verification failed'"
COPY public /app/public
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser
WORKDIR /app/server
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "--timeout", "90", "app:create_app()"]
