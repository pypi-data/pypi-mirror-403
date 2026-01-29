FROM python:3.11-alpine

WORKDIR /app

COPY pyproject.toml README.md ./
COPY endfield_daily/ endfield_daily/

RUN pip install --no-cache-dir .

# Run the tool
CMD ["endfield-daily"]
