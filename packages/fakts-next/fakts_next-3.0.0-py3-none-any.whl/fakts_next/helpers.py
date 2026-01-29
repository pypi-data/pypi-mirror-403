from fakts_next.fakts import get_current_fakts_next
from fakts_next.models import Alias
from koil.helpers import unkoil


async def afakt(key: str, omit_challenge: bool | None = None) -> Alias:
    value = await get_current_fakts_next().aget_alias(
        key, omit_challenge=omit_challenge
    )
    return value


def fakt(key: str, omit_challenge: bool | None = None) -> Alias:
    return unkoil(afakt, key, omit_challenge=omit_challenge)
