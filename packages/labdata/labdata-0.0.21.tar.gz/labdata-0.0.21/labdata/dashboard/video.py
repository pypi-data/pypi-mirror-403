import pandas as pd
import streamlit as st
import numpy as np
    
def video_tab(schema=None):
    import streamlit as st
    col1, col2 = st.columns([1, 5])
    @st.cache_data
    def get_subjects():
        df = np.unique((schema.DatasetVideo()).fetch('subject_name'))
        df = pd.DataFrame(df,columns = ['subject_name'])
        
        df.insert(0, "Select", False)
        return df.set_index("subject_name").sort_index()
    @st.cache_data    
    def get_sessions(keys):
        if len(keys):
            keys = keys.reset_index()
            dfs = []
            for i in range(len(keys)):
                dfs.append(pd.DataFrame((schema.Session*schema.DatasetVideo.proj() &
                                         f'subject_name = "{keys["subject_name"].iloc[i]}"').fetch()))
                df = pd.concat([d for d in dfs if len(d)])
            return df.set_index("session_datetime").sort_index()
        return None
    subjects = get_subjects() 
    col1.write("### Subjects", )
    edited_df = col1.data_editor(subjects.sort_index(),
                               hide_index=False,
                               disabled = ['subject_name'])
                               #column_config={"Select":
                               #               st.column_config.CheckboxColumn(required=True)},)
    sessions = get_sessions(edited_df[edited_df['Select'] == True])
    
    @st.cache_data
    def get_frame_info(schema,sessions,selection):
        frames = None
        if len(selection.selection.rows):
            frames = (schema.DatasetVideo.Frame & [dict(s) for i,s in sessions.iloc[selection.selection.rows].iterrows()]).proj().fetch(as_dict = True)
        return frames
    
    @st.cache_data
    def get_frame(selected):
        try:
            return (schema.DatasetVideo.Frame() & selected).fetch1('frame')
        except:
            st.write('Could not get frame. Use C to clear cache')
        return None
    
    
    if sessions is None:
        col1.write('No subjects selected.')
    else:
        tx = f'### Sessions ({len(sessions)})'
        col2.write(tx)        
        selection = col2.dataframe(sessions,
                    on_select='rerun',
                    selection_mode="multi-row",) 
        frames = get_frame_info(schema,sessions,selection)
        if not frames is None:
            slide = col2.slider(label = 'Frame',min_value = 0, 
                              max_value = len(frames)-1,
                              value = 0)
            im = get_frame(frames[slide])
            if not im is None:
                col1.write(frames[slide])
                col2.image(im)
