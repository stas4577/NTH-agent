import requests
import time
import os
import subprocess
import psutil
import platform
import socket
import uuid
import os



# URL твоего backend-сайта
BASE_URL = "http://192.168.0.27:8000"
REGISTER_URL = f"{BASE_URL}/api/register_server"
CHECK_APPROVAL_URL = f"{BASE_URL}/api/check_approval"
COMMANDS_URL = f"{BASE_URL}/api/commands"
HEARTBEAT_URL = f"{BASE_URL}/api/heartbeat"


file_path = "agent_id.txt"
if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        SERVER_ID = file.read().strip()
else:
    SERVER_ID = str(uuid.uuid4())
    with open(file_path, 'w') as file:
        file.write(SERVER_ID)
    


AUTH_TOKEN = "secret_token_123"  # защита от левых запросов

# ==========================
# 🧩 Вспомогательные функции
# ==========================

def shutdown():
    os.system("shutdown /s /t 5")

def restart():
    os.system("shutdown /r /t 5")

def run_game_server():
    subprocess.Popen(["java", "-Xmx1024M", "-Xms1024M", "-jar", "server.jar", "nogui"])

def get_system_stats():
    """Собирает статистику по CPU, RAM, Memory и аптайму."""
    cpu_load = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    uptime = time.time() - psutil.boot_time()
    disk_usage = psutil.disk_usage('/')
    return {
        "cpu": cpu_load,
        "ram_used": round(memory.used / (1024 ** 3), 2),
        "ram_total": round(memory.total / (1024 ** 3), 2),
        "uptime": round(uptime / 3600, 1),
        "disk_used": round(disk_usage.used / (1024 ** 3), 2),
        "disk_total": round(disk_usage.total / (1024 ** 3), 2),
        "disk_percent": disk_usage.percent
    }

def check_commands():
    try:
        response = requests.get(f"{COMMANDS_URL}?server_id={SERVER_ID}&token={AUTH_TOKEN}", timeout=5)
        if response.status_code == 200:
            command = response.json().get("command")
            if command == "shutdown":
                shutdown()
            elif command == "restart":
                restart()
            elif command == "start_game":
                run_game_server()
    except Exception as e:
        print(f"Ошибка при получении команды: {e}")

# ==========================
# 🧠 Регистрация агента
# ==========================

def register_server():
    """Отправляет запрос на регистрацию нового агента"""
    payload = {
        "server_id": SERVER_ID,
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "agent_version": "1.0.0",
    }

    try:
        response = requests.post(f"{REGISTER_URL}?token={AUTH_TOKEN}", json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("Ответ сервера:", data.get("message", data))
            return data
        else:
            print("Ошибка регистрации:", response.text)
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
    return None


def wait_for_approval():
    """Проверяет, одобрен ли сервер админом"""
    print("⏳ Ожидание одобрения администратора...")
    while True:
        try:
            r = requests.get(f"{CHECK_APPROVAL_URL}/{SERVER_ID}?token={AUTH_TOKEN}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "approved":
                    print("✅ Сервер одобрен! Начинаю работу.")
                    break
                elif data.get("status") == "rejected":
                    print("❌ Сервер отклонён администратором.")
                    exit(0)
            else:
                print("Ошибка проверки статуса:", r.text)
        except Exception as e:
            print("Ошибка проверки одобрения:", e)
        time.sleep(10)

# ==========================
# 🚀 Основной цикл
# ==========================

if __name__ == "__main__":
    print("Агент запущен...")
    print(f"server-id = {SERVER_ID}")

    reg = register_server()
    if not reg:
        print("Не удалось зарегистрироваться. Завершение.")
        exit(1)

    wait_for_approval()

    while True:
        check_commands()
        try:
            stats = get_system_stats()
            payload = {"server_id": SERVER_ID, "stats": stats}
            response = requests.post(f"{HEARTBEAT_URL}?token={AUTH_TOKEN}", json=payload, timeout=5)
            if response.status_code != 200:
                print("Ошибка отправки heartbeat:", response.text)
        except Exception as e:
            print("Ошибка при отправке heartbeat:", e)

        time.sleep(5)
