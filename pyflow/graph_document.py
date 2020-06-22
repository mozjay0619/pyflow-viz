from bokeh.io import output_notebook, show, output_file
from bokeh.layouts import gridplot
from bokeh.models.widgets import Div
from bokeh.models.widgets import Paragraph
from bokeh.models.widgets import PreText
from bokeh.plotting import figure, show, output_file
import bokeh

import numpy as np
import struct
import imghdr
import base64
import os

from subprocess import check_call
from scipy import optimize
from skimage import io

TMP_DIGRAPH_FILEPATH = 'digraph.png'
TMP_GRAPH_RENDER_FILEPATH = 'pyflow_tmp'
TMP_GRAPH_RENDER_PDF_FILEPATH = 'pyflow_tmp.pdf'
TMP_PNG_FILEPATH = 'OutputFile.png'

def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0) # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception: #IGNORE:W0703
                return
        else:
            return
        return width, height
    
def add_graph_alias(graph_obj):
    
    html_str = "<h3>{}</h3>".format(graph_obj.graph_alias)
    return html_str

def add_graph_image(graph_obj, dirpath=None, filename=None, summary=True, graph_attributes=None):
    
    graph_img_path = graph_obj.save_view(summary=summary, graph_attributes=graph_attributes, 
                                         dirpath=dirpath, filename=filename)
    
    html_str = "<html>\n"
    data_uri = base64.b64encode(open(graph_img_path, 'rb').read()).decode('utf-8')
    html_str += '<img src="data:image/png;base64,{}">'.format(data_uri)
    
    os.remove(graph_img_path)
    return html_str

def add_method_doc_string(graph_obj):
        
    html_str = ""
    ops_dict = {k: v for k, v in graph_obj.graph_dict.items() if v['type']=='operation'}
    ops_uids = list(ops_dict.keys())
    ops_uids = sorted(ops_uids, key = lambda x: int(x.split('_')[-1]))

    for op_uid in ops_uids:
        func_name = ops_dict[op_uid]['method_attributes']['name']
        func_docstr = ops_dict[op_uid]['method_attributes']['doc_string']

        if func_docstr is None:
            func_docstr = ""
            
        else:

            tmp_docstrs = func_docstr.split('\n')

            stripped_tmp_docstrs = [elem.lstrip() for elem in tmp_docstrs]

            while(stripped_tmp_docstrs[0]==''):
                tmp_docstrs.pop(0)
                stripped_tmp_docstrs.pop(0)


            while(stripped_tmp_docstrs[-1]==''):
                tmp_docstrs.pop()
                stripped_tmp_docstrs.pop()

            tmp_docstrs_body = tmp_docstrs[1:]

            while True:
                
                first_letters = [elem[0] for elem in tmp_docstrs_body if not elem=='' and elem[0]==' ']

                if len(first_letters)==0:
                    break
                
                if len(first_letters)==len([elem for elem in tmp_docstrs_body if not elem=='']):
                    tmp_docstrs_body = [elem[1:] for elem in tmp_docstrs_body]
                
                else:
                    break
        
            tmp_docstrs_header = tmp_docstrs[0].lstrip()
            tmp_docstrs_body.insert(0, tmp_docstrs_header)

            tmp_docstrs_body.insert(0, '')
            tmp_docstrs_body.append('')

            tmp_docstrs = ['    ' + elem for elem in tmp_docstrs_body]
            func_docstr = '\n'.join(tmp_docstrs)
        
        html_str += "\u25B6 {}\n".format(func_name)
        html_str += "{}\n".format(func_docstr)

    return html_str

def get_layout_elements(graph_obj, pixel_offset):

    graph_img_path = graph_obj.save_view(summary=True, graph_attributes=None, 
                                         dirpath=None, filename=None)

    img_width_x, img_height_y = get_image_size(graph_img_path)
    
    frame_width_x, frame_height_y = 975, max(550, min(img_height_y, 750))

    graph_overview_header = Div(text="""<h2>Graphs Overview</h2>""", width=300, height=40)
    graph_alias = Div(text=add_graph_alias(graph_obj), width=500, height=40)

    method_docstrs = PreText(text=add_method_doc_string(graph_obj), width=630, height=frame_height_y, 
                             style={'overflow-y':'scroll',
                                    'height':'{}px'.format(frame_height_y), 
                                    'margin-right': 'auto', 
                                    'margin-left': 'auto'})

    p = figure(x_range=(0, frame_width_x), y_range=(frame_height_y, 0))  # visible range
    p.xaxis.visible = False
    p.yaxis.visible = False 
    p.xgrid.visible = False
    p.ygrid.visible = False
    p.background_fill_color = None
    p.border_fill_color = None

    p.plot_width=frame_width_x
    p.plot_height=frame_height_y

    MAX_RATIO = 1.25

    if (img_width_x > frame_width_x) or (img_height_y > frame_height_y):
        width_ratio = img_width_x / frame_width_x
        height_ratio = img_height_y / frame_height_y

        max_ratio = max(width_ratio, height_ratio)
        if max_ratio > MAX_RATIO:
            max_ratio = MAX_RATIO

        img_width_x = img_width_x / max_ratio
        img_height_y = img_height_y / max_ratio

    graph = graph_obj.view()
    filepath_ = graph.render('pyflow_tmp')
    
    print("\u2714 Rendering graph [ {} ]...          ".format(graph_obj.graph_alias), end="", flush=True)
    dpi = tune_dpi(img_height_y, img_width_x)
    dpi = int(dpi[0])
    check_call(['dot','-Tpng', '-Gdpi={}'.format(dpi+pixel_offset), TMP_GRAPH_RENDER_FILEPATH, '-o', TMP_PNG_FILEPATH])

    img = io.imread(TMP_PNG_FILEPATH)

    if img.shape[-1]==3:
        rgba = np.zeros([*img.shape[0:2], 4])
        rgba[:, :, 3] = 255
        rgba[:, :, 0:3] = img
        img = rgba
        img = img.astype(np.uint8)

    p.image_rgba(image=[np.array(img)[::-1, :, :]], x=0, y=img_height_y, dw=img_width_x, dh=img_height_y, 
                  dilate=False, global_alpha=10)
    print('Completed!')
    
    return graph_alias, p, method_docstrs

def document(*graph_objs, filename=None, pixel_offset=-1):
    
    filename = 'graphs_overview.html'
    graph_overview_header = Div(text="""<h2>Graphs Overview</h2>""", width=300, height=40)
    
    grid = [[graph_overview_header, None]]
    
    for graph_obj in graph_objs:
        graph_alias, p, method_docstrs = get_layout_elements(graph_obj, pixel_offset)
        grid.append([graph_alias, None])
        grid.append([p, method_docstrs])
        
    grids = gridplot(grid, toolbar_location='right')
    
    output_file(filename, 
            title='Bokeh Figure')

    show(grids)
    
    filepath = os.path.join(os.getcwd(), filename)
    print('\nRendered html file location: {}'.format(filepath))

    cleanup_dir()

def tune_dpi(height, width):
    
    def f(x, args):
        if x[0] < 5:
            return 999999999
        check_call(['dot','-Tpng', '-Gdpi={}'.format(x[0]), TMP_GRAPH_RENDER_FILEPATH,'-o', TMP_PNG_FILEPATH])
        img = io.imread(TMP_PNG_FILEPATH)
        return mae(img.shape[0:2], args)
        
    re = optimize.minimize(f, x0=[50], 
                           args=[height, width],  method="Nelder-Mead")
    return re.x

def mae(array1, array2):
    
    return np.average(np.abs(np.asarray(array1) - np.asarray(array2)), axis=0)

def cleanup_dir():

    os.remove(TMP_DIGRAPH_FILEPATH)
    os.remove(TMP_GRAPH_RENDER_FILEPATH)
    os.remove(TMP_GRAPH_RENDER_PDF_FILEPATH)
    os.remove(TMP_PNG_FILEPATH)
