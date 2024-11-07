import pymysql
from Scripts.bottle import response
from sshtunnel import SSHTunnelForwarder
from prettytable import PrettyTable
import requests
from dotenv import load_dotenv
import os
import pandas as pd

# Tải các biến môi trường từ file .env
load_dotenv()

# Lấy các giá trị từ môi trường
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = int(os.getenv('SSH_PORT'))
SSH_USERNAME = os.getenv('SSH_USERNAME')
SSH_PASSWORD = os.getenv('SSH_PASSWORD')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
QUERY = os.getenv('QUERY')


def create_ssh_tunnel():
    """Tạo kết nối SSH Tunnel."""
    try:
        tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USERNAME,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST, DB_PORT)
        )
        tunnel.start()
        print("SSH Tunnel Established.")
        return tunnel
    except Exception as e:
        print(f"Failed to establish SSH tunnel: {e}")
        raise


def connect_to_mysql(tunnel):
    """Kết nối đến MySQL qua SSH Tunnel."""
    try:
        connection = pymysql.connect(
            host='127.0.0.1',  # Kết nối tới localhost (SSH tunnel sẽ forward cổng này)
            port=tunnel.local_bind_port,  # Cổng local từ tunnel
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("MySQL connection established successfully.")
        return connection
    except pymysql.MySQLError as err:
        print(f"Failed to connect to MySQL: {err}")
        raise


def execute_query(connection):
    """Thực thi câu truy vấn SQL."""
    try:
        cursor = connection.cursor()
        cursor.execute(QUERY)
        results = cursor.fetchall()
        return results, cursor
    except pymysql.MySQLError as err:
        print(f"Failed to execute query: {err}")
        raise


def send_table_to_google_chat(result = None, headers= None):
    """Gửi bảng dữ liệu vào Google Chat."""

    if result is None or result.empty:
        message = {"text": "No data in the table."}
        response = requests.post(WEBHOOK_URL, json=message)
    else:
        headers_list = list(headers)
        table = PrettyTable(headers_list)
        table.align = "l"  # Căn trái cho tất cả các cột

        for column in headers_list:
            table.max_width[column] = 20  # Thiết lập độ rộng tối đa cho cột

        for _, row in result.iterrows():
            table.add_row(row.tolist())

        message = {"text": f"Data in the table:\n```\n{table.get_string()}\n```"}
        response = requests.post(WEBHOOK_URL, json=message)
        if response.status_code == 200:
            print("Data sent to Google Chat successfully.")
        else:
            print(f"Failed to send data to Google Chat. Status code: {response.status_code}")


def close_connection(connection):
    """Đảm bảo đóng kết nối MySQL khi xong."""
    if 'connection' in locals() and connection.open:
        connection.close()
        print("MySQL connection closed.")


def main():
    """Hàm chính để chạy toàn bộ quy trình."""
    try:
        # Mở SSH tunnel
        tunnel = create_ssh_tunnel()

        # Kết nối đến MySQL
        connection = connect_to_mysql(tunnel)

        # Thực thi câu truy vấn và lấy kết quả
        results, cursor = execute_query(connection)

        if results:
            # Chuyển kết quả thành DataFrame để dễ xử lý
            df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])

            # Gửi dữ liệu lên Google Chat
            send_table_to_google_chat(df, df.columns)
        else:
            send_table_to_google_chat()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Đảm bảo đóng kết nối khi kết thúc
        close_connection(connection)


if __name__ == "__main__":
    main()
