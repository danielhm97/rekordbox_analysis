
# Función para contar cuantos elementos de cada tag hay en el xml_path
def check_childs_n_freq(xml_path):
    childs = {}
    for child in xml_path:
        if child.tag in childs:
            childs[child.tag] += 1
        else:
            childs[child.tag] = 1    
    return childs     

# Función para obtener el nombre del archivo sin la extensión
def get_file_name (path):
    import os
    from urllib.parse import urlparse, unquote
    
    # Parse and decode URL
    parsed = urlparse(path)
    decoded_path = unquote(parsed.path)
    ## Extract filename without extension
    return os.path.splitext(os.path.basename(decoded_path))[0]
