async def token_stream(graph, messages, config):
    try:
        async for event in graph.astream_events(
                {"messages": messages},
                config=config,
                version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"[ERROR] {str(e)}"
