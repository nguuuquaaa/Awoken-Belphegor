# build
FROM python:3.12.3-slim-bookworm as builder
RUN apt update -y
RUN apt install -y gcc
COPY requirements.txt .
RUN python -m pip install --user -U --no-cache-dir pip
RUN python -m pip install --user -U --no-cache-dir wheel Cython
RUN python -m pip install --user -U --no-cache-dir -r requirements.txt
RUN rm -rf ~/.aws

# production
FROM python:3.12.3-slim-bookworm
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1