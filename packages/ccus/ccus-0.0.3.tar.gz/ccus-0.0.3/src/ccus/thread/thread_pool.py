import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

my_corks = min(32, 5 * os.cpu_count())

def run_multi_threads(task_func, iterable, max_workers=my_corks, desc="🚀处理中"):
    """
    通用多线程执行器[多线程，无序，需要后续额外排序]
    :param task_func: 需要执行的方法名 (例如 get_one_page)
        空参用法：run_multi_threads(lambda i:func(),range(10))
    :param iterable: 迭代对象 (例如 range, 列表, 对象列表)
    :param max_workers: 最大线程数
    :param desc: 进度条描述文字
    :return: 执行结果列表
    """
    results = []
    # 获取迭代对象的总长度用于进度条
    total = len(iterable) if hasattr(iterable, '__len__') else None

    with tqdm(total=total, desc=desc) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务，这里支持任何类型的迭代对象（pn 或 obj）
            futures = {executor.submit(task_func, item): item for item in iterable}

            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    # 使用 tqdm.write 避免破坏进度条
                    pbar.write(f"任务 {item} 执行失败: {e}")

                pbar.update(1)
    return results