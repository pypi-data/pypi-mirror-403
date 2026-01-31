import os
cpu_count = os.cpu_count()
threading_count = min(32, 5 * cpu_count)