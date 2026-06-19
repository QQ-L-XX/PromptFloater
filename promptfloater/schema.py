"""Validation and normalization for PromptFloater prompt documents."""

SCHEMA_VERSION = 1
MAX_CATEGORIES = 100
MAX_ITEMS = 2_000
MAX_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 200
MAX_CONTENT_LENGTH = 50_000


class ValidationError(ValueError):
    """Raised when imported or persisted prompt data is invalid."""


def _required_string(value, path, max_length, *, allow_empty=False):
    if not isinstance(value, str):
        raise ValidationError(f"{path} 必须是字符串")
    if not allow_empty and not value.strip():
        raise ValidationError(f"{path} 不能为空")
    if len(value) > max_length:
        raise ValidationError(f"{path} 长度不能超过 {max_length}")
    return value


def validate_document(data: object) -> dict:
    """Return a normalized copy of a prompt document or raise ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError("数据根节点必须是对象")

    version = data.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise ValidationError(f"不支持的 schema_version: {version}")

    categories = data.get("categories")
    if not isinstance(categories, list):
        raise ValidationError("categories 必须是数组")
    if len(categories) > MAX_CATEGORIES:
        raise ValidationError(f"分类数量不能超过 {MAX_CATEGORIES}")

    normalized_categories = []
    category_ids = set()
    item_ids = set()
    total_items = 0

    for category_index, category in enumerate(categories):
        path = f"categories[{category_index}]"
        if not isinstance(category, dict):
            raise ValidationError(f"{path} 必须是对象")
        category_id = _required_string(category.get("id"), f"{path}.id", MAX_NAME_LENGTH)
        if category_id in category_ids:
            raise ValidationError(f"分类 ID 重复: {category_id}")
        category_ids.add(category_id)
        name = _required_string(category.get("name"), f"{path}.name", MAX_NAME_LENGTH)
        items = category.get("items")
        if not isinstance(items, list):
            raise ValidationError(f"{path}.items 必须是数组")

        normalized_items = []
        for item_index, item in enumerate(items):
            item_path = f"{path}.items[{item_index}]"
            if not isinstance(item, dict):
                raise ValidationError(f"{item_path} 必须是对象")
            item_id = _required_string(item.get("id"), f"{item_path}.id", MAX_NAME_LENGTH)
            if item_id in item_ids:
                raise ValidationError(f"提示词 ID 重复: {item_id}")
            item_ids.add(item_id)
            content = _required_string(item.get("content"), f"{item_path}.content", MAX_CONTENT_LENGTH)
            desc = item.get("desc", "")
            desc = _required_string(desc, f"{item_path}.desc", MAX_DESCRIPTION_LENGTH, allow_empty=True)
            fav = item.get("fav", False)
            if not isinstance(fav, bool):
                raise ValidationError(f"{item_path}.fav 必须是布尔值")
            normalized_items.append({"id": item_id, "content": content, "desc": desc, "fav": fav})
            total_items += 1
            if total_items > MAX_ITEMS:
                raise ValidationError(f"提示词总数不能超过 {MAX_ITEMS}")

        normalized_categories.append({"id": category_id, "name": name, "items": normalized_items})

    return {"schema_version": SCHEMA_VERSION, "categories": normalized_categories}
