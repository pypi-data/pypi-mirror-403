"""SCIM User Management Example

Demonstrates SCIM user operations including:
- Listing all SCIM users
- Getting user by ID or username
- Creating new users
- Updating user attributes
- Deactivating/activating users
- Deleting users

Usage:
    python -m examples.scim.scim_users
"""
from pywats import pyWATS, ScimUser, ScimUserName, ScimUserEmail


def main():
    # Initialize API client
    api = pyWATS(
        base_url="https://your-wats-server.com",
        token="your-api-token"
    )
    
    # ====================
    # List all SCIM users
    # ====================
    print("=== Listing SCIM Users ===")
    response = api.scim.get_users()
    print(f"Total users: {response.total_results}")
    
    for user in response.resources or []:
        status = "✓ active" if user.active else "✗ inactive"
        print(f"  {user.user_name}: {user.display_name} ({status})")
    
    # ====================
    # Get user by username
    # ====================
    print("\n=== Get User by Username ===")
    user = api.scim.get_user_by_username("john.doe@example.com")
    if user:
        print(f"Found: {user.display_name}")
        print(f"  ID: {user.id}")
        print(f"  Active: {user.active}")
        if user.name:
            print(f"  Name: {user.name.given_name} {user.name.family_name}")
    else:
        print("User not found")
    
    # ====================
    # Create a new user
    # ====================
    print("\n=== Create New User ===")
    new_user = ScimUser(
        user_name="jane.doe@example.com",
        display_name="Jane Doe",
        active=True,
        name=ScimUserName(
            given_name="Jane",
            family_name="Doe",
            formatted="Jane Doe"
        ),
        emails=[
            ScimUserEmail(
                value="jane.doe@example.com",
                type="work",
                primary=True
            )
        ]
    )
    
    # Uncomment to actually create:
    # created = api.scim.create_user(new_user)
    # if created:
    #     print(f"Created user: {created.display_name} ({created.id})")
    print("(Skipped - uncomment to create)")
    
    # ====================
    # Update user display name
    # ====================
    print("\n=== Update Display Name ===")
    # Uncomment with a real user ID to update:
    # updated = api.scim.update_display_name("user-id-here", "Jane Smith")
    # if updated:
    #     print(f"Updated name to: {updated.display_name}")
    print("(Skipped - uncomment with real user ID)")
    
    # ====================
    # Deactivate a user
    # ====================
    print("\n=== Deactivate User ===")
    # Uncomment with a real user ID to deactivate:
    # deactivated = api.scim.deactivate_user("user-id-here")
    # if deactivated:
    #     print(f"User {deactivated.display_name} is now inactive")
    print("(Skipped - uncomment with real user ID)")
    
    # ====================
    # Reactivate a user
    # ====================
    print("\n=== Reactivate User ===")
    # Uncomment with a real user ID to reactivate:
    # reactivated = api.scim.set_user_active("user-id-here", active=True)
    # if reactivated:
    #     print(f"User {reactivated.display_name} is now active")
    print("(Skipped - uncomment with real user ID)")
    
    # ====================
    # Delete a user
    # ====================
    print("\n=== Delete User ===")
    # Uncomment with a real user ID to delete:
    # api.scim.delete_user("user-id-here")
    # print("User deleted")
    print("(Skipped - uncomment with real user ID)")


if __name__ == "__main__":
    main()
