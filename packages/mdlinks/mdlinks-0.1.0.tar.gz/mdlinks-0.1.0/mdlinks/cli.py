from importlib.metadata import version

import click
import lxml.html
import requests

__version__ = version("mdlinks")

USER_AGENT = f"mdlinks/{__version__}"


def get_html_page(url: str) -> lxml.html.HtmlElement:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT})
    assert resp.ok
    return lxml.html.fromstring(resp.content)


@click.command()
@click.version_option(__version__)
@click.option("-i", "--input-file", type=click.File(), default="-")
@click.option("-x", "--xpath", default="//title")
@click.option("-t", "--template", default="* [{title}]({url})")
def main(input_file, xpath, template):
    for url in (x.strip() for x in input_file):
        tree = get_html_page(url)
        title = tree.xpath(xpath)[0].text_content()
        output = template.format(title=title, url=url)
        print(output)
