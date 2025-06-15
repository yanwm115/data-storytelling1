import streamlit as st
import requests
import json
import pandas as pd
import altair as alt
import numpy as np

with open("burtin.json", "r") as f:
    data = json.load(f)
df = pd.DataFrame(data)

for drug in ["Penicillin", "Streptomycin", "Neomycin"]:
    df[drug] = pd.to_numeric(df[drug], errors='coerce')

df_melted = df.melt(
    id_vars=["Bacteria", "Gram_Staining"],
    value_vars=["Penicillin", "Streptomycin", "Neomycin"],
    var_name="Antibiotic", value_name="MIC")
df_melted["Effectiveness"] = -np.log10(df_melted["MIC"])
df_melted["Label"] = df_melted["Bacteria"]

def bar_chart(data, title_text, show_legend=True, show_y_axis=True, show_x_axis=True, antibiotic=None):
    data = data.sort_values("Effectiveness", ascending=True).copy()
    data["Label_Unique"] = pd.Categorical(
        data["Bacteria"], categories=data["Bacteria"].tolist(), ordered=True
    )
    base = alt.Chart(data).encode(
        x=alt.X(
            "Effectiveness:Q",
            title="Effectiveness (-log₁₀ MIC)",
            scale=alt.Scale(domain=[-3.5, data["Effectiveness"].max() + 0.5]), 
            axis=alt.Axis(titleFontWeight='bold')
        ),
        y=alt.Y(
            "Label_Unique:N",
            sort=None,
            title="Bacteria" if show_y_axis else None,
            axis=alt.Axis(
                labelLimit=400,
                labelFontSize=13,
                titleFontSize=14,
                labels=show_y_axis,
                ticks=show_y_axis,
                titleFontWeight='bold')
        ),
        color=alt.Color(
            "Gram_Staining:N",
            scale=alt.Scale(domain=["positive", "negative"], range=["#2481c3", "#f5974f"]),
            legend=alt.Legend(title="Gram-Stain") if show_legend else None
        ),
        tooltip=["Bacteria", "Antibiotic", "Gram_Staining", "MIC", "Effectiveness"]
    )

    bars = base.mark_bar()

    rule = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(
        color='black',
        strokeDash=[10, 10]
    ).encode(x='x:Q')

    pos_labels = alt.Chart(data[data["Effectiveness"] > 0]).mark_text(
        align='left',
        baseline='middle',
        dx=6
    ).encode(
        x="Effectiveness:Q",
        y=alt.Y("Label_Unique:N", sort=None),
        text=alt.Text("Effectiveness:Q", format=".2f")
    )
    neg_labels = alt.Chart(data[data["Effectiveness"] <= 0]).mark_text(
        align='right',
        baseline='middle',
        dx=-6
    ).encode(
        x="Effectiveness:Q",
        y=alt.Y("Label_Unique:N", sort=None),
        text=alt.Text("Effectiveness:Q", format=".2f")
    )
    chart = bars + pos_labels + neg_labels + rule

    if antibiotic and antibiotic != "All":
        annotation_dict = {
            "Penicillin": "💡 High effectiveness shown for Gram-Positive",
            "Streptomycin": "💡 Effectiveness varies for Gram-Positive/Negative",
            "Neomycin": "💡 Broadly effective for Gram-Positive/Negative"
        }
        if antibiotic in annotation_dict:
            dx_val = 175 if antibiotic == "Penicillin" else 190
            dy_val = 60 if antibiotic == "Neomycin" else 40
            annotation = alt.Chart(pd.DataFrame({
                'x': [data["Effectiveness"].max() - 1],
                'y': [str(data["Label_Unique"].astype(str).tolist()[len(data)//2])],
                'text': [annotation_dict[antibiotic]]
            })).mark_text(
                align='right',
                baseline='middle',
                fontSize=14,
                fontStyle='italic',
                dx=dx_val,
                dy=dy_val,
                color='black',
                tooltip=None
            ).encode(
                x='x:Q',
                y=alt.Y('y:N', sort=None),
                text='text:N'
            )
            chart += annotation
    return chart.properties(
        width=380 if show_y_axis else 350,
        height=max(30 * len(data), 600)
    )


st.set_page_config(layout="wide")
st.title("Effectiveness of Different Antibiotics by Gram Strain ")
st.write("Let's explore Burtin's antibiotic dataset that records the minimum inhibitory concentration (MIC) " \
"of the 3 antibiotics (Penicillin, Streptomycin, Neomycin) against 16 bacterial species. Does the gram staining of " \
"the bacteria affect antibiotic effectiveness? We're going to find out!")

st.subheader("📝 **Additional Information!**")
with st.expander("Antibiotic and Effectiveness"):
    st.markdown("""
### What is an antibiotic?
- An antibiotic is a substance that kills bacteria or inhibits their growth. Antibiotics work by targeting specific
                bacterial processes or structures that are essential for the survival of bacteria, while leaving human 
                cells unharmed. **In simple terms, it is a medicine that fights bacterial infections by killing harmful
                bacteria or stopping them from multiplying. 

### What makes antibiotics effective? 
- They attack specific parts of bacteria that human cells don't have.
- They reach the right concentration level at the infection site.
- The bacteria haven't learned to be resistant to the antibiotic yet!
    """)
with st.expander("Gram Stain Difference"):
    st.markdown("""
### Gram Staining: What's the difference?
- Scientists use a special dye test in order to categorize and divide bacteria into two main groups based on the wall structure: 
Purple bacteria (Gram-positive) and Pink bacteria (Gram-negative)

### Gram-positive:
- Have a thick strong outer wall.
- Turn purple when stained with the special dye.
- Examples: strep throat bacteria, food poisoning bacteria
                
### Gram-negative:
- Have a thinner wall but with extra protective layer.
- Turn pink when stained with the special dye.
- Often harder to kill with antibiotics (because of extra protective layer).
- Examples: E. coli, salmonella
    """)
with st.expander("3 Antibiotics: Penicillin, Streptomycin, Neomycin"):
    st.markdown("""
### Penicillin:
- The first antibiotic ever discovered (by accident on moldy bread!)
- Works by breaking down bacteria's protective wall.
- Best against gram-positive bacteria.

### Streptomycin:
- Stops bacteria from making the proteins they need to survive.
- Works against both gram-negative and gram-positive bacteria.
- Was important for treating tuberculosis (TB)!

### Neomycin: 
- Stops bacteria from making proteins.
- Usually used in creams and ointments for cuts and scrapes.
- Too harsh to take as a pill so it's applied to the skin!  
    """)

st.divider()

st.subheader("Exploration of different antibiotics on various bacteria!")
choice = st.selectbox("Pick an antibiotic:", ["All", "Penicillin", "Streptomycin", "Neomycin"])

if choice == "All":
    pen = df_melted[df_melted["Antibiotic"] == "Penicillin"]
    strep = df_melted[df_melted["Antibiotic"] == "Streptomycin"]
    neo = df_melted[df_melted["Antibiotic"] == "Neomycin"]

    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        st.markdown(
            "<h6 style='text-align: center; font-weight: bold;'>Penicillin Is Highly Effective Against Gram-Positive Bacteria, But Fails Against Gram-Negative</h6>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<h6 style='text-align: center; font-weight: bold;'>Streptomycin Shows Moderate Effectiveness Across Both Gram Types, With Some Variation</h6>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            "<h6 style='text-align: center; font-weight: bold;'>Neomycin Performs Well Across Most Bacteria, Especially Gram-Negative Stains</h6>",
            unsafe_allow_html=True
        )

    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        st.altair_chart(bar_chart(pen, "", show_legend=False, show_y_axis=True, show_x_axis=True, antibiotic=None))
    with col2:
        st.altair_chart(bar_chart(strep, "", show_legend=False, show_y_axis=False, show_x_axis=True, antibiotic=None))
    with col3:
        st.altair_chart(bar_chart(neo, "", show_legend=True, show_y_axis=False, show_x_axis=True, antibiotic=None))
else:
    df_filtered = df_melted[df_melted["Antibiotic"] == choice]
    if choice == "Penicillin":
        chart_title = "Penicillin Is Highly Effective Against Gram-Positive Bacteria, But Fails Against Gram-Negative"
    elif choice == "Streptomycin":
        chart_title = "Streptomycin Shows Moderate Effectiveness Across Both Gram Types, With Some Variation"
    elif choice == "Neomycin":
        chart_title = "Neomycin Performs Well Across Most Bacteria, Especially Gram-Negative Stains"

    st.markdown(
        f"<h6 style='text-align: center; font-weight: bold;'>{chart_title}</h6>",
        unsafe_allow_html=True
    )
    st.altair_chart(
        bar_chart(df_filtered, chart_title, show_legend=True, antibiotic=choice),
        use_container_width=True
    )

st.divider()

st.markdown("#### Key Insights")

if choice == "Penicillin":
    st.markdown("""
- **Penicillin** is **highly effective** against **Gram-positive bacteria**, showing strong inhibition.
- It is **mostly ineffective** against **Gram-negative bacteria**.
- This reflects its known mechanism: it targets peptidoglycan in Gram-positive cell walls.
    """)
elif choice == "Streptomycin":
    st.markdown("""
- **Streptomycin** shows **moderate, broad-spectrum effectiveness**.
- Some Gram-positive and Gram-negative species respond well, but resistance is noticeable.
- It performs better than Penicillin on several Gram-negative stains. """)
elif choice == "Neomycin":
    st.markdown("""
- **Neomycin** has **broad-spectrum potency**, especially against **Gram-negative bacteria**.
- Some Gram-positive species show reduced sensitivity.
- It's among the strongest overall in this dataset. """)
else:
    st.markdown("""
- **Knowing whether bacteria are Gram-positive or Gram-negative is crucial for choosing the right antibiotic.** 
                Doctors perform Gram-staining tests to identify the type of bacteria before prescribing any 
                treatment. This approach increases the chances of successful treatment and reduces the risk of 
                antibiotic resistance.
- **Penicillin shows its great effectiveness against Gram-positive bacteria.** This is 
                because the bacteria have thick cell walls that penicillin can easily target
                and break down. Gram-negative baceria with their protective outer membrane are 
                often able to resist penicillin's effects.
- **Gram-negative bacterial types generally show resistance to many and more antibiotics.** Their 
                double layered cell wall structure acts like an extra armor/protection, making it 
                harder for antibiotics to penetrate and reach their targets. This is why infections 
                caused by Gram-negative bacteria can be more challenging to treat.
- **Both Streptomycin and Neomycin provide broader spectrum coverage compared to penicillin.** These 
                antibiotics can attack both Gram-positive and Gram-negative bacteria by targeting their
                protein functions. This makes them useful when doctors aren't sure what type of bacteria is 
                causing an infection. 
 """)

