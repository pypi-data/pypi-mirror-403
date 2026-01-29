""" Utils to format responses
"""


def build_doc_list(documents):
    """Build document list

    Args:
        documents:

    Returns:

    """
    return (
        [
            {
                "content": document.content,
                "snippet_id": document.id,
                "data_id": str(document.meta["data_id"]),
                "data_pid": (
                    str(document.meta["data_pid"])
                    if "data_pid" in document.meta
                    else None
                ),
                "data_title": document.meta["title"],
                "score": document.score,
            }
            for document in documents
        ]
        if documents
        else []
    )


def build_doc_data_list(data_list, data_pids: dict[str, str] = None):
    """Build document list from data list

    Args:
        data_list:
        data_pids:

    Returns:

    """
    if not data_list:
        return list()

    data_pids = data_pids or dict()

    return (
        [
            {
                "content": data.content,
                "data_id": str(data.id),
                "data_pid": data_pids.get(str(data.id), None),
                "data_title": data.title,
            }
            for data in data_list
        ]
        if len(data_list)
        else []
    )
