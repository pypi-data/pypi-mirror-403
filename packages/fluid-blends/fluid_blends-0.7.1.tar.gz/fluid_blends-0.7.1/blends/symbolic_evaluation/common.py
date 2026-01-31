import re

from blends.models import (
    Graph,
    NId,
)
from blends.query import (
    adj_ast,
    match_ast,
)
from blends.symbolic_evaluation.dispatcher import (
    generic,
)
from blends.symbolic_evaluation.models import (
    SymbolicEvalArgs,
)

# https://learn.microsoft.com/en-us/dotnet/api/system.web.httprequest
NET_SYSTEM_HTTP_METHODS = {
    "Cookies",
    "Form",
    "Headers",
    "Params",
    "Path",
    "PathInfo",
    "QueryString",
    "ReadLine",
    "GetString",
}
NET_CONNECTION_OBJECTS = {
    "TcpClient",
    "TcpListener",
    "SqlCommand",
    "WebClient",
}

JAVA_CONNECTION_METHODS = {
    "batchUpdate",
    "getBytes",
    "getHeader",
    "getHeaderNames",
    "getHeaders",
    "getName",
    "getParameter",
    "getTheParameter",
    "getParameterMap",
    "getParameterNames",
    "getParameterValues",
    "getQueryString",
    "getValue",
    "query",
    "queryForList",
    "queryForMap",
    "queryForObject",
    "queryForRowSet",
    "getInputStream",
    "getReader",
    "getCookies",
}

ANGULAR_USER_INPUTS = [
    r"\bthis\.route\.params\b",
    r"\bthis\.route\.queryParams\b",
    r"\bthis\.route\.fragment\b",
    r"\bthis\.http\.post",
    r"\bthis\.http\.put",
    r"\bthis\.http\.patch",
    r"\bdocument\.cookie\b",
    r"\blocalStorage\.getItem\(",
    r"\bsessionStorage\.getItem\(",
    r"\bwindow\.location\b",
    r"\bwindow\.name\b",
    r"\bwindow\.history\b",
    r"\bdocument\.URL\b",
    r"\bdocument\.location\b",
    r"\bdocument\.referrer\b",
]

JS_TS_HTTP_INPUTS = {
    r"\b(req|request)\.body\b",
    r"\b(req|request)\.params\b",
    r"\b(req|request)\.query\b",
    r"\b(req|request)\.originalUrl\b",
    r"\b(req|request)\.baseUrl\b",
    r"\b(req|request)\.path\b",
    r"\b(req|request)\.headers\b",
    r"\b(req|request)\.cookies\b",
    r"\b(req|request)\.file\b",
}

PYTHON_INPUTS = {
    "request.COOKIES.get",
    "request.GET",
    "request.GET.get",
    "request.POST.get",
    "request.args",
    "request.args.get",
    "request.data.get",
    "request.files",
    "request.files.get",
    "request.headers",
    "request.headers.get",
    "request.META.get",
    "request.form.get",
    "request.values.get",
    "request.json.get",
    "request.get_json",
    "request.args.to_dict",
    "request.get_data",
}

PHP_INPUTS = {"_GET", "_POST", "_REQUEST", "_FILES", "_COOKIE"}

PYTHON_REQUESTS_LIBRARIES = {
    "requests",
    "urllib",
    "urllib2",
    "urllib3",
    "httplib2",
    "httplib",
    "http",
    "treq",
    "aiohttp",
}
SCALA_INPUTS = {
    "request.uri.query.params.get",
    "request.uri",
    "request.headers.get",
    "request.cookies.get",
    "request.as[String]",
    "request.decode",
    "request.attributes.get",
    "request.getQueryString",
    "request.queryString",
    "request.body.asText",
    "request.body.asFormUrlEncoded",
    "request.body",
    "request.path",
}

SCALA_HTTP_LIBRARIES = {
    "org.http4s.client",
    "sttp.client3",
    "akka.http.scaladsl.Http",
    "play.api.libs.ws",
    "scalaj.http",
    "dispatch._",
    "feign",
}

RUBY_INPUTS = {
    "params",
    "request.query_parameters",
    "request.request_parameters",
    "cookies",
    "request.headers",
}

KOTLIN_INPUTS = {
    "call.parameters",
    "call.request.queryParameters",
    "call.request.headers",
    "call.request.cookies",
    "call.receiveText",
    "call.receiveParameters",
    "request.getParameter",
    "request.getHeader",
    "request.queryString",
    "request.cookies",
}

INSECURE_ALGOS = {
    "none",
    "blowfish",
    "bf",
    "des",
    "desede",
    "rc2",
    "rc4",
    "rsa",
    "3des",
}
INSECURE_MODES = {"cbc", "ecb", "ofb"}
INSECURE_HASHES = {"md2", "md4", "md5", "sha1", "sha-1"}

CREDENTIAL_SETTINGS = {
    "EMAIL_HOST_PASSWORD",
    "API_KEY",
    "SECRET_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_S3_SECRET_ACCESS_KEY",
    "SOCIAL_AUTH_GOOGLE_OAUTH_SECRET",
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET",
    "SOCIAL_AUTH_GOOGLE_PLUS_SECRET",
    "AUTH_LDAP_BIND_PASSWORD",
    "SECRET_KEY_FALLBACKS",
}

SWIFT_INPUTS = (
    "req.content",
    "req.query",
    "req.parameters",
    "req.body",
    "req.cookies",
    "req.headers",
    "req.method",
    "req.url",
)

SPRING_INPUTS = (
    "RequestParam",
    "RequestHeader",
    "CookieValue",
    "RequestBody",
    "PathVariable",
    "MatrixVariable",
    "ModelAttribute",
)


def concatenate_name(graph: Graph, n_id: NId, name: str | None = None) -> str:
    prev_str = ""
    if name:
        prev_str = name if name.startswith("::") else f".{name}"

    node_type = graph.nodes[n_id]["label_type"]
    if node_type == "MethodInvocation":
        expr = graph.nodes[n_id]["expression"]
        if graph.nodes[n_id].get("object_id") and (next_node := match_ast(graph, n_id)["__0__"]):
            expr = concatenate_name(graph, next_node, expr)
    elif node_type == "SymbolLookup":
        expr = graph.nodes[n_id]["symbol"]
    else:
        expr = ""
    return str(expr + prev_str)


def check_swift_inputs(graph: Graph, n_id: NId) -> bool:
    node_id = n_id
    if graph.nodes[node_id]["label_type"] == "If" and (
        block_id := graph.nodes[node_id]["condition_id"]
    ):
        node_id = block_id
    if graph.nodes[node_id]["label_type"] == "TryStatement" and (
        block_id := graph.nodes[node_id]["block_id"]
    ):
        node_id = block_id
    return bool(
        (
            graph.nodes[node_id]["label_type"] == "MethodInvocation"
            or graph.nodes[node_id]["label_type"] == "MemberAccess"
        )
        and (expr := graph.nodes[node_id].get("expression"))
        and expr.startswith(SWIFT_INPUTS)
    )


def owasp_user_connection(args: SymbolicEvalArgs) -> bool:
    ma_attr = args.graph.nodes[args.n_id]
    return bool(
        ma_attr["expression"] in JAVA_CONNECTION_METHODS
        and (obj_id := ma_attr.get("object_id"))
        and generic(args.fork(n_id=obj_id, evaluation={}, triggers=set())).triggers
        == {"userconnection"},
    )


def check_js_ts_http_inputs(args: SymbolicEvalArgs) -> bool:
    n_attrs = args.graph.nodes[args.n_id]
    member_access = f"{n_attrs['expression']}.{n_attrs['member']}"
    return next(
        (True for expr in JS_TS_HTTP_INPUTS if re.match(expr, member_access) is not None),
        False,
    )


def check_python_inputs(args: SymbolicEvalArgs) -> bool:
    n_attrs = args.graph.nodes[args.n_id]
    if n_attrs["label_type"] != "MemberAccess":
        return False
    member_access = f"{n_attrs['expression']}.{n_attrs['member']}"
    return member_access in PYTHON_INPUTS


def check_php_inputs(graph: Graph, n_id: NId) -> bool:
    node = graph.nodes[n_id]
    if node["label_type"] != "ElementAccess":
        return False
    return graph.nodes[node["expression_id"]].get("symbol", "") in PHP_INPUTS


def check_kotlin_inputs(graph: Graph, n_id: NId) -> bool:
    node = graph.nodes[n_id]
    if not (expr_id := node.get("expression_id")):
        return False
    expr_node = graph.nodes[expr_id]
    if expr_node.get("label_type") != "MemberAccess":
        return False
    member_access = f"{expr_node.get('expression')}.{expr_node.get('member')}"
    return member_access in KOTLIN_INPUTS


def check_ruby_inputs(graph: Graph, n_id: NId) -> bool:
    node = graph.nodes[n_id]
    return bool(
        (node["label_type"] == "ElementAccess")
        and (expr_id := node.get("expression_id"))
        and (expr_node := graph.nodes[expr_id])
        and (
            (
                (expr_node["label_type"] != "MethodInvocation")
                and (expr_node["symbol"] in RUBY_INPUTS)
            )
            or (
                (expr_node["label_type"] == "MethodInvocation")
                and (obj_id := expr_node.get("object_id"))
                and (obj_node := graph.nodes[obj_id])
                and (expr_id := expr_node.get("expression_id"))
                and (expr_node := graph.nodes[expr_id])
                and (member_access := f"{obj_node['symbol']}.{expr_node.get('symbol')}")
                and (member_access in RUBY_INPUTS)
            )
        )
    )


def check_scala_inputs(graph: Graph, n_id: NId) -> bool:
    return bool(
        (method_name := concatenate_name(graph, n_id))
        and any(
            method_name.startswith(input_pattern) or method_name in input_pattern
            for input_pattern in SCALA_INPUTS
            if input_pattern
        )
    )


def check_spring_scala_inputs(graph: Graph, n_id: NId) -> bool:
    if graph.nodes[n_id]["label_type"] == "Parameter" and (param_data := adj_ast(graph, n_id)):
        for param_id in param_data:
            if (
                graph.nodes[param_id]["label_type"] == "Annotation"
                and (name := graph.nodes[param_id].get("name"))
                and (name in SPRING_INPUTS)
            ):
                return True
    return False
