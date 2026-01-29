from adtools.ad_agent.protocol import AlgoProto


class AgentBase:
    pass


def timer(algo: AlgoProto, name:str):
    pass


def sample_algorithm(
    prompt, evaluate_method, *method_args, **method_kwargs
) -> AlgoProto:
    pass


def sample_init_algorithm(prompt, evaluator) -> AlgoProto:
    pass


def save_to_logger(logger, algo_proto):
    pass
