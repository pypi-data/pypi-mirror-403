from caerp.utils.strings import month_name


def get_node_url(
    request,
    node=None,
    _query={},
    suffix="",
    api=False,
    _anchor=None,
    absolute=False,
):
    if node is None:
        node = request.context

    url_node_type = node.type_.replace("internal", "").replace("sheet", "")
    if url_node_type[-1:] == "s":
        url_node_type += "es"
    elif url_node_type[-1:] == "y":
        url_node_type = url_node_type[-1:] + "ies"
    else:
        url_node_type += "s"
    route = "/%s/{id}" % url_node_type

    if suffix:
        route += suffix

    if api:
        route = "/api/v1%s" % route

    params = dict(id=node.id, _query=_query)
    if _anchor is not None:
        params["_anchor"] = _anchor

    if absolute:
        method = request.route_url
    else:
        method = request.route_path
    return method(route, **params)


def get_node_label(request, node=None, with_details=False) -> str:
    if node is None:
        node = request.context

    label = ""
    details = None

    if "estimation" in node.type_:
        label = node.internal_number
        details = node.name
    elif "invoice" in node.type_:
        if node.official_number:
            label = node.official_number
            details = node.name
        else:
            label = node.name
            details = ""
    elif node.type_ == "expensesheet":
        label = f"{month_name(node.month).capitalize()} {node.year}"
        details = node.title or ""
    elif node.type_ in ["customer", "supplier"]:
        label = node.label
    else:
        label = node.name

    if label is None:
        # Ref #4844 : mako attend forcément une string
        label = "-"

    if with_details and details and details != "":
        return f"{label}<br/><small>{details}</small>"
    else:
        return label
