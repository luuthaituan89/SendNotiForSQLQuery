```markdown
# MySQL SSH Tunnel Notifier

## Create .env file with this information:
Create a `.env` file in the root directory and add the following information:

```
SSH_HOST=
SSH_PORT=
SSH_USERNAME=
SSH_PASSWORD=

DB_HOST=
DB_PORT=
DB_USERNAME=
DB_PASSWORD=
DB_NAME=

WEBHOOK_URL=

QUERY=""
```

## Install package:
Run the following command to install the required packages:

```bash
pip install pymysql bottle sshtunnel prettytable requests python-dotenv pandas
```

## Run:
To run the program, use the following command:

```bash
python3 noti.py
```
```

Bạn chỉ cần sao chép nội dung này và lưu vào file `README.md` trong dự án của mình.