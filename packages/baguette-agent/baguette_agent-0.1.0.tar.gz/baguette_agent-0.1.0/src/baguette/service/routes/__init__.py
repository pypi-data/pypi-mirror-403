from . import journal, memory, skills, traces, transactions


def register_routes(app, storage, _raise_http, Body, Query) -> None:
    skills.register(app, storage, _raise_http, Body, Query)
    transactions.register(app, storage, _raise_http, Body, Query)
    traces.register(app, storage, _raise_http, Body, Query)
    journal.register(app, storage, _raise_http, Body, Query)
    memory.register(app, storage, _raise_http, Body, Query)


__all__ = ["register_routes"]
