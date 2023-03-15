import logging
from pathlib import Path
from typing import Union, Optional, List, Tuple, Generator
from users.models import ReferalUserModel
from json import load

log = logging.getLogger(__name__)


import logging
from pathlib import Path
from typing import Union, Optional
from users.models import ReferalUserModel
from json import load

log = logging.getLogger(__name__)


def _get_descendants_from_list(storage: list, lvl: int) -> int:
    return len([i for i in storage if i == lvl])


def _get_flat_user_data_from_json(
    d: dict, ref_list: list, invited_by: Optional[ReferalUserModel] = None
) -> Tuple[int, int]:
    # No safety checks for format validness, for now
    ref_id = d["id"]
    user_info = [ref_id, invited_by]
    ref_list.append(user_info)

    direct_desc = len(d["refs"])
    total_desc = direct_desc
    direct_desc_levels = []

    desc_data = []

    if isinstance(d["refs"], list) and direct_desc > 0:
        for i in d["refs"]:
            desc_count, desc_lvl = _get_flat_user_data_from_json(
                d=i,
                invited_by=ref_id,
                ref_list=ref_list,
            )
            direct_desc_levels.append(desc_lvl)
            total_desc += desc_count

    lvl = ReferalUserModel.calculate_user_lvl(
        total_desc=total_desc,
        direct_desc=direct_desc,
        desc_storage=direct_desc_levels,
        get_descendants=_get_descendants_from_list,
    )

    user_info.append(total_desc)
    user_info.append(lvl)

    return total_desc, lvl


def _batch_update_users(user_data):
    for i in user_data:
        instance = ReferalUserModel.objects.get(referal_id=i[0])
        referal_id = i[1]
        if referal_id is not None:
            instance.invited_by = ReferalUserModel.objects.get(referal_id=referal_id)
        instance.referal_lvl = i[3]
        yield instance


def add_users_from_json(path_to_json: Union[str, Path]):
    with open(path_to_json, "r") as fp:
        data = load(fp)

    print("Fetching users")
    user_data = []
    _get_flat_user_data_from_json(
        d=data,
        ref_list=user_data,
    )

    print("Creating users")
    create_user_data = (ReferalUserModel(referal_id=i[0]) for i in user_data)
    ReferalUserModel.objects.bulk_create(create_user_data)

    print("Updating users")
    ReferalUserModel.objects.bulk_update(
        _batch_update_users(user_data),
        fields=(
            "invited_by",
            "referal_lvl",
        ),
    )

    print("Done")
