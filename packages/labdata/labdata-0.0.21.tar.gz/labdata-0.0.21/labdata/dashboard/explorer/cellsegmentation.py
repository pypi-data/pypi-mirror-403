from ...utils import *
from ...schema import *

# this uses dash and plotly
from dash import Dash, html, dash_table,dcc,Input,Output,callback,no_update, State
import plotly.express as px
import plotly.io as pio
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash_extensions import Keyboard

colors = ['#000000',
          '#1f77b4',
          '#d62728',
          '#ff7f0e',
          '#e377c2',
          '#7f7f7f',
          '#bcbd22']

def roi_color_projection(roi_masks):
    from matplotlib.colors import hsv_to_rgb
    from scipy import sparse as sp
    coloridx = np.random.choice(np.arange(1,256)/255.,len(roi_masks),replace=True)
    icells = [coloridx[i]*(m>0) for i,m in enumerate(roi_masks)] # get the cell index
    # check if sparse
    if sp.issparse(roi_masks[0]):
        allrois = sp.vstack(roi_masks).todense()
        allrois = allrois.reshape([len(roi_masks),*roi_masks[0].shape])
        icells = sp.vstack(icells).todense()
        icells = icells.reshape([len(roi_masks),*roi_masks[0].shape])
    xx = np.max(allrois,axis = 0).astype('float32')
    xx /= np.percentile(xx,99.5)
    xx = np.clip(xx,0,1)
    yy = np.max(icells,axis = 0).astype('float32')
    return (255*hsv_to_rgb(np.stack([yy,xx,xx]).transpose(1,2,0))).astype('uint8')

def plot_rois_projection(proj,rois_mask,roi_contours,cell_selection, cmap = 'gray',height = 600,width = 800,show_masks = True, show_bad = False):
    opacity = 1
    centers = []
    scatters = []
    cell_indices  = []
    for icell,r in enumerate(roi_contours):
        s = cell_selection.iloc[icell]
        if not r is None:
            if s['selection'] == 1:
                c = 'yellow'
            else:
                c = 'white'
                if not show_bad:
                    continue
            cell_indices.append(icell)
            scatters.append(go.Scatter(x=r[:,0],y =r[:,1],mode = 'lines', 
                                        line = dict(color = c,width = 0.8), showlegend=False,hoverinfo='skip'))
            centers.append([np.mean(r[:,0]),np.mean(r[:,1])])
        else:
            centers.append([np.nan,np.nan])
    centers = np.array(centers)
    scatters.append(go.Scatter(x = centers[:,0],
                               y = centers[:,1],
                               text = cell_indices,
                               mode='markers+text',
                               name = 'centers',
                               marker=dict(color='darkred',size=8),
                               customdata = cell_selection[["roi_num","selection"]],
                               hovertemplate =  ['<b>ROI num</b>: %{customdata[0]}<br>' + 
                      '<b>selection</b>: %{customdata[1]}<br> '+
                      '<extra></extra>'],
                      hoverinfo='all',
                      showlegend=False))
    fig = go.Figure()
    if show_masks:  # add masks
        opacity = 0.3
        rois_mask_im = roi_color_projection([rois_mask[i] for i in cell_indices])
        fig.add_trace(go.Image(z=rois_mask_im,hoverinfo = 'skip'))
        print('Including rois mask.')
    if not proj is None: # add projection
        fig.add_trace(go.Heatmap(z=proj,colorscale = cmap, showscale=False,
                                zmin=np.percentile(proj,5), 
                                zmax=np.percentile(proj,99.5),hoverinfo = 'skip',opacity = opacity))
    fig.add_traces(scatters) # add roi contours
    fig.data[-1].update(textfont_color= 'darkorange',textposition = 'top center')
    fig.layout.hovermode = 'closest'
    fig.update_yaxes(scaleanchor = "x", scaleratio = 1)
    fig.update_layout(xaxis=dict(visible=False),
                        yaxis = dict(visible=False),
                        coloraxis_showscale=False,
                        uirevision = 'donothing',
                        autosize=False,
                        showlegend = False,
                        width=width,      
                        height=height,
                        margin=dict(l=0, r=0, t=0, b=0),
                        #clickmode='event+select',
                        modebar_remove=['lasso2d', 'select2d'])
    return fig,cell_indices

def plot_traces(traces,cells,frame_rate = 1,height = 700,width = 600):
    time = np.arange(len(traces[0]))/frame_rate
    fig = go.Figure()
    scatters = []
    offset = 1
    for icell,trace in enumerate(traces):
        nt = trace - trace.min()
        nt /= nt.max()+0.0001
        scatters.append(go.Scatter(x=time, y = nt+icell*offset,mode = 'lines',
                                   name = f'ROI {cells.iloc[icell].roi_num}', 
                                   line = dict(color = colors[np.mod(icell,len(colors)-1)],
                                               width = 1.4), showlegend=False))
    fig.add_traces(scatters)
    fig.update_layout(xaxis=dict(visible=True),
                      yaxis = dict(visible=False),
                      uirevision = 'donothing',
                      width=width,      
                      height=height,
                      modebar_remove=['lasso2d', 'select2d'])
    return fig

def interactive_data_explorer(subject_filter = None,user_name = None, mode = 'load_all',#'fast_init',
                               debug = False, port='8051',open_browser = False):

    pio.templates.default = "simple_white"
    if subject_filter is None:
        if user_name in [None,'none']:
            subjects = (Subject & CellSegmentation).fetch('subject_name')
        else:
            subjects = (Subject & CellSegmentation & f'user_name = "{user_name}"').fetch('subject_name')
    else:
        subjects = (Subject & (CellSegmentation & f'subject_name LIKE "{subject_filter}"')).fetch('subject_name')
    params = CellSegmentationParams().fetch(as_dict = True)

    data= dict(sessions = None,
               selected_session = None,
               plane = [],
               cells_table = [],
               selected_cells = [],
               cell_info_data = [],
               cell_data = [],
               selected_cell = 0,
               dset = None,
               traces_mode = 'dff')
    app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        Keyboard(captureKeys = ["n","p","c"], id="keyboard",),
        dbc.Row([html.H2("Cell Segmentation session explorer",style = {'font-weight': 'bold'})]),
        dbc.Row([
            dbc.Col([html.Span("Subject:",style = {'font-weight': 'bold'})], width = 2),
            dbc.Col([dcc.Dropdown(subjects,None,id = 'subject_selection')], width = 3),
            dbc.Col([html.Span("Parameters:",style = {'font-weight': 'bold'})], width=2),
            dbc.Col([dcc.Dropdown([f"parameter_set_num = {p['parameter_set_num']}" for p in params],
                              None, id = 'params_table', multi=False)], width = 4),]),
        dbc.Row([dbc.Col([html.Span("Sessions:", style = {'font-weight': 'bold'})]),
                 dbc.Col([dash_table.DataTable(data=None,
                                                style_header={
                                                   'backgroundColor': 'rgb(230, 230, 230)',
                                                   'fontWeight': 'bold'},
                                                style_table = {'overflowY': 'scroll',
                                                               'height': '200px',
                                                               'border': '1px solid black'},
                                                style_cell = {'textAlign': 'left'},
                                                style_data = {'whiteSpace': 'normal',
                                                                'height': 'auto'},
                                                style_cell_conditional = [
                                                    {'if': {'column_id': 'col1'},
                                                     'width': '100px'}],
                                                row_selectable = 'single',
                                                id = 'sessions_table'),],
                                                width = 12)]),
        dbc.Row([dbc.Col([
            dbc.Row([html.Span("Selected plane:", style = {'font-weight': 'bold'})]),
                     dcc.Dropdown([],None, id = 'plane_selection', multi=False),
                     html.Span("Selected labeling:", style = {'font-weight': 'bold'}),
                     dcc.Dropdown([],None, id = 'labeling_selection', multi=False),
                     html.Span("Projection:", style = {'font-weight': 'bold'}),
                     dcc.Dropdown([],None, id = 'projection', multi=False),
                     dcc.Checklist(['Show ROI masks','Show all ROIs'],['Show ROI masks'], id = 'roi_masks'),
                     html.Span("Trace selection:", style = {'font-weight': 'bold'}),
                     dcc.Dropdown(['df/f','deconv','f_trace'],'df/f', id = 'trace_selection', multi=False),],width = 2),
            dbc.Col([dbc.Row([html.Span("ROIs and traces:", style = {'font-weight': 'bold'}),
                              dcc.Graph(id='projection_plot', style={'display': 'none','height':'600px'})]),
                              ],width = 10)]),
        dbc.Row([dcc.Graph(id='traces_heatmap_plot', style={'display': 'none','height':'600px'})]),
        dbc.Row([dbc.Col([dcc.Graph(id='cells_plot', style={'display': 'none','height':'600px'})],width = 3),
                 dbc.Col([dcc.Graph(id='traces_plot', style={'display': 'none','height':'600px'})],width = 9),]),
        dbc.Row([html.Span("Cells table:", style = {'font-weight': 'bold'})]),
        dbc.Row([dash_table.DataTable(data=None,
                                    style_header={'backgroundColor': 'rgb(230, 230, 230)',
                                                    'fontWeight': 'bold'},
                                    style_table = {'overflowY': 'scroll',
                                                   'overflowX': 'auto',
                                                   'height': '1000px',
                                                   'border': '1px solid black'},
                                    style_cell = {'textAlign': 'left','width': '150px',
                                                  },
                                    style_data = {'whiteSpace': 'normal',
                                                  'height': 'auto'},
                                    fixed_rows={'headers': True},
                                    style_cell_conditional = [],
                                    fill_width=False,
                                    page_action='none',
                                    row_selectable = 'multi', id = 'cells_table')])])
    # SESSIONS
    @callback(
        Output('sessions_table', 'data'),
        Output('sessions_table', 'selected_rows',allow_duplicate = True),
        Input('subject_selection', 'value'),
        Input('params_table', 'value'),prevent_initial_call = True)
    def update_sessions(value,param):
        if value is None:
            return
        if param is None or len(param) == 0:
            return no_update
        sessions = (CellSegmentation & 
            f"subject_name = '{value}'" &
            param).proj().fetch(as_dict = True)
        data['sessions'] = sessions
        return sessions,[]
    # SESSION SELECTED
    def update_data(dset,data,mode = 'load_all',traces_mode = None):
        if traces_mode == None:
            traces_mode = 'df/f'
        data['traces_mode'] = traces_mode
        if traces_mode == 'df/f':
            data['traces_mode'] = 'dff'
        print(f"Fetching {dset}")
        data['dset'] = dset
        if mode == 'fast_init':
            data['cells_data'] = None
        else:
            if traces_mode == 'deconv':
                print('Loading deconv.')
                data['cells_data'] = pd.DataFrame((CellSegmentation.Deconvolved & data['dset']).fetch())
            elif traces_mode == 'f_trace':
                print('Loading raw.')
                data['cells_data'] = pd.DataFrame((CellSegmentation.RawTraces & data['dset']).fetch())
            else:
                print('Loading df/f.')
                data['cells_data'] = pd.DataFrame((CellSegmentation.Traces & data['dset']).fetch())
            print('done loading.')
        tt = (CellSegmentation & dset).fetch1()
        if 'caiman' in tt['algorithm_version']:
            threshold = 70 # for caiman
        else:
            threshold = 20 # for suite2p
        data['rois_mask'] = (CellSegmentation.ROI & dset).get_roi_sparse_masks()
        data['contours'] = (CellSegmentation.ROI & dset).get_roi_contours(threshold)
        #data['roi_cm'] = [np.nanmean(c,axis = 1) for c in data['contours']]
        data['proj_names'],data['proj'] = (CellSegmentation.Projection & dset).fetch('proj_name','proj_im')
        data['proj_names'] = [n for n in data['proj_names']]
        data['proj_idx'] = data['proj_names'].index('std')
        data['selected_cell'] = -1
        data['show_roi_masks'] = True
        data['show_all_rois'] = False
        print(f"Loaded {dset}")

    @callback(
        Output('plane_selection','options'),
        Output('plane_selection','value'),
        Output('cells_table','data',allow_duplicate = True),
        Output('projection_plot', 'style',allow_duplicate = True),
        Output('traces_heatmap_plot', 'style',allow_duplicate = True),
        Input('sessions_table', 'selected_rows'),
        prevent_initial_call = True)
    def update_selected_session(selected_rows):
        # print(selected_rows)
        data['dset'] = None
        if selected_rows is None:
            return [],None,None,{'display': 'none'},{'display': 'none'}
        if len(selected_rows)==0:
            return [],None,None,{'display': 'none'},{'display': 'none'}
        dset = data['sessions'][selected_rows[0]]
        data['selected_session'] = data['sessions'][selected_rows[0]]
        # needs to be in data
        data['planes'] = np.unique([s for s in (CellSegmentation.Plane() 
                                                & data['selected_session']).fetch('plane_num') if not s is None])
        plane = data['planes'][0]
        dset = dict(dset,plane_num=plane)
        data['dset'] = dset
        return (data['planes'], plane, None,{'display': 'none'},{'display': 'none'})
    
    @callback(
        Output('traces_heatmap_plot','figure',allow_duplicate = True),
        Output('traces_heatmap_plot', 'style'),
        Input('trace_selection','value'),
        prevent_initial_call = True)
    def update_heatmap(selection):
        # print(selected_rows)
        if selection is None:
            return None,{'display': 'none'}
        if selection == 'df/f':
            selection  = 'dff'
        if not data['traces_mode'] == selection:
            print(data['traces_mode'],selection)
            update_data(data['dset'],data,traces_mode = selection)
        print(selection)
        fig = go.Figure()
        if 'cell_indices' in data.keys():
            cell_indices = np.array(data['cell_indices'])
        else:
            cell_indices = np.arange(len(tt))
        tt = np.stack(data['cells_data'][data['traces_mode']].iloc[cell_indices].values)
        from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
        from scipy.spatial.distance import pdist
        
        distance_matrix = pdist(tt[:,:3000], metric='hamming')
        linkage_matrix = linkage(distance_matrix, method='ward')
        clusters = fcluster(linkage_matrix, t=10, criterion='maxclust')
        ii = np.argsort(clusters)
        fig.add_trace(go.Heatmap(z=tt[ii],colorscale = 'inferno', showscale=True,
                                zmin=np.percentile(tt,5), 
                                zmax=np.percentile(tt,99.5),hoverinfo = 'skip',opacity = 1))
        return (fig,{'display': 'block'})

    @callback(
        Output('labeling_selection','options',allow_duplicate = True),
        Output('labeling_selection','value',allow_duplicate = True),
        Output('projection','options',allow_duplicate = True),
        Output('projection','value',allow_duplicate = True),
        Output('projection_plot', 'style',allow_duplicate = True),
        Output('cells_table','data',allow_duplicate = True),
        Input('plane_selection','value'),
        prevent_initial_call = True)
    def update_plane_selection(plane):
        if data['dset'] is None:
            return [],[],[],None,{'display': 'None'},None
        
        data['dset']['plane_num'] = plane
        dset = data['dset']
        print(dset)
        cells = pd.DataFrame((CellSegmentation.Selection() & dset).fetch())
        selection_methods = np.unique(cells.selection_method.values)
        data['cells_table'] = cells[cells.selection_method == selection_methods[0]]
        update_data(dset,data)
        return (selection_methods, selection_methods[0],
                ['none']+data['proj_names'],data['proj_names'][data['proj_idx']],
                {'display': 'block'},
                data['cells_table'][['roi_num','selection','likelihood']].to_dict(orient='records'))

    @callback(Output('projection_plot','figure',allow_duplicate = False),
              Output('trace_selection','value'),
              Input('projection', 'value'),
              Input('roi_masks', 'value'), prevent_initial_call = True)
    def update_projection(value,roi_masks):
        if not roi_masks is None:
            if 'Show ROI masks' in roi_masks:
                data['show_roi_masks'] = True
            else:
                data['show_roi_masks'] = False
            if 'Show all ROIs' in roi_masks:
                data['show_all_masks'] = True
            else:
                data['show_all_masks'] = False
        if value is None:
            print('[update_projection]: skipping')
            return no_update
        if 'proj_names' in data.keys():
            if value == 'none':
                data['proj_idx'] = None
                proj = None
            else:
                data['proj_idx'] = data['proj_names'].index(value)
                proj = data['proj'][data['proj_idx']]

            data['projection_figure'],cell_indices = plot_rois_projection(proj,
                                                                          data['rois_mask'],
                                                                          data['contours'],
                                                                          data['cells_table'],
                                                                          show_masks = data['show_roi_masks'],
                                                                          show_bad = data['show_all_masks'])
            data['cell_indices'] = cell_indices
            
            print(f'Using projection: {value} [{data["proj_idx"]}]')
            return data['projection_figure'],data['traces_mode']
        else:
            print('Skipping projection update.')
            return no_update

    @callback(
        Output('cells_table','selected_rows',allow_duplicate=True),
        Input('projection_plot','selectedData'),
        prevent_initial_call = True)
    def select_cells(selection):
        if not selection:
            return no_update
        idx = [s['pointIndex'] for s in selection['points']]
        return idx

    @callback(
        Output('projection_plot','figure',allow_duplicate=True),
        Output('traces_plot','figure',allow_duplicate=True),
        Output('traces_plot', 'style',allow_duplicate=True),
        Output("cells_table", "style_data_conditional",allow_duplicate = True),
        Input('cells_table','selected_rows'),
        prevent_initial_call = True)
    def select_cells_table(selection):
        print(f'Selected table {selection}')
        if not 'projection_figure' in data.keys():
            print('Could not update because projection_figure is not loaded yet')
            return no_update
        fig = data['projection_figure']
        if not selection:
            print('Empty selection, skipping')
            return fig,None,{'display':'none'},[]
        idx = selection
        try:
            fig.update_layout(selections = None)
            fig.update_traces(selectedpoints=idx, selector = ({'name':'centers'}))
            data['projection_figure'] = fig
        except Exception as err:
            print(err)
            print('Selected units are not on the projection plot, skipping update.')
        if data['cells_data'] is None:
            conn = CellSegmentation.Traces.connection
            with conn.transaction:
                traces = (CellSegmentation.Traces & 
                          data['dset'] & 
                          [dict(roi_num = data['cells_table'].iloc[i].roi_num)
                           for i in idx]).fetch('dff')
        else:
            traces = data['cells_data'].iloc[idx][data['traces_mode']].values
        traces = plot_traces(traces,data['cells_table'].iloc[idx])
        return data['projection_figure'],traces,{'display':'block'},style_selected_rows(idx)

    # @callback(Output("cells_table", "style_data_conditional",allow_duplicate = True),
    #           Input("cells_table", "selected_rows"), prevent_initial_call = True)
    def style_selected_rows(sel_rows):
        if sel_rows in [None,[]]:
            return []
        res = []
        data['selected_cells'] = np.array(sel_rows)
        for i,r in enumerate(sel_rows):
            if i<len(colors)-1:
                color = colors[i]
            else:
                color = 'gray'
            res.append({"if": {"row_index": r}, "backgroundColor": color})
            if color == '#000000':
                res[-1]["color"] = 'white'
        return res  
    
    @app.callback(
        Output('cells_table','selected_rows',allow_duplicate=True),
        Input("keyboard", "n_keydowns"),
        Input("keyboard", "keydown"),
        prevent_initial_call = True)
    def previous_cell(valp,key):
        key =key["key"]
        if key == 'c':
            data['selected_cells'] = []
        if key == 'n':
            if len(data['selected_cells']) == 0:
                data['selected_cells'] = np.array(data['cell_indices'][:3])
            data['selected_cells'] += 1
        if key == 'p':
            if len(data['selected_cells']) == 0:
                data['selected_cells'] = np.array(data['cell_indices'][:3])
            data['selected_cells'] -= 1
        return update_cell_on_key()

    def update_cell_on_key():
        data['selected_cells'] = np.array([np.mod(d,len(data['cells_table'])) for d in data['selected_cells']])
        idx = [d for d in data['selected_cells']]
        return idx
    
    if open_browser:
        import webbrowser
        import threading 
        def _open_browser():
            webbrowser.open_new_tab(f"http://localhost:{port}")
        threading.Timer(2,_open_browser).start()
    app.run(debug = debug,port=port)
