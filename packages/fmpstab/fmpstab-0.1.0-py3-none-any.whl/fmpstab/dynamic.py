from typing import Callable, Any

def create_endpoint_method(ep: str) -> Callable:
    """
    Returns an endpoint method bound to a specific API endpoint.
    Renames parameters (e.g. 'start_date' to 'from') before calling the client.
    """
    def method(self, *args, **kwargs):
        if 'start_date' in kwargs:
            kwargs['from'] = kwargs.pop('start_date')
        elif 'from_' in kwargs:
            kwargs['from'] = kwargs.pop('from_')
        if 'end_date' in kwargs:
            kwargs['to'] = kwargs.pop('end_date')
        elif 'to_' in kwargs:
            kwargs['to'] = kwargs.pop('to_')
        return self.call(ep, **kwargs)
    return method

def attach_dynamic_functions(client: Any) -> None:
    """
    Attaches dynamic endpoint methods to the client.
    """
    for ep in client.endpoints.keys():
        func_name = ep.replace("-", "_")
        setattr(client.__class__, func_name, create_endpoint_method(ep))
