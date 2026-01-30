from langchain_core.runnables import RunnableConfig

from nancal_langchain_base.log.node_log import Logger


def init_run_config(graph, ctx):
    tracer = Logger(graph, ctx)
    tracer.on_chain_start = tracer.on_chain_start_graph
    tracer.on_chain_end = tracer.on_chain_end_graph
    config = RunnableConfig(
        callbacks=[tracer],
    )
    return config


def init_agent_config(graph, ctx):
    config = RunnableConfig(
        callbacks=[]
    )
    return config

