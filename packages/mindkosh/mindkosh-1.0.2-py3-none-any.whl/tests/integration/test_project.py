import pytest


def test_project(client, random_str):
    projects = client.project.get()
    ids = []
    for project in projects:
        assert isinstance(project, client.project)
        ids.append(project.project_id)

    # create
    name = random_str(5)
    description = random_str(5) + " " + random_str(4)

    new_project = client.project.create(
        name=name,
        description=description
    )

    assert name == new_project.name
    assert description == new_project.description

    updated_projects = client.project.get()
    assert len(updated_projects) == len(projects) + 1
    updated_ids = []
    for project in updated_projects:
        assert isinstance(project, client.project)
        updated_ids.append(project.project_id)

    new_project_id = new_project.project_id
    assert new_project_id in updated_ids
    ### update name ###
    new_name = random_str(6)
    updated_project = new_project.update_name(
        name=new_name
    )

    assert new_project.name == new_name

    ### update description ###
    new_description = random_str(2) + " " + random_str(9)
    updated_project = new_project.update_description(
        description=new_description
    )

    assert new_project.description == new_description

    ### delete project ###
    new_project.delete()
    updated_projects = client.project.get()
    assert len(updated_projects) == len(projects)
    updated_ids = []
    for project in updated_projects:
        assert isinstance(project, client.project)
        updated_ids.append(project.project_id)

    assert new_project_id not in updated_ids


def test_exceptions(client):
    ### create ###
    name = "  "
    with pytest.raises(Exception) as e_info:
        new_project = client.project.create(
            name=name
        )
