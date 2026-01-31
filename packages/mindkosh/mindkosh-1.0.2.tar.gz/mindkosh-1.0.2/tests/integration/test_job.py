import os
from mindkosh.job import Job

def test_segment_and_job(client,Label,random_str):
    resourceDir = '../assets/images/' 
    segment_size = 2
    task  = client.task.create(
        name = random_str(),
        labels = (
            Label(
                name ="penguine",
                color = "#000000"
            ),
        ),
        resources = [os.path.abspath(resourceDir)],
        segment_size = segment_size
    )

    segments = task.segments
    assert len(segments)==segment_size
    frame = 0
    for segment in segments:
        assert segment['start_frame']==frame
        assert segment['stop_frame']==frame + (segment_size-1)
        frame += segment_size

        jobs = segment['jobs']
        for job in jobs:
            assert isinstance(job,Job)

    task.delete()
    