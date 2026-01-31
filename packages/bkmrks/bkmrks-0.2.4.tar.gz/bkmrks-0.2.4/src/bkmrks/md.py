from bkmrks import bkmrks, files, folders, icons, urls


def generate(md_file_name=None, catalog="index"):
    if md_file_name is None:
        md_file_name = folders.public_folder(path="index")

    bookmarks = bkmrks.get_catalog_data(catalog=catalog)
    md_file_content = ""
    if len(bookmarks) > 0:
        for line in bookmarks.values():
            if len(line) > 0:
                for item in line.values():
                    md_file_content += md_a_img(item)
            md_file_content += md_hr()
    if len(md_file_content) < 10:
        return None

    md_file_name = files.apply_ext(md_file_name, ext="md")

    with open(md_file_name, "+w") as f:
        f.write(md_file_content)
    return md_file_name


def md_a_img(item):
    try:
        url = item["url"]
    except:
        return ""
    if "name" in item:
        name = item["name"]
    else:
        name = urls.get_name_from_domain(url=url)

    if "img" in item:
        img = item["img"]
    else:
        img = icons.get_default_img(text=name)

    return f'\n[![{name}]({img})]({url} "{name}")'


def md_hr():
    return "\n---"
