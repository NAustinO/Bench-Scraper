<div id="top"></div>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->



<!-- ABOUT THE PROJECT -->
## About The Project

Recipe aggregator and image parsing tool that exports JSON output to file and a corresponding image folder containing all recipes with file path generation. Data is not included within this repository and is exploratory and for personal use only.

<!-- ### Built With -->

## Libraries
* [Scrapy](https://scrapy.org/)
* [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/)
* [Selenium WebDriver](https://www.selenium.dev/documentation/webdriver/)


## Example Output 
```json
{
   "url": "/recipes/1014736-stir-fried-pork-and-pineapple",
    "filters": [],
    "collections": [
        "Easy Stir Fry Recipes"
    ],
    "image_urls": [
        "https://static01.nyt.com/images/2016/06/06/dining/06COOKING-STIR-FRIED-PORK-PINEAPPLE1/06COOKING-STIR-FRIED-PORK-PINEAPPLE1-articleLarge.jpg"
    ],
    "title": "Stir-Fried Pork and Pineapple",
    "author": "Mark Bittman",
    "yields": "2 servings",
    "time": "About 30 minutes",
    "intro": "This recipe, an adaptation from “The Hakka Cookbook” by Linda Lau Anusasananan, came to The Times by way of Mark Bittman in 2013. The Hakka people are sometimes thought of as the Jews of China, because they’re dispersed all over the place. But the Hakkas cannot even point to an original homeland: you can find them everywhere. “Some people call us dandelions, because we thrive in poor soil,” says Ms. Anusasananan, who was born in California. Hakka dishes like this one, chow mein and pretty much anything in bean sauce, have defined Chinese-restaurant cooking for nearly everyone. This lively stir-fry comes together in about a half-hour and is easily doubled or tripled for a crowd. To make it more family- and weeknight-friendly, substitute sliced bell peppers for the fungus and canned pineapple for the fresh, and leave out (or greatly reduce) the chile peppers.",
    "tags": [
        "Asian",
        "Black Fungus",
        "Boneless Pork Shoulder",
        "Pineapple",
        "Dinner",
        "Quick",
        "Weekday",
        "Weeknight",
        "Main Course"
    ],
    "steps": [
        "For the pork: Cut the pork into slices\n1/8 inch thick, 2 inches long and\n1 inch wide. In a small bowl, stir together\nthe soy sauce, oil and cornstarch,\nand mix with the pork.",
        "For the sauce: In a small bowl mix the\nvinegar, sugar, soy sauce and salt.",
        "Rinse the fungus. In\na medium bowl, soak the fungus in\nhot water until soft and pliable, 5 to 15\nminutes, and then drain. Pinch out\nand discard any hard, knobby centers.\nCut the fungus into 1-inch pieces.\nTrim the ends off the scallions, and then\nchop them, including green tops, into\n2-inch lengths.",
        "Set a wok or a large frying pan over\nhigh heat. When the pan is hot, after\nabout 1 minute, add the oil and rotate\nthe pan to spread. Add the ginger\nand pork; stir-fry until the meat is lightly\nbrowned, about 2 minutes. Add the\npineapple, black fungus, sauce\nmixture, scallions and chile. Stir-fry until\npineapple is hot, 1 to 2 minutes.\nTransfer to a serving dish."
    ],
    "ingredients": {
        "For the Pork": [
            {
                "display": "8 ounces boneless pork shoulder or loin, trimmed of fat"
            },
            {
                "display": "2 teaspoons soy sauce"
            },
            {
                "display": "1 teaspoon vegetable oil"
            },
            {
                "display": "1 teaspoon cornstarch"
            }
        ],
        "For the Sauce": [
            {
                "display": "2 tablespoons rice vinegar"
            },
            {
                "display": "1 tablespoon sugar"
            },
            {
                "display": "1 tablespoon soy sauce"
            },
            {
                "display": "½ teaspoon salt"
            }
        ],
        "For the Stir-Fry": [
            {
                "display": "8 pieces dried black fungus, like cloud ears, each about 1 inch wide (see note)"
            },
            {
                "display": "3 scallions, including green tops"
            },
            {
                "display": "2 tablespoons vegetable oil"
            },
            {
                "display": "2 tablespoons thinly slivered fresh ginger"
            },
            {
                "display": "8 ounces fresh pineapple, cut into 3/4-inch chunks (about 1 cup)"
            },
            {
                "display": "5 to 8 thin rings fresh chile (preferably red)"
            }
        ]
    },
    "full_url": "https://cooking.nytimes.com/recipes/1014736-stir-fried-pork-and-pineapple",
    "images": [
        {
            "url": "https://static01.nyt.com/images/2016/06/06/dining/06COOKING-STIR-FRIED-PORK-PINEAPPLE1/06COOKING-STIR-FRIED-PORK-PINEAPPLE1-articleLarge.jpg",
            "path": "full/7a345a1a245ddf73a62f51f4a9758ec5f53bbc48.jpg",
            "checksum": "8d87f647ff30f3a4cc83d0f73f851cb7",
            "status": "uptodate"
        }
    ]
}
<<<<<<< HEAD
```

<p align="right">(<a href="#top">back to top</a>)</p>





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/othneildrew/Best-README-Template.svg?style=for-the-badge
[contributors-url]: https://github.com/othneildrew/Best-README-Template/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/othneildrew/Best-README-Template.svg?style=for-the-badge
[forks-url]: https://github.com/othneildrew/Best-README-Template/network/members
[stars-shield]: https://img.shields.io/github/stars/othneildrew/Best-README-Template.svg?style=for-the-badge
[stars-url]: https://github.com/othneildrew/Best-README-Template/stargazers
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/othneildrew/Best-README-Template/issues
[license-shield]: https://img.shields.io/github/license/othneildrew/Best-README-Template.svg?style=for-the-badge
[license-url]: https://github.com/othneildrew/Best-README-Template/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: hhttps://www.linkedin.com/in/nick-ozawa/
[product-screenshot]: images/screenshot.png
=======

```
>>>>>>> 92d10c9df7bec12da7e2c2545dcd3fb24ff9bf87
