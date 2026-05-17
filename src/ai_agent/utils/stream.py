async def token_stream(graph, messages, config):
    try:
        # messages 为 None 时表示从 checkpoint 恢复（resume 场景）
        input_data = {"messages": messages} if messages is not None else None
        async for event in graph.astream_events(
                input_data,
                config=config,
                version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"[ERROR] {str(e)}"
