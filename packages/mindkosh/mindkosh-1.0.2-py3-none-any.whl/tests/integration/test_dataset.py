import os
import pytest
import random
import time


def test_duplicate_dataset_exception(client,random_str):
    name = random_str(5)
    data_type = random.choice(['image','video','pointcloud'])
    dst1 = client.create_dataset(
        name = name,
        data_type = data_type
    )

    with pytest.raises(Exception) as e_info:
        dst2 = client.create_dataset(
            name = name,
            data_type = data_type
        )
    
    client.delete_dataset(dst1['id'])


def test_image_datasets(client, random_str):
    datasets = client.get_datasets()
    ids = [dataset['id'] for dataset in datasets]

    ### create ###
    name = random_str(5)
    data_type = 'image'

    new_dataset = client.create_dataset(
        name = name,
        data_type = data_type
    )

    assert name == new_dataset['name']
    assert data_type == new_dataset['data_type']

    updated_datasets = client.get_datasets()
    assert len(updated_datasets) == len(datasets) + 1
    updated_dst_ids = [dataset['id'] for dataset in updated_datasets]

    new_dst_id = new_dataset['id']
    assert new_dst_id in updated_dst_ids
    
    ### Delete ###
    client.delete_dataset(new_dst_id)
    

def test_image_data(client,random_str):
    name = random_str(5)
    dst = client.create_dataset(
        name = name,
        data_type = 'image'
    )
    dataset_id = dst['id']
    local_path = '../assts/images'
    files_to_upload = os.listdir()
    files_count = len(files_to_upload)

    client.upload_files(
        dataset_id = dataset_id,
        resources = [local_path]
    )

    updated_dst = client.get_dataset(
        dataset_id =dataset_id
    )

    assert updated_dst['files_count'] == files_count

    files = client.get_dataset_files(dataset_id=dataset_id)
    for file in files:
        file_name = file.split('_',1)[1]
        assert file_name in files_to_upload


def test_pointcloud_data(client,random_str,PointCloudFile,RelatedFile):
    name = random_str(5)
    dst = client.create_dataset(
        name = name,
        data_type = 'pointcloud'
    )
    dataset_id = dst['id']
    pcd_file_name = 'test.pcd'
    pcd_files_dir = '../assets/pointcloud/'
    pcd_file_path = os.path.join(pcd_files_dir,pcd_file_name)
    image_dir = '../assets/images/'
    image_files = os.listdir(image_dir)
    image_file1 = os.path.join(image_dir,image_files[0])
    image_file2 = os.path.join(image_dir,image_files[1])
    
    pointcloudfile = PointCloudFile(
        filepath = pcd_file_path,
        related_files = [
            RelatedFile(
                filepath = image_file1,
                sequence = 2
            ),
            RelatedFile(
                filepath = image_file2,
                sequence = 1
            )
        ]
    )

    client.upload_pointcloud_data(
        dataset_id = dataset_id,
        pointcloudfile = pointcloudfile
    )
    time.sleep(3)

    files = client.get_dataset_files(dataset_id=dataset_id)
    assert len(files)==3
    for file in files:
        file_name = file['name'].split('_',1)[1]
        if file_name==pcd_file_name:
            related_files = file['related_files']
            assert len(related_files)==2
            break

    client.delete_dataset(dataset_id)