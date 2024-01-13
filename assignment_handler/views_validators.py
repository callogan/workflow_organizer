from django.contrib import messages

from assignment_handler.models import ProjectBlock
from assignment_handler.validation import ValidationResult


def validate_project_create_custom(request, form):
    predefined_blocks = ProjectBlock.predefined_blocks()
    block_names = set()
    keys = []
    indices = [block["index"] for block in predefined_blocks]

    for ind in indices:
        keys.append(f"block_{ind}_total_tasks")
        keys.append(f"block_{ind}_completed_tasks")

    for key in keys:
        block_index = int(key.split("_")[1])

        if str(block_index) in form.data.getlist("project_blocks", []):
            for block in predefined_blocks:
                if block["index"] == block_index:
                    block_names.add(block["name"])

    for key in keys:
        if key in form.data and form.data[key]:
            block_index = int(key.split("_")[1])

            for block in predefined_blocks:
                if block["index"] == block_index:
                    block_names.add(block["name"])

    block_names = list(block_names)

    # Creation of dictionary with indices and corresponding names of all entered blocks
    block_name_id_corp = {}

    for block_name in block_names:
        for predefined_block in predefined_blocks:
            if predefined_block["name"] == block_name:
                block_name_id_corp[predefined_block["index"]] = block_name

    # CREATION PRELIMINARY DATA FOR VALIDATION MAP
    # Сreation a dictionary with block indices of checkboxes marked
    checked_blocks = {}
    if "project_blocks" in form.data:
        value = form.data.getlist("project_blocks")

        if isinstance(value, list):
            checked_blocks["project_blocks"] = value
        else:
            checked_blocks["project_blocks"] = [value]

    # Creation a dictionary for grouping keys with the same numbers
    block_keys = {}

    for key in form.data:
        parts = key.split("_")

        if parts[0] == "block":
            block_num = parts[1]
        else:
            continue

        if block_num not in block_keys:
            block_keys[block_num] = []

        if form.data[key] != "":
            block_keys[block_num].append(key)

        if "blocks" in block_keys:
            del block_keys["blocks"]

        to_delete = []
        for k, v in block_keys.items():
            if not v:
                to_delete.append(k)

        for k in to_delete:
            del block_keys[k]

    # Validation map creation
    validation_map = {}
    for key, values in block_keys.items():
        validation_map[key] = values

    for checked_key, checked_values in checked_blocks.items():
        for i in range(len(checked_values)):
            value = checked_values[i]

            if value not in validation_map:
                validation_map[value] = [checked_key]

    for checked_key, checked_values in checked_blocks.items():
        for value in checked_values:
            if isinstance(value, list):
                for v in value:
                    if v in validation_map and checked_key not in validation_map[v]:
                        validation_map[v].append(checked_key)
            else:
                if value in validation_map and checked_key not in validation_map[value]:
                    validation_map[value].append(checked_key)

    sorted_validation_map = {int(key): value for key, value in validation_map.items()}
    validation_map = dict(
        sorted(sorted_validation_map.items(), key=lambda item: item[0])
    )

    # Data minimum validation
    initial_errors_blocks = []
    initial_errors_tasks = []

    if not form.data.get("project_blocks"):
        initial_errors_blocks.append(
            "It is required to select at least one project block by marking the checkbox next to its name"
        )

    any_tasks_filled = False
    for field in form.data:
        if field.startswith("block_") and field.endswith("_total_tasks"):
            if form.data[field]:
                any_tasks_filled = True
                break

    if not any_tasks_filled:
        initial_errors_tasks.append(
            'It is required to fill in the "Total tasks" field for the corresponding selected project block'
        )

    if initial_errors_blocks and initial_errors_tasks:
        for error in initial_errors_blocks:
            messages.error(request, error)
        for error in initial_errors_tasks:
            messages.error(request, error)

    # MAIN VALIDATION PROCEDURE

    for block_id, fields in validation_map.items():
        expected_fields = get_expected_fields_for_create(block_id)

        missing_fields = set(expected_fields) - set(fields)

        for field in missing_fields:
            if field == "project_blocks":
                message = (
                    f"It is required to mark the checkbox next to the project block"
                    f' "{block_name_id_corp[int(block_id)]}"'
                )
                messages.error(request, message)
            if field.startswith("block_") and field.endswith("_total_tasks"):
                block_index = field.split("_")[1]
                message = (
                    f'It is required to fill in the "Total tasks" field for the project block'
                    f' "{block_name_id_corp[int(block_index)]}"'
                )
                messages.error(request, message)

    return ValidationResult(
        validation_map=validation_map, block_name_id_corp=block_name_id_corp
    )


def get_expected_fields_for_create(project_id):
    fields = []
    if 0 <= int(project_id) <= 6:
        fields = [f"block_{project_id}_total_tasks", "project_blocks"]
    return fields


def validate_project_update_structures_custom(form):
    project = form.save()

    all_blocks = project.projectblock_set.all()
    predefined_blocks = ProjectBlock.predefined_blocks()

    # Names of existing keys that were selected during editing
    block_names = set()

    for block in all_blocks:
        keys = [
            f"block_{block.id}_total_tasks",
            f"block_{block.id}_completed_tasks",
        ]

        if str(block.id) in form.data.get("existing_project_blocks", []):
            block_names.add(block.name)

        for key in keys:
            if key in form.data and form.data[key]:
                block_names.add(block.name)

    block_names = list(block_names)

    # Generating new block names
    new_block_names = set()

    keys = []

    indices = [block["index"] for block in predefined_blocks]

    for ind in indices:
        keys.append(f"new_block_{ind}_completed_tasks")
        keys.append(f"new_block_{ind}_total_tasks")

    for key in keys:
        block_index = int(key.split("_")[2])

        if str(block_index) in form.data.getlist("new_project_blocks", []):
            for block in predefined_blocks:
                if block["index"] == block_index:
                    new_block_names.add(block["name"])

    for key in keys:
        if key in form.data and form.data[key]:
            block_index = int(key.split("_")[2])

            for block in predefined_blocks:
                if block["index"] == block_index:
                    new_block_names.add(block["name"])

    new_block_names = list(new_block_names)

    # Creation of dictionary with indices and corresponding names of all entered blocks
    block_name_id_corp = {}

    for block_name in block_names:
        blocks = ProjectBlock.objects.filter(name=block_name)

        for block in blocks:
            block_index = block.id
            completed_tasks_key = f"block_{block_index}_completed_tasks"
            total_tasks_key = f"block_{block_index}_total_tasks"

            if (
                str(block_index) in form.data.get("existing_project_blocks", [])
                or form.data.get(completed_tasks_key, "") != ""
                or form.data.get(total_tasks_key, "") != ""
            ):
                block_name_id_corp[block_index] = block_name

    for block_name in new_block_names:
        for predefined_block in predefined_blocks:
            if predefined_block["name"] == block_name:
                block_name_id_corp[predefined_block["index"]] = block_name

    # Сreation a dictionary with block indices of checkboxes marked
    checked_blocks = {}
    for key in ["existing_project_blocks", "new_project_blocks"]:
        if key in form.data:
            value = form.data.getlist(key)

            if isinstance(value, list):
                checked_blocks[key] = value
            else:
                checked_blocks[key] = [value]

    # Creation a dictionary for grouping keys with the same numbers
    block_keys = {}

    for key in form.data:
        parts = key.split("_")

        if parts[0] == "block":
            block_num = parts[1]
        elif parts[0] == "new":
            block_num = parts[2]
        else:
            continue

        if block_num not in block_keys:
            block_keys[block_num] = []

        if form.data[key] != "":
            block_keys[block_num].append(key)

        if "blocks" in block_keys:
            del block_keys["blocks"]

        to_delete = []
        for k, v in block_keys.items():
            if not v:
                to_delete.append(k)

        for k in to_delete:
            del block_keys[k]

    validation_map = {}
    for key, values in block_keys.items():
        validation_map[key] = values

    for checked_key, checked_values in checked_blocks.items():
        for i in range(len(checked_values)):
            value = checked_values[i]

            if value not in validation_map:
                validation_map[value] = [checked_key]

    for checked_key, checked_values in checked_blocks.items():
        for value in checked_values:
            if isinstance(value, list):
                for v in value:
                    if v in validation_map and checked_key not in validation_map[v]:
                        validation_map[v].append(checked_key)
            else:
                if value in validation_map and checked_key not in validation_map[value]:
                    validation_map[value].append(checked_key)

    return ValidationResult(
        validation_map=validation_map, block_name_id_corp=block_name_id_corp
    )


def validate_project_update_procedure_custom(request, form):
    result = validate_project_update_structures_custom(form)

    messages_status = False

    for block_id, fields in result.validation_map.items():
        if int(block_id) <= 6 and len(fields) < 3:
            expected_fields = get_expected_fields_for_update(block_id)
            missing_fields = set(expected_fields) - set(fields)

            for field in missing_fields:
                if field.startswith("new_") and field.endswith("_total_tasks"):
                    block_index = field.split("_")[2]
                    message = (
                        f'It is required to fill in the "Total tasks" field for the project block'
                        f' "{result.block_name_id_corp[int(block_index)]}"'
                    )
                    existing_messages = [
                        str(msg) for msg in messages.get_messages(request)
                    ]
                    if message not in existing_messages:
                        messages.error(request, message)
                        messages_status = True
                if field == "new_project_blocks":
                    message = (
                        f"It is required to mark the checkbox next to the project block "
                        f' "{result.block_name_id_corp[int(block_id)]}"'
                    )
                    existing_messages = [
                        str(msg) for msg in messages.get_messages(request)
                    ]
                    if message not in existing_messages:
                        messages.error(request, message)
                        messages_status = True

        elif int(block_id) > 6 and len(fields) < 3:
            expected_fields = get_expected_fields_for_update(block_id)
            missing_fields = set(expected_fields) - set(fields)

            for field in missing_fields:
                if field.startswith("block_") and field.endswith("_total_tasks"):
                    block_index = field.split("_")[1]
                    message = (
                        f'It is required to fill in the "Total tasks" field for the project block'
                        f' "{result.block_name_id_corp[int(block_index)]}"'
                    )
                    existing_messages = [
                        str(msg) for msg in messages.get_messages(request)
                    ]
                    if message not in existing_messages:
                        messages.error(request, message)
                        messages_status = True
                if field.startswith("block_") and field.endswith("_completed_tasks"):
                    block_index = field.split("_")[1]
                    message = (
                        f'It is required to fill in the "Completed tasks" field for the project block'
                        f' "{result.block_name_id_corp[int(block_index)]}"'
                    )
                    existing_messages = [
                        str(msg) for msg in messages.get_messages(request)
                    ]
                    if message not in existing_messages:
                        messages.error(request, message)
                        messages_status = True
                if field == "existing_project_blocks":
                    message = (
                        f" It is required to mark the checkbox next to the project block"
                        f' "{result.block_name_id_corp[int(block_id)]}"'
                    )
                    existing_messages = [
                        str(msg) for msg in messages.get_messages(request)
                    ]
                    if message not in existing_messages:
                        messages.error(request, message)
                        messages_status = True

    return messages_status


def get_expected_fields_for_update(project_id):
    if 0 <= int(project_id) <= 6:
        fields = [
            f"new_block_{project_id}_total_tasks",
            f"new_block_{project_id}_completed_tasks",
            "new_project_blocks",
        ]
    else:
        fields = [
            f"block_{project_id}_total_tasks",
            f"block_{project_id}_completed_tasks",
            "existing_project_blocks",
        ]

    return fields
