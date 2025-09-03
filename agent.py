import requests
import time
import os
import subprocess

# URL твоего backend-сайта
BACKEND_URL = "http://127.0.0.1:8000/api/commands"
HEARTBEAT_URL = "http://127.0.0.1:8000/api/heartbeat"
SERVER_ID = "server1"  # уникальный ID сервера
AUTH_TOKEN = "secret_token_123"  # защита от левых запросов

def shutdown():
    os.system("shutdown /s /t 5")  # выключение Windows через 5 секунд

def restart():
    os.system("shutdown /r /t 5")  # перезапуск Windows

def run_game_server():
    # Пример: запуск Minecraft сервера
    subprocess.Popen(["java", "-Xmx1024M", "-Xms1024M", "-jar", "server.jar", "nogui"])

def check_commands():
    try:
        response = requests.get(
            f"{BACKEND_URL}?server_id={SERVER_ID}&token={AUTH_TOKEN}", timeout=5
        )
        if response.status_code == 200:
            command = response.json().get("command")
            if command == "shutdown":
                shutdown()
            elif command == "restart":
                restart()
            elif command == "start_game":
                run_game_server()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    print("Агент запущен...")
    while True:
        check_commands()
        print('Попытка постучать на сервер')
        # Отправка статуса сервера
        try:
            requests.post(f"{HEARTBEAT_URL}?token={AUTH_TOKEN}", json={"server_id": SERVER_ID})
            print('Постучал на сервер')
        except:
            print('Не удалось постучать на сервер')

        time.sleep(5)  # проверяем каждые 5 секунд

