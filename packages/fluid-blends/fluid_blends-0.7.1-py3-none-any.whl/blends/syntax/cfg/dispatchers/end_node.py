from blends.models import (
    NId,
)
from blends.syntax.models import (
    SyntaxCfgArgs,
)


def build(args: SyntaxCfgArgs) -> NId:
    return args.n_id
