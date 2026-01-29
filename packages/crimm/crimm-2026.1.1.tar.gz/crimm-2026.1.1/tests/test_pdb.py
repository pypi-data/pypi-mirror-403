import requests
import os
from crimm.IO import MMCIFParser as cifParser
from crimm.StructEntities.Chain import PolymerChain

def fetch_rcsb_cif(code):
    """Fetches a file from a remote location via HTTP.
    If a PDB code is given, the .cif form of that struture will be fetched from
    the RCSB servers. If that code is given an extension, that file format will
    be obtained instead of .cif. If a URL is given, the function will simply
    look in that location.
    For example:
    
        >>> atomium.fetch('1lol.mmtf', file_dict=True)
    
    This will get the .mmtf version of structure 1LOL, but only go as far as
    converting it to an atomium file dictionary.
    :param str code: the file to fetch.
    :param bool file_dict: if ``True``, parsing will stop at the file ``dict``.
    :param bool data_dict: if ``True``, parsing will stop at the data ``dict``.
    :raises ValueError: if no file is found.
    :rtype: ``File``"""

    if code.startswith("http"):
        url = code
    elif code.endswith(".mmtf"):
        url = "https://mmtf.rcsb.org/v1.0/full/{}".format(code[:-5].lower())
    else:
        if "." not in code: code += ".cif"
        url = "https://files.rcsb.org/view/" + code.lower()
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        text = response.content if code.endswith(".mmtf") else response.text
        return text
    raise ValueError("Could not find anything at {}".format(url))

def fetch_local_cif(pdb_id):
    pdb_id = pdb_id.lower()
    entry_point = '/mnt/backup/PDB/'
    subdir = pdb_id[1:3]
    file_path = os.path.join(entry_point, subdir,pdb_id+'.cif')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            cif_text = f.read()
        return cif_text

def find_local_cif_path(pdb_id):
    pdb_id = pdb_id.lower()
    entry_point = '/mnt/backup/PDB/'
    subdir = pdb_id[1:3]
    file_path = os.path.join(entry_point, subdir, pdb_id+'.cif')
    if os.path.exists(file_path):
        return file_path

def check_broken_chains(pdb_ids):
    Parser = cifParser(QUIET=True)
    broken = []
    failed = {'ValueError':[],'KeyError':[],'IndexError':[],'Other':[]}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for pdb_id in tqdm(pdb_ids):
            filepath = find_local_cif_path(pdb_id)
            if not filepath:
                print(pdb_id, ' not found!')
                continue
            try:
                model = Parser.get_structure(filepath)
                for chain in model:
                    if isinstance(chain, PolymerChain) and not chain.is_continuous():
                        broken.append(pdb_id)
                        break
            except ValueError:
                failed['ValueError'].append(pdb_id)
            except KeyError:
                failed['KeyError'].append(pdb_id)
            except IndexError:
                failed['IndexError'].append(pdb_id)
            except:
                failed['Other'].append(pdb_id)
    return broken, failed

if __name__ == "__main__":
    from random import randrange, seed
    import pickle
    import warnings
    from tqdm import tqdm
    from tqdm.contrib.concurrent import process_map

    with open('/home/truman/all_pdb_proteins.txt','r') as f:
        all_pdb_ids = f.read().strip().split(',')

    # all_pdb_ids = all_pdb_ids[:1000]
    n = 500
    chunks = [
        all_pdb_ids[i * n:(i + 1) * n] for i in range(
            (len(all_pdb_ids) + n - 1) // n
        )
    ]
    seed(42)
    with open('tqdm_progress.out', 'w') as fh:
        r = process_map(
                check_broken_chains, 
                chunks,
                file=fh,
                )
    
    all_broken = []
    all_failed = {'ValueError':[],'KeyError':[],'IndexError':[],'Other':[]}
    for broken, failed in r:
        all_broken.extend(broken)
        for key, val in failed.items():
            all_failed[key].extend(val)
    
    # print(all_broken, all_failed)
    # broken, failed = check_broken_chains(all_pdb_ids[:500])

    with open('broken_pdb_chain.txt', 'w') as f:
        for pdb_id in all_broken:
            f.write(pdb_id+'\n')
    
    with open('failed_pdb_chain.txt', 'w') as f:
        for key, val in all_failed.items():
            f.write(key+'\n')
            for pdb_id in val:
                f.write('\t'+pdb_id+'\n')

    with open('failed_dict.pkl', 'wb') as p:
        pickle.dump(all_failed, p)