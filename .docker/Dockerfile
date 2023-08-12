# build
FROM python:3.11.4-slim-buster as builder
RUN apt update -y
RUN apt install -y gcc
COPY requirements.txt .
RUN python3.11 -m pip install --user -U --no-cache-dir pip
RUN python3.11 -m pip install --user -U --no-cache-dir wheel
RUN python3.11 -m pip install --user -U --no-cache-dir Cython
RUN python3.11 -m pip install --user -U --no-cache-dir -r requirements.txt
RUN rm -rf ~/.aws

# production
FROM python:3.11.4-slim-buster
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1