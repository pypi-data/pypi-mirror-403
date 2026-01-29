"""a class based approach to handling role hierarchy"""

__all__ = ["extract_role_hierarchy", "get_roles_w_hierarchy", "calc_role"]

from ..classes.DomoInstanceConfig.role import DomoRole, DomoRoles


def extract_role_hierarchy(
    role: DomoRole, hierarchy_delimiter
) -> DomoRole:  # augments the domo role with a hierarchy INT attribute
    description_arr = role.description.split(hierarchy_delimiter)

    if len(description_arr) != 1:
        hierarchy = int(description_arr[1])

    elif role.is_system_role:
        hierarchy = (5 - role.id) * 2 + 1

    else:
        hierarchy = 0

    role.hierarchy = hierarchy

    return role


async def get_roles_w_hierarchy(
    auth,
    hierarchy_delimiter=" - h",  # post fix to delimit hierarchy number.  assumes scale of 1:10, system accounts will be included.
    debug_api: bool = False,
):
    """gets instance roles and adds an attribute hierarchy"""

    domo_config = DomoRoles(auth=auth)
    domo_roles = await domo_config.get(debug_api=debug_api)
    return [
        extract_role_hierarchy(role=role, hierarchy_delimiter=hierarchy_delimiter)
        for role in domo_roles
    ]


async def calc_role(
    current_role_id,
    new_role_name,
    auth,
    hierarchy_delimiter=" - h",
    is_alter_system_roles: bool = False,  # by default calc role will not apply to system roles and will always update to a system role
):
    """compares current role to new role hierarchy and returns the higher one.  will not adjust system roles"""

    instance_roles = await get_roles_w_hierarchy(
        auth=auth, hierarchy_delimiter=hierarchy_delimiter
    )

    current_role = next(role for role in instance_roles if role.id == current_role_id)

    if current_role.is_system_role and not is_alter_system_roles:
        print(f"{current_role.name} is a system role -- no changes")
        return current_role

    expected_role = next(
        (role for role in instance_roles if role.name == new_role_name), None
    )

    if not expected_role:
        raise Exception(f"{new_role_name} not found in {auth.domo_instance}")

    if current_role.hierarchy >= expected_role.hierarchy:
        return current_role

    return expected_role
