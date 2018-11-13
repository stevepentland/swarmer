""" This test suite expects an actual live redis instance to run against. 

You can accomplish this via running with docker like so:
docker run --rm --name test-redis -p 6379:6379 -d redis:5

When running, set the TEST_INCLUDE_REDIS environment variable
"""

import os

import pytest
import redis
import ulid

from db import JobLog


@pytest.mark.skipif(os.environ.get('TEST_INCLUDE_REDIS') is None, reason='requires local default redis to run')
class TestLiveJobLog:
    database = redis.StrictRedis()
    job_log = JobLog(database)

    def test_add_job_and_delete(self):
        job_key = ulid.new().str
        TestLiveJobLog.job_log.add_job(job_key, 'an_image', 'www.example.com')
        actual = TestLiveJobLog.job_log.get_job(job_key)
        assert actual == {'__image': 'an_image',
                          '__callback': 'www.example.com',
                          'tasks': '[]'}
        TestLiveJobLog.job_log.clear_job(job_key)
        with pytest.raises(ValueError):
            TestLiveJobLog.job_log.get_job(job_key) is None

    def test_add_tasks(self):
        job_key = ulid.new().str
        TestLiveJobLog.job_log.add_job(job_key, 'an_image', 'www.example.com')
        tasks = [{'task_name': 'first', 'task_args': [1, 2, 3]},
                 {'task_name': 'second', 'task_args': [3, 4, 5]}]
        TestLiveJobLog.job_log.add_tasks(job_key, tasks)
        actual = TestLiveJobLog.job_log.get_job(job_key)
        assert actual == {'__callback': 'www.example.com', '__image': 'an_image', '__task_count_complete': '0',
                          '__task_count_started': '0', '__task_count_total': '2',
                          'tasks': '[{"args": [1, 2, 3], "status": 500, "result": {"stdout": null, "stderr": null}, "name": "first"}, {"args": [3, 4, 5], "status": 500, "result": {"stdout": null, "stderr": null}, "name": "second"}]'}
        TestLiveJobLog.job_log.clear_job(job_key)
        with pytest.raises(ValueError):
            TestLiveJobLog.job_log.get_job(job_key) is None

    def test_update_status(self):
        job_key = ulid.new().str
        TestLiveJobLog.job_log.add_job(job_key, 'an_image', 'www.example.com')
        tasks = [{'task_name': 'first', 'task_args': [1, 2, 3]}]
        TestLiveJobLog.job_log.add_tasks(job_key, tasks)
        TestLiveJobLog.job_log.update_status(job_key, 'first', 1)
        actual = TestLiveJobLog.job_log.get_task(job_key, 'first')
        assert actual == {'args': [1, 2, 3], 'name': 'first',
                          'result': {'stdout': None, 'stderr': None}, 'status': 1}

    def test_update_result(self):
        job_key = ulid.new().str
        TestLiveJobLog.job_log.add_job(job_key, 'an_image', 'www.example.com')
        tasks = [{'task_name': 'first', 'task_args': [1, 2, 3]}]
        TestLiveJobLog.job_log.add_tasks(job_key, tasks)
        TestLiveJobLog.job_log.update_result(
            job_key, 'first', {'stdout': 'This is some text value', 'stderr': None})
        actual = TestLiveJobLog.job_log.get_task(job_key, 'first')
        assert actual == {'args': [1, 2, 3], 'name': 'first',
                          'result': {'stdout': 'This is some text value', 'stderr': None}, 'status': 500}

    @pytest.mark.parametrize('name,incr,expected', [
        ('__task_count_started', 1, 1),
        ('__task_count_started', 2, 2),
        ('__task_count_started', -1, -1),
        ('__task_count_complete', 1, 1),
        ('__task_count_complete', 2, 2),
        ('__task_count_complete', -1, -1)
    ])
    def test_modify_task_started_count(self, name, incr, expected):
        job_key = ulid.new().str
        TestLiveJobLog.job_log.add_job(job_key, 'an_image', 'www.example.com')
        tasks = [{'task_name': 'first', 'task_args': [1, 2, 3]},
                 {'task_name': 'second', 'task_args': [3, 4, 5]}]
        TestLiveJobLog.job_log.add_tasks(job_key, tasks)
        current = int(TestLiveJobLog.job_log.get_task_count(
            job_key, name))
        assert current == 0
        TestLiveJobLog.job_log.modify_task_count(
            job_key, name, incr)
        incremented = int(TestLiveJobLog.job_log.get_task_count(
            job_key, name))
        assert incremented == expected
