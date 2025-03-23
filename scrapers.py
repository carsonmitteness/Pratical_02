# TODO: make a requirements.txt
from bs4 import BeautifulSoup
import requests
# used for formatting the name better -> prepend with scraped.txt
from urllib.parse import urlparse


def create_file_name(url):
    parsed_url_path = urlparse(url)
    path_name = parsed_url_path.path.split('/')
    cleaned_list = [item for item in path_name if item]
    name_ending = "-".join(cleaned_list)
    domain_name = parsed_url_path.netloc.split('.')[1]

    return f"{domain_name}-{name_ending}"

def combine_spans_into_ones(lst):
    return_string = ''

    # basic formatting that the LLM probably doesn't care about
    for wrd in lst:
        word_info = wrd.get_text()
        white_space_removed = word_info.strip()

        if  white_space_removed == '>>>'  or white_space_removed == '...':
            return_string += ' '
        else:
            return_string += word_info
    
    return return_string

def filter_header_links(str):
    ret = ''
    for char in str:
        if not char  == '¶' or not char == '#':
            ret += char

    return ret

# TODO: this likely can work with the redispy examples so try them: 
def scrape_read_the_docs_mongo_link(url, path_name):
    total_content = ''
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')

    create_name = create_file_name(url)

    header = soup.find('h1')
    link_subject = filter_header_links(header.get_text())
    headers = ['h2', 'h3', 'h4']

    # TODO: maybe a method that adds this whitespace so its pleasant to look through?
    total_content += link_subject + ' '
    
    # Mongo Pages follow along in sections
    for element in soup.find_all('section'):

        for header in headers:
            sub_header = element.find(header)
            if not sub_header == None:
                header_content = filter_header_links(sub_header.get_text())
                total_content += header_content + ' '

        paragraphs = element.find_all('p')
        for paragraph in paragraphs:
            # TODO: sub elements format weirdly?
            details = paragraph.get_text()
            total_content += details + ' '

        code_blocks = element.find_all('pre')
        for code_block in code_blocks: 
            spans = code_block.find_all('span')
            
            code_details = combine_spans_into_ones(spans)
            total_content += code_details + ' '

        # after each separate with a space:
        total_content += ' ' 
    
    # TODO: the files are formatted a bit weird, idk if its invisible characters or anything, but looks alright
    file_name = f"{path_name}/{create_name}.txt"
    with open(file_name, "w") as file:
        file.write(total_content)

# Note to self: Results seem fine:

# Redis io official examples:
def scrape_redis_develop(url, path_name):
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')
    # there are two sections one for sidebar -> ignore it and just pull from the first section:
    page_content = soup.find('section')

    create_name = create_file_name(url)

    total_content = ''
    # data is sequential for the most part in one big section:
    for element in page_content.contents:
        # TODO: whitespace on this is bad -> should try and remove these with each line I add
        element_type = element.name
        if element_type == None:
            # ignore blank tags
            continue
        
        # # element is a paragraph:
        if element_type == 'p':
            details = element.get_text()
            total_content += details

        # # headers
        if element_type == 'h1' or element_type == 'h2':
            details = element.get_text().strip()
            total_content += details

        # # these code blocks are nested inside divs:
        if element_type == 'div':
            if 'highlight' in element['class']:
            # all divs are highlight blocks for code:
                code_block = element.next_element.next_element
                code_details = combine_spans_into_ones(code_block)
                total_content += code_details
            
        # unnested code blocks: 
        if element_type == 'pre':
            # TODO: idk double check this: This only applies to like 5 pages, but I can just pull them normally without spans, but see:
            total_content += element.get_text() + ' '
            spans = element.find_all('span')

            code_details = combine_spans_into_ones(spans)
            total_content += code_details

    file_name = f"{path_name}/{create_name}.txt"
    with open(file_name, "w") as file:
        file.write(total_content)


# TODO: will implement a driver a bunch of links that can be passed into here:
def pull_data_from_block(code_tag):
    total_string = ''

    # lots of sub-calls which may not be idea? -> Idk maybe have to work something else out Idk why this is so slow...
    table_rows = code_tag.find_all('tr')
    for row in table_rows:
        row_text = row.get_text()
        total_string += row_text + ' '
    
    return total_string

# return back the string collected:
def handle_section(soup_element):
    headers = ['h1', 'h2', 'h3']

    element_type = soup_element.name
    if element_type == None:
        return ''

    if element_type == 'p':
        total_string = soup_element.get_text() + ' '
        return total_string

    # headers format a bit differently:
    if element_type in headers:
        total_string = soup_element.get_text().strip() + ' '
        return total_string

    if element_type == 'ul' or element_type == 'ol':
        total_string = ''
        # any list items:
        list_items = soup_element.find_all('li')
        for item in list_items:
            parsed_item = handle_section(item)
            total_string += parsed_item

        return total_string


    if element_type == 'div':
        total_string = ''
        for item in soup_element.contents:
            if item.name == 'pre':
                total_string += pull_data_from_block(item)

            else:
                total_string += handle_section(item)
        return total_string

    else:
        # default case:
        return ''


# TODO: test with more to make sure this doesn't blow up...
def scrape_mongo_driver_docs(url, path_name):
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')

    create_name = create_file_name(url)

    total_content = ''

    # it looks like all possibilties are just at the bottom?
    main_div = soup.find(id='template-container')
    main_content = main_div.find('main')
    main_section = main_content.find('section')

    header = main_section.find('h1')
    link_subject = filter_header_links(header.get_text())

    total_content += link_subject + ' '
                
    for element in main_section.find_all('section'):
        for item in element.contents:
            total_content += handle_section(item)

        nested_section = element.find_all('section')
        for section in nested_section:
            total_content += handle_section(section)

    file_name = f"{path_name}/{create_name}.txt"
    with open(file_name, "w") as file:
        file.write(total_content)

def read_description_list(element):
    total_string = ''

    for item in element.contents:
        item_name = item.name

        if item_name == 'dt' or item_name == 'dd' :
            total_string +=  item.get_text() + ' '

    return total_string

def pull_text_from_detail(detail):
    total_string = ''

    # can just go down the line
    for element in detail.contents:
        # can't do element.type b/c its a string:
        total_string += element.get_text().strip() + ' '

    return total_string


def scrape_redis_documentation_page(url, base_path):
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')

    create_name = create_file_name(url)

    total_content  = ''

    main_content = soup.find('main')
    main_section = main_content.find('section', class_='prose')

    header = main_section.find('h1')
    link_subject = filter_header_links(header.get_text())

    total_content += link_subject + ' '

    for element in main_section.contents:
        element_type = element.name

        if element_type == None:
            continue

        if element_type == 'details':
            total_content += pull_text_from_detail(element)

        if element_type == 'dl':
            total_content += read_description_list(element)

        # element is a paragraph:
        if element_type == 'p':
            details = element.get_text()
            total_content += details + ' '

        # headers
        if element_type == 'h1' or element_type == 'h2':
            details = element.get_text().strip()
            total_content += details

        # these code blocks are nested inside divs:
        if element_type == 'div':
            if 'highlight' in element['class']:
            # all divs are highlight blocks for code:
                code_block = element.next_element.next_element
                code_details = combine_spans_into_ones(code_block)
                total_content += code_details

        # also normal list items:
        if element_type == 'ul' or element_type == 'ol':
            total_string = ''
            # any list items:
            list_items = element.find_all('li')
            for item in list_items:
                parsed_item = handle_section(item)
                total_string += parsed_item

            total_content += total_string 

        # top level items:
        if element_type == 'pre':
            # see if its top level:
            total_content += element.get_text() + ' '
            # double check for both cases:
            spans = element.find_all('span')
            code_details = combine_spans_into_ones(spans)
            total_content += code_details

    file_name = f"{base_path}/{create_name}.txt"
    with open(file_name, "w") as file:
        file.write(total_content)


def get_doc_crawler_links():
    url = 'https://redis.io/docs/latest/commands/'
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')

    total_array = []

    main_content = soup.find('main')
    content_grid = main_content.find(id='commands-grid')

    for link in content_grid.find_all('a'):
        path = link.get('href')
        total_path = f'https://redis.io/{path}'
        total_array.append(total_path)
    
    return total_array


# runs through all of the links and examples for scraping and writes them to the given destination:
def main_scraper():
    base_path = 'data/documentation'

    read_the_docs_links = [
        'https://pymongo.readthedocs.io/en/stable/tutorial.html',
        'https://pymongo.readthedocs.io/en/stable/examples/aggregation.html',
        'https://pymongo.readthedocs.io/en/stable/examples/authentication.html',
        'https://pymongo.readthedocs.io/en/stable/examples/collations.html',
        'https://pymongo.readthedocs.io/en/stable/examples/copydb.html',
        'https://pymongo.readthedocs.io/en/stable/examples/custom_type.html',
        'https://pymongo.readthedocs.io/en/stable/examples/bulk.html',
        'https://pymongo.readthedocs.io/en/stable/examples/client_bulk.html',
        'https://pymongo.readthedocs.io/en/stable/examples/datetimes.html',
        'https://redis.readthedocs.io/en/stable/examples/connection_examples.html',
        'https://redis.readthedocs.io/en/stable/examples/search_json_examples.html',
        'https://redis.readthedocs.io/en/stable/examples/set_and_get_examples.html',
        'https://redis.readthedocs.io/en/stable/examples/search_vector_similarity_examples.html',
        'https://redis.readthedocs.io/en/stable/examples/pipeline_examples.html',
        'https://redis.readthedocs.io/en/stable/examples/redis-stream-example.html',
    ]

    # for link in read_the_docs_links:
    #     print(f'Processing link: {link}')
    #     scrape_read_the_docs_mongo_link(link, base_path)


    # commented out are the overview files (not too sure how helpful they are...)
    mongo_db_manual_links = [
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/connect/mongoclient/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/connect/connection-targets/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/databases-collections/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/insert/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/specify-query/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/find/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/specify-documents-to-return/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/project/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/count/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/distinct/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/cursors/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/update/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/delete/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/bulk-write/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/gridfs/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/configure/',
        #  'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/filtered-subset/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/group-total/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/unpack-arrays/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/one-to-one-join/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/aggregation/multi-field-join/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/data-formats/bson/',
        'https://www.mongodb.com/docs/languages/python/pymongo-driver/current/data-formats/dates-and-times/',
    ]

    for link in mongo_db_manual_links:
        print(f'Processing link: {link}')
        scrape_mongo_driver_docs(link, base_path)

    redis_docs = [
        'https://redis.io/docs/latest/develop/clients/redis-py/connect/',
        'https://redis.io/docs/latest/develop/clients/redis-py/queryjson/',
        'https://redis.io/docs/latest/develop/clients/redis-py/vecsearch/',
        'https://redis.io/docs/latest/develop/clients/redis-py/transpipe/'
    ]

    for link in redis_docs:
        print(f'Processing link: {link}')
        scrape_redis_develop(link, base_path)

    # TODO/ nice to have some of the sites have some useful links (https://redis.io/docs/latest/develop/data-types/strings/ and mongo docs),
    # but the scraper can't work on the terminals with code option selects

    # embeddings are small for this -> barely double the amount from the pdfs:

    # Do this last...
    # redis_commands = get_doc_crawler_links()
    # for link in redis_commands:
    #     print(f'Processing link: {link}')
    #     scrape_redis_documentation_page(link, base_path)


if __name__ == "__main__":
    main_scraper()


