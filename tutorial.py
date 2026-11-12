import streamlit as st
st.title("Tianic App")

st.write("Hello from titanic-app")

st.radio("select a number",[1,2,3],index = 0)

checked = st.checkbox("check me out")

if checked:
    st.write("you checked me")

with st.form("search"):
    name = st.text_input("Name contains",placeholder="e.g Allen")
    classes = st.multiselect("Class",[1,2,3],default=[1,2,3])
    ages = st.slider("Age",0,80,(0,80))
    submitted = st.form_submit_button("Search")

if submitted:
    st.write(f"You searched {name} in class {classes} and ages {ages}")