from paging import slice_page


def list_page(items, page, size):
    return {"items": slice_page(items, page, size), "total": len(items)}
