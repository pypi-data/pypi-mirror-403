
def test_create_tag(client,random_str):

    name = random_str(5)
    
    new_tag = client.create_tag(
        name = name
    )

    assert new_tag['name'] == name
