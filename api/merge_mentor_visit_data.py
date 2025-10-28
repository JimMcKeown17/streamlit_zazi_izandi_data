import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_survey_dataframes():
    """Load the old and new survey dataframes"""
    try:
        old_df = pd.read_csv('data/mentor_visit_tracker/latest_old.csv')
        new_df = pd.read_csv('data/mentor_visit_tracker/latest_new.csv')
        
        print(f"Loaded old survey: {len(old_df)} records")
        print(f"Loaded new survey: {len(new_df)} records")
        
        return old_df, new_df
    except FileNotFoundError as e:
        print(f"Error loading data files: {e}")
        print("Please run fetch_mentor_visit_data.py first to download the survey data")
        return None, None

def map_old_to_new_columns():
    """
    Create mapping between old and new survey columns
    Returns dict with mappings and lists of columns that were removed/added
    """
    
    # Common columns that exist in both (with same column_name)
    common_columns = [
        'Mentor Name',
        'School Name',
        'EA Name',
        'Grade',
        'Class',
        "Are the EA's children grouped correctly?",
        "If EA grouping are incorrect, please explain why?",
        "Are the EA using their letter tracker correctly?",
        "How engaged did you feel the learners are?",
        "How energertic & prepared was the EA?",
        "Please rate the overall quality of the sessions you observe",
        "How many sessions does the EA say they can do per day?",
        "How is the EA's relationship with their teacher?",
        "Any additional commentary?"
    ]
    
    # Columns that were removed in new survey (only in old)
    removed_columns = [
        "Is the EA using the comment section and session tags on Teampact accordingly?",
        "The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)",
        "Does the EA say that they often have trouble getting children for sessions (please ask them)?"
    ]
    
    # Columns that were added in new survey (only in new)
    added_columns = [
        "If No, have you corrected it?",
        "Session Tag",
        "Is the EA using the comment section accordingly?",
        "Teaching at the right level",
        "Does the EA experience challenges accessing the learners",
        "Reason for having 1 session or none"
    ]
    
    return {
        'common': common_columns,
        'removed': removed_columns,
        'added': added_columns
    }

def merge_survey_data(old_df, new_df):
    """
    Merge old and new survey data into a single unified dataframe
    """
    
    print("\n" + "="*80)
    print("MERGING SURVEY DATA")
    print("="*80)
    
    # Get column mappings
    column_map = map_old_to_new_columns()
    
    # Metadata columns (present in both)
    metadata_columns = [
        'response_id', 'response_uuid', 'survey_id', 'user_id', 'user_name',
        'response_start_at', 'response_end_at', 'duration_minutes', 
        'is_completed', 'created_at', 'updated_at'
    ]
    
    # Add survey source identifier before merging
    old_df['survey_source'] = 'Old Survey (612)'
    new_df['survey_source'] = 'New Survey (677)'
    
    # Combine all columns that should be present in final dataframe
    all_columns = (
        metadata_columns + 
        ['survey_source'] +
        column_map['common'] + 
        column_map['removed'] + 
        column_map['added']
    )
    
    # Ensure both dataframes have all columns (fill missing with NaN)
    for col in all_columns:
        if col not in old_df.columns:
            old_df[col] = np.nan
        if col not in new_df.columns:
            new_df[col] = np.nan
    
    # Select only the columns we want in the final output
    old_df_aligned = old_df[all_columns].copy()
    new_df_aligned = new_df[all_columns].copy()
    
    # Concatenate the dataframes
    merged_df = pd.concat([old_df_aligned, new_df_aligned], ignore_index=True)
    
    # Sort by response date (most recent first)
    merged_df['response_start_at'] = pd.to_datetime(merged_df['response_start_at'])
    merged_df = merged_df.sort_values('response_start_at', ascending=False)
    
    print(f"\n✅ Merge complete!")
    print(f"   Total records: {len(merged_df)}")
    print(f"   Old survey records: {len(old_df)}")
    print(f"   New survey records: {len(new_df)}")
    print(f"   Total columns: {len(merged_df.columns)}")
    
    # Print column breakdown
    print(f"\n📊 Column Breakdown:")
    print(f"   Metadata columns: {len(metadata_columns) + 1}")  # +1 for survey_source
    print(f"   Common question columns: {len(column_map['common'])}")
    print(f"   Old-only columns: {len(column_map['removed'])}")
    print(f"   New-only columns: {len(column_map['added'])}")
    
    # Show which columns have missing data
    print(f"\n⚠️  Columns with missing data:")
    missing_data = merged_df.isnull().sum()
    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
    
    for col, count in missing_data.head(10).items():
        pct = (count / len(merged_df)) * 100
        print(f"   {col}: {count} missing ({pct:.1f}%)")
    
    return merged_df

def create_data_quality_report(merged_df):
    """Create a summary report of the merged data"""
    
    print("\n" + "="*80)
    print("DATA QUALITY REPORT")
    print("="*80)
    
    # Survey distribution
    print("\n📈 Survey Distribution:")
    survey_counts = merged_df['survey_source'].value_counts()
    for survey, count in survey_counts.items():
        pct = (count / len(merged_df)) * 100
        print(f"   {survey}: {count} responses ({pct:.1f}%)")
    
    # Date range
    print("\n📅 Date Range:")
    print(f"   Earliest response: {merged_df['response_start_at'].min()}")
    print(f"   Latest response: {merged_df['response_start_at'].max()}")
    
    # Completion rate
    print("\n✓ Completion Status:")
    completion_rate = merged_df['is_completed'].mean() * 100
    print(f"   Completed responses: {completion_rate:.1f}%")
    
    # Top respondents
    print("\n👥 Top 5 Respondents (Mentors):")
    top_users = merged_df['user_name'].value_counts().head(5)
    for user, count in top_users.items():
        print(f"   {user}: {count} visits")
    
    # Response duration stats
    print("\n⏱️  Response Duration (minutes):")
    print(f"   Mean: {merged_df['duration_minutes'].mean():.2f}")
    print(f"   Median: {merged_df['duration_minutes'].median():.2f}")
    print(f"   Min: {merged_df['duration_minutes'].min():.2f}")
    print(f"   Max: {merged_df['duration_minutes'].max():.2f}")

def save_merged_data(merged_df, output_dir='data/mentor_visit_tracker'):
    """Save the merged dataframe to CSV"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_file = f'{output_dir}/merged_data_{timestamp}.csv'
    merged_df.to_csv(timestamped_file, index=False)
    
    # Save as latest
    latest_file = f'{output_dir}/merged_data_latest.csv'
    merged_df.to_csv(latest_file, index=False)
    
    print(f"\n💾 Saved merged data:")
    print(f"   {timestamped_file}")
    print(f"   {latest_file}")
    
    return latest_file

def main():
    """Main function to execute the merge process"""
    
    print("="*80)
    print("MENTOR VISIT TRACKER - SURVEY DATA MERGE")
    print("="*80)
    
    # Load data
    old_df, new_df = load_survey_dataframes()
    
    if old_df is None or new_df is None:
        print("\n❌ Cannot proceed without data files")
        return
    
    # Merge data
    merged_df = merge_survey_data(old_df, new_df)
    
    # Create quality report
    create_data_quality_report(merged_df)
    
    # Save merged data
    output_file = save_merged_data(merged_df)
    
    print("\n" + "="*80)
    print("✅ MERGE COMPLETE!")
    print("="*80)
    print(f"\nMerged data available at: {output_file}")
    print(f"Total records: {len(merged_df)}")
    print(f"Total columns: {len(merged_df.columns)}")
    
    return merged_df

if __name__ == "__main__":
    merged_df = main()
