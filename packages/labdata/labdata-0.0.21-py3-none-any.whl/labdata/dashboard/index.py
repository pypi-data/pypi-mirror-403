import streamlit as st
import pandas as pd
import numpy as np
from functools import partial

import sys

def parse_procedure(procedure_dict):
    from datetime import datetime
    note_insert = None
    weight_insert = None
    insert = dict(subject_name = procedure_dict['subject_name'],
                    procedure_datetime = datetime.combine(procedure_dict['date'],procedure_dict['time']),
                    procedure_type = procedure_dict['procedure_type'])
    if not procedure_dict['user_name'] is None:
        insert['user_name'] = procedure_dict['user_name']
        if not procedure_dict['note'] is None:
            note_insert = dict(notetaker = insert['user_name'],
                                note_datetime = insert['procedure_datetime'],
                                notes = procedure_dict['note'])
            insert['note_datetime'] = note_insert['note_datetime']
            insert['notetaker'] = note_insert['notetaker']
    if procedure_dict['user_name'] is None and not procedure_dict['note'] is None: 
        raise(ValueError('Need to specify a user_name for adding notes.'))
    if not procedure_dict['weight'] is None:
        weight_insert = dict(weight = procedure_dict['weight'],
                            subject_name = procedure_dict['subject_name'],
                            weighing_datetime = insert['procedure_datetime'])
        insert['weighing_datetime'] = weight_insert['weighing_datetime']
        
    return insert,note_insert,weight_insert

def procedures_tab(schema = None):
    @st.cache_resource
    def get_users_and_subjects():
        return schema.LabMember.fetch('user_name'),schema.Subject.fetch('subject_name')
    
    users,subjects = get_users_and_subjects()
    @st.cache_resource
    def get_procedure_types():
        return schema.ProcedureType.fetch('procedure_type')
    
    @st.cache_resource
    def get_procedures(subject_name):
        return pd.DataFrame((schema.Procedure*schema.Note & dict(subject_name = subject_name)).fetch())
    
    procedure_types = get_procedure_types()
    
    procedure_dict = dict()
    procedure_dict['subject_name'] = st.selectbox('__Subject__', subjects,index = None)

    if not procedure_dict['subject_name'] is None:
        procedures = get_procedures(procedure_dict['subject_name'])
        if len(procedures):
            edited_procedures = st.data_editor(procedures,column_config={
            "Select":st.column_config.CheckboxColumn(required=True)})
        else:
            st.write('There are no procedures for this subject.')
        # st.write(procedure_dict)
        st.write('### Add procedure:')
        with st.form('add procedure'):
            project_users = (schema.Project.User() & f'project_name = "{schema.schema_project}"').fetch('user_name')
            userindex = None
            if len(project_users):
                userindex = [u for u in users].index(project_users[0])
            procedure_dict['user_name'] = st.selectbox('__Experimenter__', users,index = userindex)
            procedure_dict['date'] = st.date_input('__Date__', value = "today")
            procedure_dict['time'] = st.time_input('__Procedure start time__', value = "now")
            procedure_dict['procedure_type'] = st.selectbox('__Procedure type__', procedure_types, index = None)
            procedure_dict['procedure_metadata'] = st.text_input('__Metadata__', value = None)
            procedure_dict['weight'] = st.number_input('__Weight__', value = None)
            procedure_dict['note'] = st.text_area('__Notes__', value = None)
            submitted = st.form_submit_button('Add Procedure', type='primary')
            if submitted:
                for a in ['date','time','procedure_type','user_name']:
                    if not procedure_dict[a]:
                        st.error(f"Specify a {a}")
                # merge the procedure date and time
                proc_dict,note_dict,weigh_dict = parse_procedure(procedure_dict)
                st.write(proc_dict),st.write(note_dict),st.write(weigh_dict)
                
                if not note_dict is None:
                    schema.Note.insert1(note_dict)
                if not weigh_dict is None:
                    schema.Weighing.insert1(weigh_dict)
                schema.Procedure.insert1(proc_dict)
                st.write('Added procedure to database')
    # select a proceedure

def notes_tab(schema = None):
    @st.cache_resource
    def get_users_and_subjects():
        return schema.LabMember.fetch('user_name'),schema.Subject.fetch('subject_name')
    
    users,subjects = get_users_and_subjects()
    #@st.cache_resource
    def get_dataset_notes(subject_name):
        return pd.DataFrame((schema.Dataset*schema.Note & dict(subject_name = subject_name)).fetch())
    sub_dict = dict()
    sub_dict['subject_name'] = st.selectbox('__Subject__', subjects,index = None)
    dataset_notes = []
    if not sub_dict['subject_name'] is None:    
        dataset_notes = get_dataset_notes(sub_dict['subject_name'])
    if len(dataset_notes):
        edited_dataset_notes = st.data_editor(dataset_notes,column_config={
                            "Select":st.column_config.CheckboxColumn(required=True)})
    else:
        st.write('There are no Dataset Notes for this subject.')

def intro_tab(user_name = None, schema = None):
    @st.cache_data
    def get_subjects():
        if not user_name is None:
            df = pd.DataFrame((schema.Subject() & f'user_name = {user_name}').fetch())
        else:        
            df = pd.DataFrame(schema.Subject().fetch())
        df.insert(0, "Select", False)
        return df.set_index("subject_name").sort_index()
        
    @st.cache_data
    def get_sessions(keys):
        if len(keys):
            keys = keys.reset_index()
            dfs = []
            for i in range(len(keys)):
                dfs.append(pd.DataFrame((schema.Session()*schema.Dataset() &
                                            f'subject_name = "{keys["subject_name"].iloc[i]}"').fetch()))
            if len(dfs):
                d = [d for d in dfs if len(d)]
                if not len(d):
                    return None
                df = pd.concat(d)
                return df.set_index("session_datetime").sort_index()
            else:
                return None
        return None
    subjects = get_subjects() 
    st.write("### Subjects", )
    edited_df = st.data_editor(subjects.sort_index(),
                                hide_index=False,
                                disabled = ['subject_name',
                                            'subject_dob',
                                            'subject_sex',
                                            'strain_name',
                                            'user_name'])
                                #column_config={"Select":
                                #               st.column_config.CheckboxColumn(required=True)},)
    sessions = get_sessions(edited_df[edited_df['Select'] == True])
    if sessions is None:
        st.write('No subjects selected.')
    else:
        uniqueds = np.unique([s for s in sessions.dataset_type.values if not s is None])
        tx = f'### Sessions ({len(sessions)})'
        for d in uniqueds:
            if not d is None:
                tx += f' - {d}: {len(sessions[sessions.dataset_type == d])}'
        st.write(tx,sessions)

    st.write('### Add a subject')
    insert_dict = dict()

    st.cache_resource()
    def get_users():
        return schema.LabMember.fetch('user_name')
    
    with st.form('add subject'):
        users = get_users()
        project_users = (schema.Project.User() & f'project_name = "{schema.schema_project}"').fetch('user_name')
        userindex = None
        if len(project_users):
            userindex = [u for u in users].index(project_users[0])
        insert_dict['user_name'] = st.selectbox('__User Name__', users,index = userindex)
        insert_dict['subject_name'] = st.text_input('__Subject ID__',value=None)
        insert_dict['subject_dob'] = st.date_input('__Date of Birth__')
        insert_dict['subject_sex'] = st.selectbox('__Sex__', ['M', 'F', 'Unknown'])
        if insert_dict['subject_sex'] == 'Unknown':
            insert_dict['subject_sex'] = 'U'
        available_strains = [s for s in schema.Strain().fetch('strain_name')]
        insert_dict['strain_name'] = st.selectbox('__Strain__', available_strains)
        submitted = st.form_submit_button('Add Subject', type='primary')
        if submitted:
            st.write('Adding subject to database')
            st.write(insert_dict)
            schema.Subject().insert1(insert_dict)

    selected_subject = edited_df[edited_df['Select'] == True]
    if len(selected_subject):
        selected_subject = selected_subject.reset_index()
        selected_subject = selected_subject['subject_name'].iloc[0]
        edit_dict = dict(subject_name = selected_subject)
        st.write(f'### Edit subject: {selected_subject}')
        with st.form('edit subject'):           
            edit_dict = (schema.Subject & edit_dict).fetch1()
            st.write(edit_dict)
            edit_dict['subject_dob'] = st.date_input('__Date of Birth__', value = edit_dict['subject_dob'])
            edit_dict['subject_sex'] = st.selectbox('__Sex__', ['M', 'F', 'U'], index = ['M', 'F', 'U'].index(edit_dict['subject_sex']))
            edit_dict['strain_name'] = st.selectbox('__Strain__', available_strains, index = available_strains.index(edit_dict['strain_name']))
            submitted = st.form_submit_button('Edit', type='primary')
            if submitted:
                st.write('Adding subject to database')
                st.write(edit_dict)
                schema.Subject().update1(edit_dict)
                st.write(f'Updated {edit_dict["subject_name"]}')
                get_subjects.clear()
                import time
                for i in range(10):
                    time.sleep(0.2)
                    st.write(f'.')
                st.rerun()
st.set_page_config(
    page_title="labdata dashboard",
    page_icon="🧪",
    layout="wide",
      initial_sidebar_state="auto")

from compute import compute_tab
from sorting import sorting_tab
from segmentation import segmentation_tab
from video import video_tab
from decisiontask import decisionmaking_tab
@st.cache_resource
def load_schema(project):
    # load project
    from labdata import load_project_schema
    return load_project_schema(project)

project = None
for k in sys.argv:
    if 'project=' in k:
        project = k.replace('project=','')
schema = load_schema(project)

page_names_to_funcs = {
    "**Subjects**": partial(intro_tab, schema = schema),
    "**Procedures**": partial(procedures_tab, schema = schema),
    "**Notes**": partial(notes_tab, schema = schema),
    "**Spike sorting**": partial(sorting_tab, schema = schema),
    "**Cell Segmentation**": partial(segmentation_tab, schema = schema),
    "**Video**": partial(video_tab, schema = schema),
    "**Decision-making behavior**": partial(decisionmaking_tab, schema = schema),
    "**Compute tasks**": partial(compute_tab, schema = schema),
}

from labdata import plugins
for p in plugins.keys():
    if hasattr(plugins[p],'dashboard_function'):
        page_names_to_funcs[plugins[p].dashboard_name] = partial(plugins[p].dashboard_function, schema = schema)

tab_name = st.sidebar.radio(
    "### labdata dashboard",
    page_names_to_funcs.keys())

page_names_to_funcs[tab_name]()
