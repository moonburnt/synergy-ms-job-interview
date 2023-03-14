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


def _get_flat_user_data_from_json(d: dict, invited_by: Optional[ReferalUserModel] = None, ref_list:Optional[list] = None) -> list:
    if not ref_list:
        ref_list = []

    # No safety checks for format validness, for now
    ref_id = d["id"]
    ref_list.append(
        (ref_id, invited_by)
    )

    if isinstance(d["refs"], list) and len(d["refs"]) > 0:
        for i in d["refs"]:
            _get_flat_user_data_from_json(
                d = i,
                invited_by = ref_id,
                ref_list = ref_list,
            )

    return ref_list

def _batch_update_inviteers(user_data: List[Tuple[int, int]]):
    for i in user_data:
        instance = ReferalUserModel.objects.get(referal_id=i[0])
        referal_id = referal_id=i[1]
        if referal_id is None:
            continue
        else:
            instance.invited_by = ReferalUserModel.objects.get(referal_id=referal_id)
            yield instance

def _batch_update_user_lvls():
    for user in ReferalUserModel.objects.all():
        user.update_lvl(save = False)
        yield user


def add_users_from_json(path_to_json: Union[str, Path]):
    with open(path_to_json, "r") as fp:
        data = load(fp)

    print("Fetching users")
    user_data = _get_flat_user_data_from_json(
        d = data,
    )

    print("Creating users")
    create_user_data = (ReferalUserModel(referal_id = i[0]) for i in user_data)
    ReferalUserModel.objects.bulk_create(create_user_data)

    print("Updating users' inviteers")
    ReferalUserModel.objects.bulk_update(_batch_update_inviteers(user_data), fields=("invited_by",))

    print("Updating users' levels")
    ReferalUserModel.objects.bulk_update(_batch_update_user_lvls(), fields=("referal_lvl",))

    print("Done")
