"""extract family names from megalist (20 levels deep from gnathostomata"""
import re, os.path, sys
from datetime import timedelta
import wikipedia # for scraping
import pickle

# obtained from https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Undef&id=7776&lvl=3&srchmode=1&keep=1&unlock
# but at level 20, which is like 13 MiB, so do note that
TAXONOMY_BROWSER_HTML_FILENAME = "Gnathostomata taxonomy.html"

EXCLUDE_LIST = {'Menidae', 'Gaidropsaridae', 'Batrachostomatidae', 'Centropidae'} # it's actually a set 😯
REPLACE_LIST = {
    'Belonidae':'Needlefish',
    'Mullidae': 'Goatfish',
    'Chilodontidae': 'Chilodontidae (fish)',
    'Ursidae': 'Bear',
    'Alcidae': 'Auk',
    'Coliidae': 'Mousebird',
    'Todidae': 'Tody',
    'Gruidae': 'Crane (bird)',
    'Hypocolidae': 'Grey hypocolius',
    'Mimidae': 'Mimid',
    'Ranidae': 'True frog'
    } # and this one's a dict 😲

def simple_write_list (l, filename):
    with open(filename, "w") as f:
        for el in l:
            f.write(str(el) + "\n")

def retcon (family_list):
    """Remove excluded families and replace Taxonomy Browser names with Wikipedia ones."""

    retconned = []
    for fam in family_list:
        if fam in REPLACE_LIST:
            retconned.append(REPLACE_LIST[fam]) # switch tax browser name to wk name
        elif fam not in EXCLUDE_LIST:
            retconned.append(fam) # only add if not in exclude list
    return sorted(retconned)

def parse_families (taxonomy_browser_dump_filename):
    """Parse the Tax Browser HTML and return a list of families.
    Also write files containing the members of 5 major class/clades."""
    
    re_str_pre = """(?<=TITLE="family")(.+)(<STRONG>)""" # initial capturing groups
    re_str_post = """(<\/STRONG>)""" # final capturing group
    family_pattern = re.compile(re_str_pre + """(.+)""" + re_str_post) # group 2 will be the family name

    def get_families (raw):
        tup_list = re.findall(family_pattern, raw)
        family_list = [tup[2] for tup in tup_list]
        return retcon(family_list)

    # get list of members in each class
    def get_families_in_segment (raw, start, end):
        pattern = f"({start})([\s\S]+)({end})"
        match = re.search(pattern, raw)
        family_list = get_families(match.group(2))
        return family_list

    """ dead code is poetic, don't you think?
    # check for cached result
    if os.path.isfile(out_name):
        with open(out_name, "r") as f:
            tup_list = [s.replace('\n', '') for s in f.readlines()]
        return tup_list
    """

    # read file and get list of families
    with open(taxonomy_browser_dump_filename, "r") as f:
        raw = f.read()
    family_list = get_families(raw)

    chondrichthyes = get_families_in_segment(raw, "<STRONG>Chondrichthyes<\/STRONG>", "<STRONG>Teleostomi<\/STRONG>")
    osteichthyes = get_families_in_segment(raw, "<STRONG>Teleostomi<\/STRONG>", "<STRONG>Tetrapoda<\/STRONG>")
    mammals = get_families_in_segment(raw, "<STRONG>Tetrapoda<\/STRONG>", "<STRONG>Sauropsida<\/STRONG>")
    sauria = get_families_in_segment(raw, "<STRONG>Sauropsida<\/STRONG>", "<STRONG>Amphibia<\/STRONG>")
    amphibia = get_families_in_segment(raw, "<STRONG>Amphibia<\/STRONG>", "<\/html>")
    
    # write lists for future use
    simple_write_list(chondrichthyes, "list_chond.txt")
    simple_write_list(osteichthyes, "list_ost.txt")
    simple_write_list(mammals, "list_mam.txt")
    simple_write_list(sauria, "list_saur.txt")
    simple_write_list(amphibia, "list_amp.txt")
    simple_write_list(family_list, "families in Gnathostomata.txt")

    return family_list

def setup_wikipedia_scraping (rate_lim_ms):
    # totally legit, I promise!
    wikipedia.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0")
    wikipedia.set_rate_limiting(True, min_wait=timedelta(milliseconds=rate_lim_ms))

def fetch_wikipedia_pages (family_list, data_dir="family_pages", use_cache=True):
    # configure scraping options
    setup_wikipedia_scraping(rate_lim_ms=500)

    # create directory
    os.makedirs(data_dir, exist_ok=True)

    # check for cached results
    if use_cache and any(os.scandir(data_dir)): # if directory is not empty...
        print("(Probably) nothing to do here! \n(Set 'use_cache=False' to refetch everything.)")
        return
    
    N = len(family_list)
    wk_page_list = []

    with open("fail_list.txt", "w") as fail_list:
        for i, fam in enumerate(family_list):
            print(f"({i+1}/{N}): {fam}")

            try:
                # see: https://github.com/goldsmith/Wikipedia/issues/192
                p = wikipedia.page(fam, auto_suggest=False, redirect=False)
                with open(f"{data_dir}/{fam}.txt", "w") as f:
                    f.write(p.content)
                wk_page_list.append(p)

            except Exception as e:
                fail_list.write(f"[{i+1}] : {fam} \n")
                fail_list.write(str(e) + "\n\n")
                print(str(e)+'\n')

    """
    # save list of WikipediaPage objects in case it's useful idk lol
    if use_cache:
        with open("wk_page_list.dump", "wb") as p_name:
            pickle.dump(wk_page_list, p_name, pickle.HIGHEST_PROTOCOL)
    """

def main ():
    # parse the taxonomy browser HTML document and print some lists
    family_list = parse_families(TAXONOMY_BROWSER_HTML_FILENAME)

    # fetch the relevant wiki pages
    fetch_wikipedia_pages(family_list, data_dir="family_pages")

    # refetch failures
    """
    retry_list = [
        'Triglidae',
        'Needlefish',
        'Goatfish',
        'Zeidae',
        'Chilodontidae (fish)',
        'Canidae',
        'Bear',
        'Felidae',
        'Auk',
        'Mousebird',
        'Columbidae',
        'Tody',
        'Crane (bird)',
        'Grey hypocolius',
        'Mimid',
        'True frog'
    ]
    fetch_wikipedia_pages(retry_list, use_cache=False)
    """
    
if __name__ == "__main__":
    main()

    

