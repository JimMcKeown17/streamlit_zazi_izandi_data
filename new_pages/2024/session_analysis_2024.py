import plotly.express as px
import pandas as pd
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import streamlit as st


st.header("Sessions Analysis")

# Load sessions data and compute average sessions per child
_, _, sessions_df, _, _, _ = load_zazi_izandi_2024()
avg_sessions_per_child = sessions_df['Total Sessions'].mean().round(1)

# Display summary metric at the top
st.header('SUMMARY STATS')
st.metric('Average Sessions per\n Child:', f'{avg_sessions_per_child:.1f}')
st.markdown('---')

# Some quick data cleaning/organizing
def display_session_analysis():
    df = pd.read_excel("data/Zazi iZandi Session Tracker 18102024.xlsx", sheet_name="Sessions")
    months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']

    # Prepare the list of 'Total Sessions' and 'Sessions per Day' columns
    total_sessions_cols = [f'{month}: Total Sessions' for month in months]
    sessions_per_day_cols = [f'{month}: Sessions per Day' for month in months]

    # Melt the DataFrame for 'Total Sessions'
    total_sessions_df = df.melt(
        id_vars=['School', 'EA Name'],
        value_vars=total_sessions_cols,
        var_name='Month',
        value_name='Total Sessions'
    )

    # Clean the 'Month' column to extract month names
    total_sessions_df['Month'] = total_sessions_df['Month'].str.replace(': Total Sessions', '')

    # Melt the DataFrame for 'Sessions per Day'
    sessions_per_day_df = df.melt(
        id_vars=['School', 'EA Name'],
        value_vars=sessions_per_day_cols,
        var_name='Month',
        value_name='Sessions per Day'
    )

    # Clean the 'Month' column to extract month names
    sessions_per_day_df['Month'] = sessions_per_day_df['Month'].str.replace(': Sessions per Day', '')

    # Merge the two DataFrames on 'School', 'EA Name', and 'Month'
    merged_df = pd.merge(
        total_sessions_df,
        sessions_per_day_df,
        on=['School', 'EA Name', 'Month']
    )

    # Set the categorical data type for 'Month' with the correct order
    month_categories = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
    merged_df['Month'] = pd.Categorical(
        merged_df['Month'],
        categories=month_categories,
        ordered=True
    )

    # Streamlit Code
    with st.container():
        st.subheader("Session Metrics per Month")
        # Metric selection
        metric = st.selectbox('Select Metric', ['Sessions per Day', 'Total Sessions'])

        # Use the entire merged_df without filtering
        plot_df = merged_df.copy()

        # Group and aggregate data
        if metric == 'Total Sessions':
            plot_data = plot_df.groupby('Month')[metric].sum().reset_index()
        else:
            plot_data = plot_df.groupby('Month')[metric].mean().reset_index()

        # Create the bar chart
        fig = px.bar(
            plot_data,
            x='Month',
            y=metric,
            title=f'{metric} by Month'
        )

        # Ensure months are in order
        fig.update_xaxes(categoryorder='array', categoryarray=month_categories)

        # Display the chart
        st.plotly_chart(fig)

    st.markdown("---")
    with st.container():
        # Streamlit app
        st.subheader('Average Sessions per Day per School')

        months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
        month_options = ['All Months'] + months

        # Month selection
        selected_month = st.selectbox('Select Month', month_options)

        # Filter data based on the selected month
        if selected_month == 'All Months':
            filtered_df = sessions_per_day_df.copy()
        else:
            filtered_df = sessions_per_day_df[sessions_per_day_df['Month'] == selected_month]

        # Calculate the average 'Sessions per Day' per school
        average_sessions = filtered_df.groupby('School')['Sessions per Day'].mean().reset_index()

        # Sort the schools from highest to lowest average 'Sessions per Day'
        average_sessions = average_sessions.sort_values(by='Sessions per Day', ascending=False)

        # Create the bar chart
        fig = px.bar(
            average_sessions,
            x='School',
            y='Sessions per Day',
            title=f"Average Sessions per Day per School ({selected_month})",
            labels={'Sessions per Day': 'Average Sessions per Day'}
        )

        # Update layout to rotate x-axis labels if needed
        fig.update_layout(xaxis_tickangle=-45)

        # Display the chart
        st.plotly_chart(fig)
    st.markdown("---")
    with st.container():
        with st.container():
            # Streamlit app
            st.subheader('Average Sessions per Day per School')

            months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov']
            month_options = ['All Months'] + months

            # Month selection
            selected_month = st.selectbox('Select Month', month_options, key="ea_month")

            # Filter data based on the selected month
            if selected_month == 'All Months':
                filtered_df = sessions_per_day_df.copy()
            else:
                filtered_df = sessions_per_day_df[sessions_per_day_df['Month'] == selected_month]

            # Calculate the average 'Sessions per Day' per school
            average_sessions = filtered_df.groupby('EA Name')['Sessions per Day'].mean().reset_index()

            # Sort the schools from highest to lowest average 'Sessions per Day'
            average_sessions = average_sessions.sort_values(by='Sessions per Day', ascending=False)

            # Create the bar chart
            fig = px.bar(
                average_sessions,
                x='EA Name',
                y='Sessions per Day',
                title=f"Average Sessions per Day per EA for ({selected_month})",
                labels={'Sessions per Day': 'Average Sessions per Day'}
            )

            # Update layout to rotate x-axis labels if needed
            fig.update_layout(xaxis_tickangle=-45)

            # Display the chart
            st.plotly_chart(fig)
        st.markdown("---")
        with st.container():
            st.subheader('Sessions per Day Over Time by EA')

            # Use the entire DataFrame without filtering
            filtered_df = sessions_per_day_df.copy()

            # Check if the DataFrame is not empty
            if filtered_df.empty:
                st.warning('No data available.')
            else:
                # Create the line chart
                fig = px.line(
                    filtered_df,
                    x='Month',
                    y='Sessions per Day',
                    color='EA Name',
                    markers=True,
                    title='Sessions per Day per EA Over Time'
                )

                # Ensure months are in the correct order on the x-axis
                fig.update_xaxes(categoryorder='array', categoryarray=months)

                # Customize layout
                fig.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Sessions per Day',
                    legend_title='EA Name',
                    hovermode='x unified'
                )

                # Display the chart
                st.plotly_chart(fig)

display_session_analysis()