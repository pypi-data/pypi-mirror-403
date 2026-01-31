def test_user(client):
    user = client.user
    assert user is not None
    assert user.id and user.account

    account = user.account
    assert account.id and account.organization

    org = account.organization
    assert org.id and org.name and org.owner
