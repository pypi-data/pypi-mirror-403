import requests, time

with open('domains.txt') as file:
    domains = file.read().splitlines()


def check_site_requests(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()

        if response.status_code == 200:
            print(f"✅ {url} доступен")
            print(f"   Время ответа: {(end_time - start_time):.2f} сек")
            print(f"   Размер ответа: {len(response.content)} байт")
            return True
        else:
            print(f"⚠️ {url} вернул код {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к {url}: {type(e).__name__}")
        return False


for domain in domains:
    check_site_requests(f'https://{domain}/')
    print("-" * 40)
