import os
import asyncio
from eos import AsyncEOS

client = AsyncEOS(
    api_key=os.environ.get(
        "EVERMEMOS_API_KEY",
    ),
)


async def main() -> None:
    # 搜索记忆
    search_result = await client.v1.memories.search(
        extra_query={
            # "query": "时间字符串",
            # "user_id": "user_001",
            # "group_id": "group_0123",
            "group_id": "0122_series_1",
            "memory_types": ["episodic_memory"],
            "retrieve_method": "keyword",
            "top_k": 10,
        }
    )
    print("搜索记忆结果:")
    print(f"  message: {search_result.message}")
    print(f"  status: {search_result.status}")
    if search_result.result:
        print(f"  total_count: {search_result.result.total_count}")
        print(f"  has_more: {search_result.result.has_more}")
        if search_result.result.memories:
            print(f"  找到 {len(search_result.result.memories)} 组记忆")
            # 打印前几个记忆的详细信息
            for idx, memory_group in enumerate(search_result.result.memories[:3], 1):
                print(f"\n  记忆组 {idx}:")
                for memory_type, memories in memory_group.items():
                    print(f"    类型: {memory_type}")
                    for mem in memories[:2]:  # 每组只显示前2个
                        print(f"      - user_id: {mem.user_id}, timestamp: {mem.timestamp}")
        
        # 打印待处理消息
        if hasattr(search_result.result, 'pending_messages') and search_result.result.pending_messages:
            print(f"\n  待处理消息 ({len(search_result.result.pending_messages)} 条):")
            for idx, msg in enumerate(search_result.result.pending_messages[:5], 1):  # 最多显示5条
                print(f"\n  消息 {idx}:")
                print(f"    id: {msg.id}")
                print(f"    message_id: {msg.message_id}")
                print(f"    group_id: {msg.group_id}")
                print(f"    user_id: {msg.user_id}")
                print(f"    sender: {msg.sender}")
                if hasattr(msg, 'sender_name') and msg.sender_name:
                    print(f"    sender_name: {msg.sender_name}")
                if hasattr(msg, 'group_name') and msg.group_name:
                    print(f"    group_name: {msg.group_name}")
                print(f"    content: {msg.content}")
                if hasattr(msg, 'refer_list') and msg.refer_list:
                    print(f"    refer_list: {msg.refer_list}")
                if hasattr(msg, 'message_create_time') and msg.message_create_time:
                    print(f"    message_create_time: {msg.message_create_time}")
                if hasattr(msg, 'created_at') and msg.created_at:
                    print(f"    created_at: {msg.created_at}")


if __name__ == "__main__":
    asyncio.run(main())
