WPP Tools

It can be used for making simpler chain forms in streamlit. Chain forms are when you have multiple forms after each other.

To install use the command 'pip install wpp-tools' and import it as 'from WPP import *' to import the functions as needed. Use 'from WPP.main import wpp_forms' to import the variable that contains activation information.

To get started with the package type init(). To add a form type add("Form_name"). When definding the streamlit form use an if statendment like this:

if wpp_foms["form"]:

followed this with you're streamlit code. For example st.form("FORM) and the submit button.
use; if submit: hide()

To reactivate the form use activate("FORM").


This project is in Beta and currently being developed. For contact or bug reporting please contact: blueshadow0324@gmail.com.