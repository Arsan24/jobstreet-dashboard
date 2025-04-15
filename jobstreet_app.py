import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import seaborn as sns
import re
import matplotlib.ticker as ticker

# Set up the Streamlit page
st.set_page_config(layout="wide", page_title="Jobstreet Dashboard")

st.title("📊 Jobstreet Data Dashboard")

# Load data with caching
@st.cache_data
def load_data():
    df = pd.read_csv('jobstreet_all_cleaned.csv')
    df['Date Posted Clean'] = pd.to_datetime(df['Date Posted Clean'], errors='coerce')

    # Handling Salary: split salary into Min and Max
    def parse_salary(salary_str):
        if isinstance(salary_str, str):
            salary_str = salary_str.replace('Rp', '').replace('IDR', '').replace('per month', '').replace('–', '-')
            salary_parts = salary_str.split('-')
            if len(salary_parts) == 2:
                try:
                    salary_min = int(salary_parts[0].replace(',', '').strip())
                    salary_max = int(salary_parts[1].replace(',', '').strip())
                    return salary_min, salary_max
                except ValueError:
                    return 0, 0
            return 0, 0
        return 0, 0

    df[['Salary Min', 'Salary Max']] = df['Salary'].apply(lambda x: pd.Series(parse_salary(x)))
    df['Salary Min'] = pd.to_numeric(df['Salary Min'], errors='coerce')
    df['Salary Max'] = pd.to_numeric(df['Salary Max'], errors='coerce')
    
    return df

df = load_data()

# Sidebar filter
st.sidebar.header("🔍 Filter Data")
selected_category = st.sidebar.multiselect("Select Category:", df['Category'].unique(), default=list(df['Category'].unique()))
min_salary = st.sidebar.slider('Minimum Salary (IDR)', 0, 10000000, 0, 100000)
max_salary = st.sidebar.slider('Maximum Salary (IDR)', 0, 10000000, 10000000, 100000)

# Filter dataframe based on salary range
filtered_df = df[df['Category'].isin(selected_category)]
filtered_df = filtered_df[(filtered_df['Salary Min'] >= min_salary) & (filtered_df['Salary Max'] <= max_salary)]

# Tabs for different analysis
tab1, tab2, tab3, tab4 = st.tabs(["📅 Time Trends", "🏢 Company & Location", "💰 Salary", "☁️ Keywords"])

# Tab 1 - Trend Jobs over Time
with tab1:
    st.subheader("Job Count per Day")
    job_per_day = filtered_df.groupby('Date Posted Clean').size().reset_index(name='Job Count')
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(job_per_day['Date Posted Clean'], job_per_day['Job Count'], marker='o')
    ax.set_title("Job Count per Day")
    ax.set_xlabel("Date")
    ax.set_ylabel("Job Count")
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("Job Count per Day by Category")
    job_per_day_category = filtered_df.groupby(['Date Posted Clean', 'Category']).size().reset_index(name='Job Count')
    fig, ax = plt.subplots(figsize=(12, 5))
    for category in selected_category:
        category_data = job_per_day_category[job_per_day_category['Category'] == category]
        ax.plot(category_data['Date Posted Clean'], category_data['Job Count'], marker='o', label=category)
    ax.set_title("Job Count per Day by Category")
    ax.set_xlabel("Date")
    ax.set_ylabel("Job Count")
    ax.legend(title='Category')
    ax.grid(True)
    st.pyplot(fig)

# Tab 2 - Company & Location
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Companies")
        top_companies = filtered_df['Company'].value_counts().head(10)
        st.bar_chart(top_companies)

    with col2:
        st.subheader("Top Locations")
        top_locations = filtered_df['Location'].value_counts().head(10)
        st.bar_chart(top_locations)

# Tab 3 - Salary
with tab3:
    st.subheader("Minimum Salary Distribution")
    salary = filtered_df[filtered_df['Salary Min'] > 0]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(salary['Salary Min'], bins=20, color='orange', edgecolor='black')
    ax.set_title('Minimum Salary Distribution')
    ax.set_xlabel('Minimum Salary')
    ax.set_ylabel('Job Count')

    # Format x-axis to display as currency
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'Rp {x:,.0f}'))

    st.pyplot(fig)

    st.subheader("Maximum Salary Distribution")
    # Filter out rows where Salary Max is 0 or NaN to ensure valid data
    valid_data = filtered_df[filtered_df['Salary Max'] > 0]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(valid_data['Salary Max'], bins=20, color='blue', edgecolor='black')
    ax.set_title('Maximum Salary Distribution')
    ax.set_xlabel('Maximum Salary')
    ax.set_ylabel('Job Count')

    # Format x-axis to display as currency
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'Rp {x:,.0f}'))

    st.pyplot(fig)


# Tab 4 - Job Description Keywords
with tab4:
    st.subheader("Word Cloud of Job Descriptions")
    common_phrases = ["qualification", "job description", "responsibilities", "join us", "we are looking for", "job details"]

    def clean_description(text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\\s]', ' ', text)
        for phrase in common_phrases:
            text = text.replace(phrase, '')
        return text

    text = ' '.join(filtered_df['Job Description'].dropna().apply(clean_description).tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate(text)
    
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
