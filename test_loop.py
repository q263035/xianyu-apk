"""
测试循环功能逻辑
"""

import json
import os

DATA_FILE = 'item_ids.json'

def load_item_ids():
    """从文件加载商品 ID 列表"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return (
                    data.get('item_ids', []),
                    data.get('interval', 60),
                    data.get('account_type', 'personal'),
                    data.get('auto_buy', False),
                    data.get('retry_delay', 600),
                    data.get('max_retries', 3),
                    data.get('loop_count', 1),
                    data.get('loop_interval', 60)
                )
        except:
            pass
    return [], 60, 'personal', False, 600, 3, 1, 60


# 测试加载
item_ids, interval, account_type, auto_buy, retry_delay, max_retries, loop_count, loop_interval = load_item_ids()

print("=" * 50)
print("循环功能测试")
print("=" * 50)
print(f"商品 ID 列表：{item_ids}")
print(f"轮询间隔：{interval}秒")
print(f"循环次数：{loop_count}")
print(f"循环间隔：{loop_interval}秒")
print("=" * 50)

# 模拟循环逻辑
if not item_ids:
    item_ids = ['111', '222', '333']  # 测试数据

print(f"\n开始模拟轮询（{len(item_ids)}个商品，{loop_count}轮）...\n")

for loop_num in range(loop_count):
    print(f"【第 {loop_num + 1}/{loop_count} 轮】")
    for idx, item_id in enumerate(item_ids):
        print(f"  → 访问商品 {item_id} ({idx + 1}/{len(item_ids)})")
    
    if loop_num < loop_count - 1:
        print(f"  ⏱️ 等待 {loop_interval} 秒后开始下一轮...\n")
    else:
        print(f"\n✅ 完成 {loop_count} 轮轮询")

print("=" * 50)
