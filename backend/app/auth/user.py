"""FastAPI dependency to extract user that has been authenticated by JWT middleware.

Usage:

    from app.auth import AuthorizedUser

    @router.get("/example-data")
    def get_example_data(user: AuthorizedUser):
        return example_read_data_for_user(userId=user.sub)
"""

from typing import Annotated
from fastapi import Depends
from .jwt_auth import get_authorized_user, User, get_admin_user

# Type alias for authorized user dependency
AuthorizedUser = Annotated[User, Depends(get_authorized_user)]

# Type alias for admin user dependency
AdminUser = Annotated[User, Depends(get_admin_user)]
