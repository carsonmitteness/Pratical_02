# TODO: make a requirements.txt
from bs4 import BeautifulSoup
import requests
# used for formatting the name better -> prepend with scraped.txt
from urllib.parse import urlparse

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
        if not char  == '¶':
            ret += char

    return ret

# TODO: this likely can work with the redispy examples so try them: 
def scrape_read_the_docs_mongo_link(url):
    total_content = ''
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')

    header = soup.find('h1')
    link_subject = filter_header_links(header.get_text())

    # TODO: maybe a method that adds this whitespace so its pleasant to look through?
    total_content += link_subject + ' '

    # parse through each section:
    
    # Mongo Pages follow along in sections
    for element in soup.find_all('section'):
        sub_header = element.find('h2')
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
    file_name = f"{link_subject}.txt"
    with open(file_name, "w") as file:
        file.write(total_content)

# Note to self: Results seem fine:
# scrape_read_the_docs_mongo_link(url)


# TODO: file name can be split of this url_parse:
# Redis io official examples:
def scrape_redis_develop(url):
    page_detals = requests.get(url)
    soup = BeautifulSoup(page_detals.text, 'html.parser')
    # there are two sections one for sidebar -> ignore it and just pull from the first section:
    page_content = soup.find('section')

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
            
        # unested code blocks: 
        if element_type == 'pre':
            code_tag = element.find_all('code')
            spans = element.find_all('span')

            code_details = combine_spans_into_ones(spans)
            total_content += code_details

    # TODO: make this name better:
    file_name = f"Redis.txt"
    with open(file_name, "w") as file:
        file.write(total_content)


# TODO: will implement a driver a bunch of links that can be passed into here: