from tqdm import tqdm
from pandas.core.frame import DataFrame
from ccus.MultiCore.utils import cpu_count
from concurrent.futures import ProcessPoolExecutor,as_completed

def run_multi_processes_dataframe_bool(task_func, data: DataFrame, max_workers=cpu_count, desc="🔥多进程处理中"):
    """
    1 data = dataFrame
    2 func 返回bool
    通用多进程执行器
    :param task_func: 需要执行的方法名
    :param data: DataFrame 数据
    :param max_workers: 最大进程数（默认 CPU 核心数）
    :param desc: 进度条描述
    :return: 满足条件的 index 列表
    """

    results = []
    total = len(data)

    # 转换为元组列表，因为进程间传递原生的 iterrows 迭代器可能会有序列化问题
    # 这样可以确保每个进程拿到的数据是干净的
    data_list = list(data.iterrows())

    with tqdm(total=total, desc=desc) as pbar:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            futures = {}
            for index, row_data in data_list:
                future = executor.submit(task_func, row_data)
                futures[future] = index

            for future in as_completed(futures):
                index = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(index)
                except Exception as e:
                    pbar.write(f"索引 {index} 进程执行失败: {e}")
                pbar.update(1)

    return sorted(results) # 多进程排序，意义不大