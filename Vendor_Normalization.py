import streamlit as st
from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL
import pandas as pd
import re

# Read Snowflake password
# with open("G:\\Logistics\\Admin\\Bart\\Cust_Move\\SnowflakePassPy.txt", "r") as snowpass:
#     PW = snowpass.read()

# # Establish Snowflake connection
# engine = create_engine(
#     URL(
#         account='usfoods',
#         user='BXW6026',
#         password=PW,
#         database='SUPPLY_CHAIN',
#         schema='LOGISTICS',
#         warehouse='USER_ADHOC',
#         role='SUPPLY_CHAIN'
#     )
# )

# Establish Snowflake connection using secrets
engine = create_engine(
    URL(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        role=st.secrets["snowflake"]["role"]
    )
)

# Query data from Snowflake
df = pd.read_sql('''
    SELECT distinct cov_nbr, max(cov_nm) as cov_nm
    FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
    WHERE div_nbr < 5000
    GROUP BY cov_nbr;
''', engine.connect())

# Add new columns to df for Streamlit table interaction
df["Logistics Vendor Name Managed"] = False  # Default unchecked
df["Driver"] = ""  # Default empty
df["Driver Reason"] = None  # Default empty (user must fill this)

# Dropdown options for the driver selection
driver_options = [
    "APVENDOR", #"DIV-PFV-LABEL", "DIV-PFV-PROD", "DIV-PFV-PROD-LABEL",
    "LABEL",
    # "PROD-LABEL", "PROD-LABEL-SFV", "PRODUCT", "TEMP & LABEL"
    "PVENDOR", "SVENDOR",
    "TEMP"
]

# Interactive table using Streamlit's data editor
edited_df = st.data_editor(
    df,
    column_config={
        "Logistics Vendor Name Managed": st.column_config.CheckboxColumn("Managed"),
        "Driver": st.column_config.SelectboxColumn("Driver", options=[""] + driver_options),  # Default empty
        "Driver Reason": st.column_config.TextColumn("Driver Reason") # User must fill this
    },
    height=500
)

# Validation: Ensure that drivers are selected only if "Managed" is checked
error_messages = []
for index, row in edited_df.iterrows():
    if row["Driver"] and not row["Logistics Vendor Name Managed"]:
        error_messages.append(f"⚠️ Row {index}: Please check 'Managed' before selecting a driver.")
    if row["Logistics Vendor Name Managed"] and not row["Driver"]:
        error_messages.append(f"⚠️ Row {index}: Please select a driver for checked rows.")
    # if row["Logistics Vendor Name Managed"] and row["Driver"] and not row["Driver Reason"]:
    #     error_messages.append(f"⚠️ Row {index}: Please provide a reason for the selected driver.")

# Display errors (if any)
if error_messages:
    for msg in error_messages:
        st.error(msg)

# Filter only valid selections (checkbox checked AND driver selected)
selected_df = edited_df[
    (edited_df["Logistics Vendor Name Managed"] == True) &
    (edited_df["Driver"] != "")   # Ensure reason is filled
]

# Show selected records (optional)
st.subheader("✅ Selected & Valid Rows")

selected_df['Normalized temp'] = None		
selected_df['APvendor Number'] = None
selected_df['Purchase Vendor Name'] = None
selected_df['SFV# for NORMALIZATION'] = None	
selected_df['Label'] = None
# selected_df['PIM Class Description (Current)'] = None	
# selected_df['PIM Category Description (Current)'] = None	
# selected_df['PIM Group Description (Current)'] = None	
# selected_df['PIM Brand Owner Name Majority'] = None
selected_df['Normalized Name'] = None

# selected_df['Driver'] = ""
selected_df = selected_df.rename(columns=str.upper)

# --- Data Fetch for Different DataFrames ---

# Fetch additional data for the different scenarios (TEMP, PROD-LABEL-SFV, etc.)
df_temp = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,RATE_TEMP
FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
WHERE div_nbr<5000 GROUP BY cov_nbr,RATE_TEMP;''', engine.connect())

# df_temp_LBL = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,RATE_TEMP,MAJORITY_PROD_LBL
# FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
# WHERE div_nbr<5000 GROUP BY cov_nbr,RATE_TEMP,MAJORITY_PROD_LBL;''', engine.connect())

df_APV_NBR = pd.read_sql('''
SELECT distinct cov_nbr,max(cov_nm) as cov_nm,APV_NBR
FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
WHERE div_nbr<5000 GROUP BY cov_nbr,APV_NBR;''', engine.connect())

# df_MAJORITY_PROD_LBL = pd.read_sql('''
# SELECT distinct cov_nbr,max(cov_nm) as cov_nm,MAJORITY_PROD_LBL,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,MAJORITY_PIM_CLS_DESC
# FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
# WHERE div_nbr<5000 GROUP BY cov_nbr,MAJORITY_PROD_LBL,MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,
# MAJORITY_PIM_CAT_DESC,MAJORITY_PIM_CLS_DESC;''', engine.connect())

# df_MAJORITY_PIM_LBL = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,MAJORITY_PROD_LBL,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
# WHERE div_nbr<5000 GROUP BY cov_nbr,MAJORITY_PROD_LBL,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC ;''', engine.connect())

# df_MAJORITY_PROD_LBL_SFV = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,
# MAJORITY_PROD_LBL,MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC,SFV_NBR FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
# WHERE div_nbr<5000 GROUP BY cov_nbr,MAJORITY_PROD_LBL,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC,SFV_NBR ;''', engine.connect())

df_MAJORITY_SVENDOR = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,
SFV_NBR FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
WHERE div_nbr<5000 GROUP BY cov_nbr,SFV_NBR ;''', engine.connect())

df_MAJORITY_PVENDOR = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,
PFV_NM FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
WHERE div_nbr<5000 GROUP BY cov_nbr,PFV_NM ;''', engine.connect())

# df_MAJORITY_PRODUCT = pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
# WHERE div_nbr<5000 GROUP BY cov_nbr,
# MAJORITY_PIM_BRND_DESC,MAJORITY_PIM_GRP_DESC,MAJORITY_PIM_CAT_DESC,
# MAJORITY_PIM_CLS_DESC;''', engine.connect())

df_LABEL= pd.read_sql('''SELECT distinct cov_nbr,max(cov_nm) as cov_nm,
MAJORITY_PROD_LBL FROM BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES
WHERE div_nbr<5000 GROUP BY cov_nbr,MAJORITY_PROD_LBL''', engine.connect())

# Apply transformation to all fetched DataFrames
def clean_dataframe(df):
    return df.applymap(lambda val: re.sub(r'[\x00-\x1F]', '', val) if isinstance(val, str) else val).rename(columns=str.upper)

# Clean all relevant dataframes
df_MAJORITY_PVENDOR = clean_dataframe(df_MAJORITY_PVENDOR)
df_MAJORITY_SVENDOR = clean_dataframe(df_MAJORITY_SVENDOR)
# df_MAJORITY_PRODUCT = clean_dataframe(df_MAJORITY_PRODUCT)
# df_MAJORITY_PROD_LBL_SFV = clean_dataframe(df_MAJORITY_PROD_LBL_SFV)
# df_MAJORITY_PIM_LBL = clean_dataframe(df_MAJORITY_PIM_LBL)
# df_MAJORITY_PROD_LBL = clean_dataframe(df_MAJORITY_PROD_LBL)
df_APV_NBR = clean_dataframe(df_APV_NBR)
# df_temp_LBL = clean_dataframe(df_temp_LBL)
df_temp = clean_dataframe(df_temp)
df_LABEL = clean_dataframe(df_LABEL)
# Re-expand selected_df with TEMP and PROD-LABEL-SFV logic
final_expanded_rows = []

for _, row in selected_df.iterrows():
    cov_nbr = row["COV_NBR"]

    # TEMP driver
    if row["DRIVER"] == "TEMP":
        matching_rates = df_temp[df_temp["COV_NBR"] == cov_nbr]["RATE_TEMP"].dropna().unique()
        for rate in matching_rates:
            new_row = row.copy()
            new_row["NORMALIZED TEMP"] = rate
            final_expanded_rows.append(new_row)

    # # PROD-LABEL-SFV driver
    # elif row["DRIVER"] == "PROD-LABEL-SFV":
    #     matches = df_MAJORITY_PROD_LBL_SFV[df_MAJORITY_PROD_LBL_SFV["COV_NBR"] == cov_nbr]
    #     distinct_combinations = matches.drop_duplicates(subset=[
    #         "MAJORITY_PIM_BRND_DESC",
    #         "MAJORITY_PIM_GRP_DESC",
    #         "MAJORITY_PIM_CAT_DESC",
    #         "MAJORITY_PIM_CLS_DESC",
    #         "MAJORITY_PROD_LBL",
    #         "SFV_NBR"
    #     ])

    #     for _, match_row in distinct_combinations.iterrows():
    #         new_row = row.copy()
    #         new_row["PIM BRAND OWNER NAME MAJORITY"] = match_row["MAJORITY_PIM_BRND_DESC"]
    #         new_row["PIM GROUP DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_GRP_DESC"]
    #         new_row["PIM CATEGORY DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CAT_DESC"]
    #         new_row["PIM CLASS DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CLS_DESC"]
    #         new_row["LABEL"] = match_row["MAJORITY_PROD_LBL"]
    #         new_row["SFV# FOR NORMALIZATION"] = match_row["SFV_NBR"]
    #         final_expanded_rows.append(new_row)
    # APVENDOR driver
    elif row["DRIVER"] == "APVENDOR":
        matching_apv = df_APV_NBR[df_APV_NBR["COV_NBR"] == cov_nbr]["APV_NBR"].dropna().unique()
        for apv in matching_apv:
            new_row = row.copy()
            new_row["APVENDOR NUMBER"] = apv
            final_expanded_rows.append(new_row)
    # PVENDOR driver
    elif row["DRIVER"] == "PVENDOR":
        matching_pfv = df_MAJORITY_PVENDOR [df_MAJORITY_PVENDOR ["COV_NBR"] == cov_nbr]["PFV_NM"].dropna().unique()
        for pfv in matching_pfv:
            new_row = row.copy()
            new_row["PURCHASE VENDOR NAME"] = pfv
            final_expanded_rows.append(new_row)
    # SVENDOR driver
    elif row["DRIVER"] == "SVENDOR":
        matching_sfv = df_MAJORITY_SVENDOR[df_MAJORITY_SVENDOR["COV_NBR"] == cov_nbr]["SFV_NBR"].dropna().unique()
        for sfv in matching_sfv:
            new_row = row.copy()
            new_row["SFV# FOR NORMALIZATION"] = sfv
            final_expanded_rows.append(new_row)

    elif row["DRIVER"] == "LABEL":
        matching_lbl = df_LABEL[df_LABEL["COV_NBR"] == cov_nbr]["MAJORITY_PROD_LBL"].dropna().unique()
        for lbl in matching_lbl:
            new_row = row.copy()
            new_row["LABEL"] = lbl
            final_expanded_rows.append(new_row)


    # # PROD-LABEL driver
    # elif row["DRIVER"] == "PROD-LABEL":
    #     matches = df_MAJORITY_PROD_LBL[df_MAJORITY_PROD_LBL["COV_NBR"] == cov_nbr]
    #     distinct_combinations = matches.drop_duplicates(subset=[
    #         "MAJORITY_PIM_BRND_DESC",
    #         "MAJORITY_PIM_GRP_DESC",
    #         "MAJORITY_PIM_CAT_DESC",
    #         "MAJORITY_PIM_CLS_DESC",
    #         "MAJORITY_PROD_LBL"
    #     ])

    #     for _, match_row in distinct_combinations.iterrows():
    #         new_row = row.copy()
    #         new_row["PIM BRAND OWNER NAME MAJORITY"] = match_row["MAJORITY_PIM_BRND_DESC"]
    #         new_row["PIM GROUP DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_GRP_DESC"]
    #         new_row["PIM CATEGORY DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CAT_DESC"]
    #         new_row["PIM CLASS DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CLS_DESC"]
    #         new_row["LABEL"] = match_row["MAJORITY_PROD_LBL"]
    #         final_expanded_rows.append(new_row)
    
    # # PRODUCT driver
    # elif row["DRIVER"] == "PRODUCT":
    #     matches = df_MAJORITY_PRODUCT[df_MAJORITY_PRODUCT["COV_NBR"] == cov_nbr]
    #     distinct_combinations = matches.drop_duplicates(subset=[
    #         "MAJORITY_PIM_BRND_DESC",
    #         "MAJORITY_PIM_GRP_DESC",
    #         "MAJORITY_PIM_CAT_DESC",
    #         "MAJORITY_PIM_CLS_DESC"
    #     ])

    #     for _, match_row in distinct_combinations.iterrows():
    #         new_row = row.copy()
    #         new_row["PIM BRAND OWNER NAME MAJORITY"] = match_row["MAJORITY_PIM_BRND_DESC"]
    #         new_row["PIM GROUP DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_GRP_DESC"]
    #         new_row["PIM CATEGORY DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CAT_DESC"]
    #         new_row["PIM CLASS DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PIM_CLS_DESC"]
    #         final_expanded_rows.append(new_row)   

    # # TEMP & LABEL driver
    # elif row["DRIVER"] == "TEMP & LABEL":
    #     matches = df_temp_LBL[df_temp_LBL["COV_NBR"] == cov_nbr]
    #     distinct_combinations = matches.drop_duplicates(subset=[
    #         "RATE_TEMP",
    #         "MAJORITY_PROD_LBL"
    #     ])

    #     for _, match_row in distinct_combinations.iterrows():
    #         new_row = row.copy()
    #         new_row["PIM BRAND OWNER NAME MAJORITY"] = match_row["RATE_TEMP"]
    #         new_row["PIM GROUP DESCRIPTION (CURRENT)"] = match_row["MAJORITY_PROD_LBL"]
    #         final_expanded_rows.append(new_row)              

    # All other drivers — keep as is 
    else:
        final_expanded_rows.append(row)

# Final expanded DataFrame
selected_df = pd.DataFrame(final_expanded_rows)
st.write(selected_df)

# Button for uploading to Snowflake
if st.button("Save & Sync Norm Vndr Data to VP"):
    try:
        # Specify table name
        # mytable = 'Normalized_VP_DATA'

        # # Upload data to Snowflake
        # selected_df.to_sql(mytable, engine, if_exists='replace', index=False, index_label=None, chunksize=12000)
        selected_df.to_excel(r"G:\Logistics\Admin\Reporting\Shama\All File\form_page\LFRM_Logistics_Vendor_Name_New.xlsx"
                             , index= False)
        # update_query = '''UPDATE BUSINESS_ANALYTICS.LOGISTICS.LFRM_VENDOR_PROPERTIES_form a
        # SET a."NORMALIZED_NM" = b."new_Normalized_name"
        # FROM SUPPLY_CHAIN.LOGISTICS."Normalized_VP_DATA" b
        # WHERE a."COV_NM" = b."COV_NM"
        # AND a."COV_NBR" = b."COV_NBR"
        # AND a."DIV_NBR" = b."DIV_NBR"
        # AND a."PFV_NBR" = b."PFV_NBR"
        # AND a."SFV_NBR" = b."SFV_NBR";'''
        # with engine.connect() as connection:
        #     # Execute the update query
        #     connection.execute(text(update_query))
        #     connection.commit()

        # Confirmation message
        st.success("✅ Data successfully uploaded to Snowflake and updated VP!")
    except Exception as e:
        st.error(f"❌ Error: {e}")