
from bs4.element import Tag


def is_card_without_duplicate(tag: Tag):
    """
    This is a selector function for the BeautifulSoup find_all method.
    """
    return (
        tag.name == "a"
        and tag.has_attr("class")
        and "card-link" in tag["class"]
        and "image-anchor" in tag["class"]
        and "card_recipe_info" not in tag["class"]
    )


def search_page_articles(tag: Tag):
    """
    This is a selector function for the BeautifulSoup find_all method.
    Method for selecting article cards from the search page. 
    """
    return (
        tag.name == "article"
        and tag.has_attr("class")
        and "card" in tag["class"] 
        and tag.has_attr("data-type")
        and tag.has_attr("data-url")
    )