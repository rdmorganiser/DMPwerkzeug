import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_value_path(project, snapshot=None):
    if snapshot is None:
        return Path('projects') / str(project.id) / 'values'
    else:
        return Path('projects') / str(project.id) / 'snapshots' / str(snapshot.id) / 'values'


def is_last_owner(project, user):
    # check if user is owner
    if user in project.owners:
        # check if the user is the last owner
        return project.owners.count() <= 1
    else:
        return False


def check_conditions(conditions, values, set_prefix=None, set_index=None):
    if conditions:
        for condition in conditions:
            if condition.resolve(values, set_prefix, set_index):
                return True
        return False
    else:
        return True


def save_import_values(project, values, checked):
    for value in values:
        if value.attribute:
            value_key = '{value.attribute.uri}[{value.set_prefix}][{value.set_index}][{value.collection_index}]'.format(
                value=value
            )

            if value_key in checked:
                current_value = value.current
                if current_value is None:
                    # assert that this is a new value
                    assert value.pk is None

                    value.project = project
                    value.save()

                    if value.file:
                        value.copy_file(value.file_name, value.file)
                    else:
                        try:
                            name = value.file_import.get('name')
                            file = value.file_import.get('file')
                            value.file.save(name, file)
                        except AttributeError:
                            pass

                else:
                    # make sure we have the correct value
                    assert current_value.snapshot is None
                    assert current_value.attribute == value.attribute
                    assert current_value.set_prefix == value.set_prefix
                    assert current_value.set_index == value.set_index
                    assert current_value.collection_index == value.collection_index

                    # assert that this is an new value
                    assert current_value.pk is not None

                    current_value.text = value.text
                    current_value.option = value.option
                    current_value.value_type = value.value_type
                    current_value.unit = value.unit
                    current_value.save()

                    if value.file:
                        current_value.file.delete()
                        current_value.copy_file(value.file_name, value.file)
                    else:
                        try:
                            name = value.file_import.get('name')
                            file = value.file_import.get('file')
                            current_value.file.delete()
                            current_value.file.save(name, file)
                        except AttributeError:
                            pass


def save_import_snapshot_values(project, snapshots, checked):
    for snapshot in snapshots:
        # assert that this is a new snapshot
        assert snapshot.pk is None

        snapshot.project = project
        snapshot.save(copy_values=False)

        for value in snapshot.snapshot_values:
            if value.attribute:
                value_key = '{value.attribute.uri}[{snapshot_index}][{value.set_prefix}][{value.set_index}][{value.collection_index}]'.format(
                    value=value,
                    snapshot_index=snapshot.snapshot_index
                )

                if value_key in checked:
                    # assert that this is a new value
                    assert value.pk is None

                    value.project = project
                    value.snapshot = snapshot
                    value.save()


def save_import_tasks(project, tasks):
    for task in tasks:
        project.tasks.add(task)


def save_import_views(project, views):
    for view in views:
        project.views.add(view)
