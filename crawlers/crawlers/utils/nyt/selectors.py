
from bs4.element import Tag


def is_card_without_duplicate(tag: Tag):
    return (
        tag.name == "a"
        and tag.has_attr("class")
        and "card-link" in tag["class"]
        and "image-anchor" in tag["class"]
        and "card_recipe_info" not in tag["class"]
    )

