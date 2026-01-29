from bs4 import BeautifulSoup


def transform_scripts(html_content):
    """Add type='text/pp' to script tags without a type attribute (only in body)"""
    has_doctype = html_content.strip().lower().startswith('<!doctype')

    soup = BeautifulSoup(html_content, 'html.parser')

    body = soup.find('body')
    if body:
        for script in body.find_all('script'):
            if not script.has_attr('type'):
                script['type'] = 'text/pp'

    result = str(soup)

    if has_doctype and not result.strip().lower().startswith('<!doctype'):
        result = '<!DOCTYPE html>\n' + result

    return result
