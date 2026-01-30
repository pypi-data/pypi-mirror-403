from ...utils import *
from ...schema import *

# this uses dash and plotly
from dash import Dash, html, dash_table,dcc,Input,Output,callback,no_update
import plotly.express as px
import plotly.io as pio
import dash_bootstrap_components as dbc

colors = ['#000000',
          '#1f77b4',
          '#d62728',
          '#ff7f0e',
          '#e377c2',
          '#7f7f7f',
          '#bcbd22']

def plot_raster(dset, data = None, n_spikes_to_plot = 100000,height = None,width = None):
    if type(dset) is dict:
        dset = [dset]
    uu = pd.DataFrame((SpikeSorting.Unit*UnitMetrics & dset).fetch())    
    
    spike_times = np.hstack(uu.spike_times.values) 
    spike_amps = np.hstack(uu.spike_amplitudes.values)
    unit_ids = np.hstack([u.unit_id*np.ones(len(u.spike_amplitudes)) for i,u in uu.iterrows()])
    spike_pos = np.vstack(uu.spike_positions.values)[:,1]

    idx = np.random.choice(
            np.arange(len(spike_times)),
            np.min([n_spikes_to_plot,len(spike_times)]),
            replace=False)
    idx = idx[np.argsort(np.take(spike_amps,idx,axis=0))]


    idx = idx[np.argsort(np.take(spike_amps,idx,axis=0))]
    
    pio.templates.default = "simple_white"
    xx = spike_times[idx].astype(np.float32)/30000
    df = pd.DataFrame(dict(spiketime = xx,
                           position=spike_pos[idx],
                           amplitude = spike_amps[idx],
                           unit_id = unit_ids[idx]))
    scatt = px.scatter(df,x = 'spiketime',
                       y = 'position',
                       color = 'amplitude',
                       opacity = 0.2,color_continuous_scale='spectral_r',
                       hover_data = ['amplitude','position','unit_id'],range_color=[
                           0, np.percentile(df['amplitude'].values,95)])
    scatt.update_layout(
        xaxis_title="time (s)", yaxis_title="depth (um)",
        autosize=False)
    if not width is None:
        scatt.update_layout(width=width,height=height)
    scatt.update_xaxes(range=[np.min(xx), np.max(xx)])
    scatt.update_traces(marker_size=3,marker=dict(showscale=False))
    scatt.update_coloraxes(showscale=False)
    if not data is None:
        data['units'] = uu
    return scatt

def waveforms_plot(dset,data = None, unitoffset = 150,height = 700,width = 600):
    if type(dset) is dict:
        dset = [dset]
    chmap = (SpikeSorting & dset).fetch1('sorting_channel_coords')
    wf = pd.DataFrame((SpikeSorting.Waveforms*UnitMetrics & dset).fetch())
    gain = (EphysRecording.ProbeSetting * ProbeConfiguration & dset).fetch1('probe_gain')
    wf = wf.sort_values(by='depth')

    from plotly import colors
    colors = colors.sample_colorscale("Viridis", len(np.unique([w for w in wf.shank.values if not w is None]))+1)
    ii = np.linspace(-1,1,wf.waveform_median.iloc[0].shape[0])*15
    import plotly.graph_objects as go
    
    xx = [[] for ic in range(len(chmap))]
    yy = [[] for ic in range(len(chmap))]
    cc = [[] for ic in range(len(chmap))]
    wf_info = []
    for j,(i,w) in enumerate(wf.iterrows()):
        if not w.active_electrodes is None and len(w.active_electrodes):
            pchans = w.active_electrodes[0]
            if len(pchans):
                oo = np.mean(chmap[pchans],axis = 0)[0]
            else:
                continue
            for ic in pchans:
                xx[ic].append(ii+unitoffset*j+1.2*(chmap[ic,0]-oo))
                xx[ic].append(np.nan)
                yy[ic].append((w.waveform_median[:,ic]*gain)*0.06+chmap[ic,1])
                yy[ic].append(np.nan)
                cc[ic].append((w.waveform_median[:,ic]*0)+w.shank)
            wf_info.append(dict(unit_id = w.unit_id,
                                shank = w.shank,
                                nspikes = w.num_spikes,
                                plot_x = unitoffset*j+np.mean(chmap[pchans,0])-oo,
                                plot_y = w.depth))
                
    if not data is None:
        data['waveform_info_data'] = wf_info
        data['waveform_data'] = wf
        data['waveform_chmap'] = chmap
        data['waveform_gain'] = gain
        
    xx = [np.hstack(a) for a in xx if len(a)]
    yy = [np.hstack(a) for a in yy if len(a)]
    cc = [np.hstack(a) for a in cc if len(a)]
    wf_info = pd.DataFrame(wf_info)
    
    fig = go.Figure()
    scatter = go.Scatter(x = wf_info['plot_x'].values,
                         text = wf_info['unit_id'].values,
                         y = wf_info['plot_y'].values,mode = 'markers+text',
                         marker=dict(color = wf_info.shank.values,
                                     size = [20 for s in range(len(wf_info))],
                                     # sizemin = 5,
                                     colorscale = 'Spectral',
                                     opacity = 0.4),
                         customdata=wf_info[["unit_id", "shank","nspikes"]], 
                         hovertemplate='<b>Unit ID</b>: %{customdata[0]}<br>' + 
                      '<b>Shank</b>: %{customdata[1]}<br> '+
                      '<b>Num Spikes</b>: %{customdata[2]}<extra></extra>' )
    s = []
    for x,y in zip(xx,yy):
        s.append(go.Scatter(x=x,y = y, mode = 'lines', showlegend=False, line=dict(color='black'),hoverinfo='skip')) 
        fig.add_trace(s[-1])
        
    fig.add_trace(scatter)
    fig.update_xaxes(visible=False)
    fig.data[-1].update(textfont_color= 'darkorange',textposition = 'top center')
    fig.layout.hovermode = 'closest'
    if 'shank' in dset[0].keys():
        ttl = '|'.join(['probe {probe_num} shank {shank}'.format(**d) for d in dset])
    else:
        ttl = '|'.join(['probe {probe_num}'.format(**d) for d in dset])
    fig.update_layout(
        showlegend=False,
        title = f"{dset[0]['subject_name']} {dset[0]['session_name']} {ttl}",
        yaxis_title="depth (um)",
        uirevision = 'donothing',
        autosize=False,  
        width=width,      
        height=height,
        clickmode='event+select'
    )
    return fig

def xcorr(x, y, maxlag):
    """
    Cross correlation with a maximum number of lags.

    `x` and `y` must be one-dimensional numpy arrays with the same length.

    This computes the same result as
        numpy.correlate(x, y, mode='full')[len(a)-maxlag-1:len(a)+maxlag]

    The return vaue has length 2*maxlag + 1.

    Adapted from code from Warren Weckesser (stackoverflow).
    
    Joao Couto - January 2016
    """
    from numpy.lib.stride_tricks import as_strided
    
    def _check_arg(x, xname):
        x = np.asarray(x)
        if x.ndim != 1:
            raise ValueError('%s must be one-dimensional.' % xname)
        return x
    
    x = _check_arg(x, 'x')
    y = _check_arg(y, 'y')
    py = np.pad(y.conj(), 2*maxlag, mode='constant')
    T = as_strided(py[2*maxlag:], shape=(2*maxlag+1, len(y) + 2*maxlag),
                   strides=(-py.strides[0], py.strides[0]))
    px = np.pad(x, maxlag, mode='constant')
    return T.dot(px)

def plot_units_comparison(units,data,width = 700,height=700):
    if len(units)>7:
        units = units[:7]
        print('Too many units selected, will only plot 7.')
    keys = ['unit_id','num_spikes','depth','shank',
            'channel_index','n_electrodes_spanned','firing_rate',
            'isi_contamination','isi_contamination_hill','amplitude_cutoff',
            'presence_ratio','depth_drift_range','depth_drift_fluctuation',
            'spike_amplitude','spike_duration',
            'trough_time','trough_amplitude','fw3m',
            'trough_gradient','peak_gradient']#,'peak_time','peak_amplitude','polarity']
    dd = data['units']
    idx = [np.where(dd.unit_id.values == u)[0][0] for u in units]
    dd = dd.iloc[idx]
    kk = dd[keys]
    kk = kk.to_dict(orient='records')
    #dd = (SpikeSorting.Unit() & data['selected_session'] & [dict(unit_id = u) for u in units]).fetch(as_dict = True)
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    pio.templates.default = "simple_white"
    fig = make_subplots(
        rows=5, cols=3,
        shared_yaxes = True,
        specs=[[dict(colspan = 1,rowspan= 4), dict(colspan = 2,rowspan= 2),None],
               [None, None,None],
              [None, dict(colspan = 2,rowspan= 2),None],
              [None, None,None],
              [dict(colspan = 2,rowspan= 1), None,dict(colspan = 1,rowspan= 1)]],
        print_grid=False,subplot_titles = ['','inter-spike intervals','cross-correlograms','spike amplitudes',''])
    amax = np.max([np.max(d['spike_amplitudes']) for it,d in dd.iterrows()])
    amin = np.min([np.min(d['spike_amplitudes']) for it,d in dd.iterrows()])
    
    spiketimes = []
    for j,(it,d) in enumerate(dd.iterrows()):
        hist, bins = np.histogram(d['spike_amplitudes'],np.arange(1*amin,1*amax,50))
        fig.add_trace(go.Scatter(x=hist,y=bins[:-1],line_color=colors[j],mode = 'lines',name=f'Unit {d.unit_id}'),row=5, col=3)
        sp = (d['spike_times']/30000).astype('float32')
        isis, bins = np.histogram(np.diff(sp),np.arange(0,1,0.0005))
        isis = isis/len(sp)
        spiketimes.append(sp[sp<400]) # sample of the spiketimes
        fig.add_trace(go.Scatter(x=1000*bins[:-1],y=isis,line_color=colors[j],mode = 'lines',name=f'Unit {d.unit_id}'),row=1, col=2)

        fig.add_trace(go.Scatter(x=sp[::4],y = d['spike_amplitudes'][::4], # make it lighter by plotting every 4th point
                                 mode = 'markers',marker_color = colors[j],
                                 marker = dict(opacity = 0.5,size = 2),name=f'Unit {d.unit_id}'),row=5, col=1)
    fig.add_trace(go.Scatter(x=[0,1000],y=[0.002,0.002],line_color='gray',line_width = 0.5,mode = 'lines'),row=1, col=2)
    fig.add_trace(go.Scatter(x=[1,1],y=[0,np.max(isis)],line_color='gray',line_width = 0.5,mode = 'lines'),row=1, col=2)
    fig.update_xaxes(type="log",row = 1,col = 2)

    # CORRELOGRAM
    tmax = np.max([np.max(m) for m in spiketimes])
    tmin = np.min([np.min(m) for m in spiketimes])
    binsize = 0.001
    edges = np.arange(tmin,tmax,binsize)
    def binarize(x,edges):
        return np.histogram(x,edges)[0]
    bspikes = Parallel(n_jobs = 8)(delayed(binarize)(sp,edges) for sp in spiketimes)
    xx = []
    nn = []
    for i,b in enumerate(bspikes):
        for j,a in enumerate(bspikes):
            xx.append([b,a])
            nn.append([i,j])
    res = Parallel(n_jobs = 8)(delayed(xcorr)(x[0],x[1],50) for x in xx)
    corr = {f'{i},{j}':x for (i,j),x in zip(nn,res)}
    norm = np.nanmax([corr[k][corr!=corr[k][50]].max() for k in corr.keys()])
    xoffset = 120
    yoffset = 0.02 #1.2
    win = np.arange(-50,51,1)
    for i,b in enumerate(bspikes):
        for j,a in enumerate(bspikes):
            c = corr[f'{i},{j}'].astype('float32')
            # norm = (len(spiketimes[i])/300)*(len(spiketimes[j])/300)
            if i==j:
                col = colors[i]
                c[50] = np.nan
            else:
                col = "black"
            # norm = np.nanmax(c)
            name = f'Unit {dd.unit_id.iloc[i]}, Unit{dd.unit_id.iloc[j]}'
            fig.add_trace(go.Scatter(x=win+i*xoffset,
                                         y=c/norm + j*yoffset,
                                         line_color=col,
                                         line_width = 2,
                                         mode = 'lines',
                                         name = name),row=3, col=2)
            
            fig.add_trace(go.Scatter(x=np.array([-50,50])+i*xoffset,y = np.array([0,0])+j*yoffset, 
                                     line_color=col, line_width = 0.2,
                                     mode = 'lines'),row=3, col=2)
    fig.update_xaxes(visible = False, row=3,col=2)
    fig.update_yaxes(visible = False, row=3,col=2)
    ## WAVEFORM
    wf = data['waveform_data']
    chmap = data['waveform_chmap']
    gain = data['waveform_gain']

    idx = [np.where(wf.unit_id.values == u)[0][0] for u in units]
    wf = wf.iloc[idx]
    unitoffset = 0
    ii = np.linspace(-1,1,wf.waveform_median.iloc[0].shape[0])*15

    for j,(i,w) in enumerate(wf.iterrows()):
        channels = np.where(np.linalg.norm(chmap-chmap[np.argmax(np.abs(w.waveform_median).max(axis = 0))],axis = 1)<150)[0]
        for ic in channels:
            x = ii+unitoffset*j+1.2*(chmap[ic,0])
            y = (w.waveform_median[:,ic]*gain)*0.07+chmap[ic,1]
            fig.add_trace(go.Scatter(x=x,y=y,line_color=colors[j],mode = "lines",
                                     name=f'Unit {w.unit_id}',
                                     opacity = 0.7),row=1, col=1)
    fig.update_layout(
            showlegend=False,
            width=width,      
            height=height,)
    return fig

tablekeys = ['unit_id','num_spikes','depth','shank',
                'channel_index','n_electrodes_spanned','firing_rate',
                'isi_contamination','isi_contamination_hill','amplitude_cutoff',
                'presence_ratio','spike_amplitude','spike_duration']
def interactive_data_explorer(subject_filter = None,user_name = None, debug = False, port='8051',open_browser = False):
    if subject_filter is None:
        if user_name in [None,'none']:
            subjects = (Subject & SpikeSorting).fetch('subject_name')
        else:
            subjects = (Subject & SpikeSorting & f'user_name = "{user_name}"').fetch('subject_name')
    else:
        subjects = (Subject & (SpikeSorting & f'subject_name LIKE "{subject_filter}"')).fetch('subject_name')
    params = SpikeSortingParams().fetch(as_dict = True)

    data= dict(sessions = None,
            selected_session = None,
            shanks = [],
            units = [],
            selected_units = [],
            waveform_info_data = [],
            waveform_data = [],
            waveform_gain = [],
            waveform_chmap = [],
            dset = None)
    app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        dbc.Row([html.H2("Spike sorting session explorer",style = {'font-weight': 'bold'})]),
        dbc.Row([
            dbc.Col([html.Span("Subject :",style = {'font-weight': 'bold'})], width = 2),
            dbc.Col([dcc.Dropdown(subjects,None,id = 'subject_selection')], width = 3),
            dbc.Col([html.Span("Spike sorting :",style = {'font-weight': 'bold'})], width=2),
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
        dbc.Row([dbc.Col([html.Span("Selected shanks:", style = {'font-weight': 'bold'})],width = 4),
                 dbc.Col([dcc.Dropdown([],None, id = 'shank_selection', multi=True)],width = 4)]),
        dbc.Row([html.Span("Drift raster:", style = {'font-weight': 'bold'})]),
        dbc.Row([dcc.Graph(id='drift_raster', style={'display': 'none'})]),
        dbc.Row([dbc.Col([dcc.Graph(id='waveforms_plot', style={'display': 'none'})],width = 6),
        dbc.Col([dcc.Graph(id='units_plot', style={'display': 'none'})],width = 6),]),
        dbc.Row([html.Span("Units table:", style = {'font-weight': 'bold'})]),
        dbc.Row([dash_table.DataTable(data=None,
                                    style_header={'backgroundColor': 'rgb(230, 230, 230)',
                                                    'fontWeight': 'bold'},
                                    style_table = {'overflowY': 'scroll','width':'2000px','height': '600px','border': '1px solid black'},
                                    style_cell = {'textAlign': 'left'},
                                    style_data = {'whiteSpace': 'normal',
                                                'height': 'auto'},
                                    fixed_rows={'headers': True},
                                    style_cell_conditional = [
                                        {'if': {'column_id': 'col1'},
                                        'width': 'auto',}],
                                    row_selectable = 'multi', id = 'units_table')])])

    @callback(
        Output('sessions_table', 'data'),
        Input('subject_selection', 'value'),
        Input('params_table', 'value'),prevent_initial_call = True)
    def update_sessions(value,param):
        if value is None:
            return
        if param is None or len(param) == 0:
            return no_update
        sessions = (SpikeSorting & 
            f"subject_name = '{value}'" &
            param).proj().fetch(as_dict = True)
        data['sessions'] = sessions
        return sessions
        
    @callback(
        Output('drift_raster','figure',allow_duplicate = True),
        Output('waveforms_plot','figure',allow_duplicate = True),
        Output('drift_raster', 'style'),
        Output('waveforms_plot', 'style'),
        Output('units_plot', 'style',allow_duplicate=True),
        Output('shank_selection','options'),
        Output('shank_selection','value'),
        Input('sessions_table', 'selected_rows'),prevent_initial_call = True)
    def update_raster_plot_and_waveforms(selected_rows):
        dset = data['sessions'][selected_rows[0]]
        data['selected_session'] = data['sessions'][selected_rows[0]]
        # needs to be in data
        data['shanks'] = np.unique([s for s in (UnitMetrics() & data['selected_session']).fetch('shank') if not s is None])
        shank = [data['shanks'][0]]
        dset = [dict(dset,shank=s) for s in data['shanks'][:1]]
        data['dset'] = dset
        # UnitMetrics() & dset
        # data['dset'] = 
        return plot_raster(dset,data=data),waveforms_plot(dset,data = data),{'display': 'block'},{'display': 'block'},{'display': 'none'},data['shanks'],shank
        
    @callback(
        Output('drift_raster','figure',allow_duplicate=True),
        Output('waveforms_plot','figure',allow_duplicate = True),
        Output('units_table','data',allow_duplicate=True),
        Input('shank_selection','value'),prevent_initial_call = True)
    def update_shank_(value):
        if value is None or len(value) == 0:
            return no_update
        dset = data['selected_session']
        if not np.all(np.isin(data['shanks'],value)): # then just plot all units
            dset = [dict(dset,shank=s) for s in value]
        r = plot_raster(dset,data=data)
        
        data['waveforms_figure'] = waveforms_plot(dset,data = data)
        dd = data['units']
        kk = dd[tablekeys]
        kk = kk.to_dict(orient='records')
        return r,data['waveforms_figure'],kk

    @callback(
        Output('units_table','selected_rows',allow_duplicate=True),
        Output('units_plot','figure',allow_duplicate=True),
        Output('units_plot', 'style',allow_duplicate=True),
        Output("units_table", "style_data_conditional",allow_duplicate = True),
        Input('waveforms_plot','selectedData'),
        prevent_initial_call = True)
    def select_units(selection):
        if selection is None:
            return None,None,{'display': 'none'},[]
        if not len(selection['points']):
            return None,None,{'display': 'none'},[]
        units = [data['waveform_info_data'][s['pointIndex']]['unit_id'] for s in selection['points']]
        data['selected_units'] = units
        
        dd = data['units']
        idx = [np.where(dd.unit_id.values == u)[0][0] for u in units]
        tblstyle = style_selected_rows(idx)
        fig = plot_units_comparison(units,data)
        return idx,fig,{'display': 'block'},tblstyle
    
    @callback(
        Output('waveforms_plot','figure',allow_duplicate=True),
        Output('units_plot','figure',allow_duplicate=True),
        Output('units_plot', 'style',allow_duplicate=True),
        Input('units_table','selected_rows'),
        prevent_initial_call = True)
    def selected_table_unit(selected_rows):
        if not 'waveforms_figure' in data.keys():
            print('Could not update because waveforms_figure is not loaded yet')
            return no_update
        fig = data['waveforms_figure']
        dd = data['units']
        waveformunits = [w['unit_id'] for w in data['waveform_info_data']]
        data['selected_units'] = [dd['unit_id'].iloc[s] for s in selected_rows]
        try:
            waveformidx = [waveformunits.index(s) for s in data['selected_units']]
            fig.update_traces(selectedpoints=waveformidx)
        except:
            print('Selected units are not on the waveform plot, skipping update.')
        unitfig = plot_units_comparison(data['selected_units'],data)

        return fig,unitfig,{'display':'block'}

    @app.callback(
            Output("units_table", "style_data_conditional",allow_duplicate = True),
            Input("units_table", "selected_rows"), prevent_initial_call = True)
    def style_selected_rows(sel_rows):
        # print(f'sel_rows {sel_rows}')
        if sel_rows in [None,[]]:
            return []
        res = []
        for i,r in enumerate(sel_rows):
            if i<len(colors)-1:
                color = colors[i]
            else:
                color = 'gray'
            res.append({"if": {"row_index": r}, "backgroundColor": color})
            if color == '#000000':
                res[-1]["color"] = 'white'
        return res
        
    if open_browser:
        import webbrowser
        import threading 
        def _open_browser():
            webbrowser.open_new_tab(f"http://localhost:{port}")
        threading.Timer(2,_open_browser).start()
    app.run(debug = debug,use_reloader=False,port=port)
