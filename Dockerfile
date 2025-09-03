FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN curl -fsSL https://raw.githubusercontent.com/wiserain/rclone/mod/install.sh | bash
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "bot.py"]
