import requests
import aiohttp
import asyncio
import concurrent.futures
from threading import Thread
import time


class Loader:
    def __init__(self):
        self.url = 'https://www.google.com/'

    def _build_url(self, skip, category):
        return self.url + f'?skip={skip}&price_min=0&price_max=1060225&up_vy_min=0&up_vy_max=108682515&up_vy_pr_min=0&up_vy_pr_max=2900&sum_min=1000&sum_max=82432725&feedbacks_min=0&feedbacks_max=32767&trend=false&sort=sum_sale&sort_dir=-1&id_cat={category}'

    def get_data(self, skip=0, category=1000):
        try:
            url = self._build_url(skip, category)
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to get data for category {category}: {str(e)}"}

    
    def get_data_multithreaded(self, categories, skip=0, max_workers=5):
        results = {}
        
        def fetch_category(category):
            return category, self.get_data(skip, category)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_category = {
                executor.submit(fetch_category, category): category 
                for category in categories
            }
            
            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    category_id, data = future.result()
                    results[category_id] = data
                except Exception as e:
                    results[category] = {"error": str(e)}
        
        return results

    
    async def get_data_async_batch(self, categories, skip=0):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for category in categories:
                url = self._build_url(skip, category)
                task = self._fetch_single(session, url, category)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {cat: result for cat, result in zip(categories, results)}
    
    async def _fetch_single(self, session, url, category):
        try:
            async with session.get(url) as response:
                data = await response.json()
                return data
        except Exception as e:
            return {"error": f"Failed to get data for category {category}: {str(e)}"}


def main():
    loader = Loader()
    categories = [1000, 1001, 1002, 1003, 1004, 1005]
    
    print("=== МНОГОПОТОЧНАЯ ЗАГРУЗКА ===")
    start_time = time.time()
    
    # Многопоточная загрузка
    results = loader.get_data_multithreaded(categories, skip=0, max_workers=3)
    
    end_time = time.time()
    print(f"Время выполнения многопоточной загрузки: {end_time - start_time:.2f} секунд")
    
    # Вывод результатов
    for category, data in results.items():
        if "error" in data:
            print(f"Категория {category}: ОШИБКА - {data['error']}")
        else:
            records_count = len(data.get('data', []))
            print(f"Категория {category}: {records_count} записей")
    
    print("\n" + "="*50 + "\n")
    
    # Асинхронная загрузка для сравнения
    async def async_demo():
        print("=== АСИНХРОННАЯ ЗАГРУЗКА ===")
        start_time = time.time()
        
        results_async = await loader.get_data_async_batch(categories)
        
        end_time = time.time()
        print(f"Время выполнения асинхронной загрузки: {end_time - start_time:.2f} секунд")
        
        for category, data in results_async.items():
            if isinstance(data, Exception) or "error" in data:
                error_msg = data if isinstance(data, Exception) else data['error']
                print(f"Категория {category}: ОШИБКА - {error_msg}")
            else:
                records_count = len(data.get('data', []))
                print(f"Категория {category}: {records_count} записей")
    
    # Запуск асинхронной демонстрации
    asyncio.run(async_demo())


if __name__ == "__main__":
    main()