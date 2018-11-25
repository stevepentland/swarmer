job_submit_schema = {
    'type': 'object',
    'required': ['image_name', 'callback_url'],
    'properties': {
        'image_name': {
            'type': 'string'
        },
        'callback_url': {
            'type': 'string'
        }
    }
}

task_submit_schema = {
    'type': 'object',
    'required': ['tasks'],
    'properties': {
        'tasks': {
            'type': 'array',
            'items': {
                'type': 'object',
                'required': ['task_name', 'task_args'],
                'properties': {
                    'task_name': {
                        'type': 'string'
                    },
                    'task_args': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'minItems': 0
                    }
                }
            },
            'minItems': 1
        }
    }
}

callback_result_schema = {
    'type': 'object',
    'required': ['task_name', 'task_status', 'task_result'],
    'properties': {
        'task_name': {
            'type': 'string'
        },
        'task_status': {
            'type': 'number'
        },
        'task_result': {
            'type': 'object',
            'required': ['stdout', 'stderr'],
            'properties': {
                'stdout': {
                    'type': 'string'
                },
                'stderr': {
                    'type': 'string'
                }
            }
        }
    }
}

schema_dict = {
    'job_submit': job_submit_schema,
    'task_submit': task_submit_schema,
    'result_submit': callback_result_schema
}


def get_schema_for(name: str) -> dict:
    return schema_dict[name]
