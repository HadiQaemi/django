from rolepermissions.roles import AbstractUserRole


class Admin(AbstractUserRole):
    available_permissions = {
        "view_users": True,
        "edit_users": True,
        "delete_users": True,
        "create_users": True,
        "view_papers": True,
        "edit_papers": True,
        "delete_papers": True,
        "create_papers": True,
        "view_statements": True,
        "edit_statements": True,
        "delete_statements": True,
        "create_statements": True,
    }


class Editor(AbstractUserRole):
    available_permissions = {
        "view_papers": True,
        "edit_papers": True,
        "delete_papers": True,
        "create_papers": True,
        "view_statements": True,
        "edit_statements": True,
        "delete_statements": True,
        "create_statements": True,
    }


class Viewer(AbstractUserRole):
    available_permissions = {
        "view_papers": True,
        "view_statements": True,
    }
